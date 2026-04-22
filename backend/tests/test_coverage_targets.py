from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import jwt
import pandas as pd
import pytest
from django.conf import settings
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import force_authenticate

from apps.accounts import views as account_views
from apps.accounts.authentication import JWTCookieAuthentication
from apps.embeddings.management.commands.build_faiss_index import Command as BuildFaissIndexCommand
from apps.recommendations.serializers import CourseSerializer
from apps.roles.management.commands.build_role_faiss_csv import Command as BuildRoleCsvCommand
from apps.roles.management.commands.seed_roles import Command as SeedRolesCommand, _importance
from apps.roles.services.role_embedding_pipeline import (
    COL_CERTS,
    COL_DESCRIPTION,
    COL_SKILLS,
    COL_TITLE,
    RoleEmbeddingPipeline,
    RolePipelineException,
)
from apps.skills import views as skill_views
from apps.skills.data.master_skills import MASTER_SKILLS
from apps.accounts.management.commands.test import Command as AccountsTestCommand
from apps.jobs import scheduler as job_scheduler


@pytest.mark.django_db
def test_accounts_view_helpers_set_and_clear_cookies(user):
    response = account_views.Response({"ok": True}, status=status.HTTP_200_OK)
    access, refresh = account_views._create_tokens(user)

    response = account_views._set_cookies(response, access, refresh)
    assert settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"] in response.cookies
    assert settings.COOKIE_CONFIG["REFRESH_COOKIE_NAME"] in response.cookies

    cleared = account_views._clear_cookies(response)
    assert cleared.cookies[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]]["max-age"] == 0
    assert cleared.cookies[settings.COOKIE_CONFIG["REFRESH_COOKIE_NAME"]]["max-age"] == 0


@pytest.mark.django_db
def test_login_starts_scheduler_and_handles_scheduler_errors(user, monkeypatch):
    user.set_password("secret-pass")
    user.save(update_fields=["password"])

    factory = RequestFactory()
    request = factory.post("/api/auth/login/", {"email": user.email, "password": "secret-pass"})

    fake_scheduler = types.SimpleNamespace(start_scheduler=MagicMock())
    monkeypatch.setattr(settings, "TESTING", False, raising=False)

    with patch.object(account_views.LoginSerializer, "is_valid", return_value=True), patch.object(
        account_views.LoginSerializer,
        "validated_data",
        {"email": user.email, "password": "secret-pass"},
        create=True,
    ), patch("apps.accounts.views.authenticate", return_value=user), patch.dict(
        sys.modules, {"apps.jobs.scheduler": fake_scheduler}
    ):
        response = account_views.login(request)

    assert response.status_code == 200
    fake_scheduler.start_scheduler.assert_called_once()

    bad_scheduler = types.SimpleNamespace(start_scheduler=MagicMock(side_effect=RuntimeError("boom")))
    with patch.object(account_views.LoginSerializer, "is_valid", return_value=True), patch.object(
        account_views.LoginSerializer,
        "validated_data",
        {"email": user.email, "password": "secret-pass"},
        create=True,
    ), patch("apps.accounts.views.authenticate", return_value=user), patch.dict(
        sys.modules, {"apps.jobs.scheduler": bad_scheduler}
    ):
        response = account_views.login(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_logout_without_cookies_skips_csrf(user, monkeypatch):
    request = RequestFactory().post("/api/auth/logout/")
    force_authenticate(request, user=user)

    enforce = MagicMock()
    monkeypatch.setattr(account_views, "enforce_csrf", enforce)

    response = account_views.logout(request)
    assert response.status_code == 200
    enforce.assert_not_called()


@pytest.mark.django_db
def test_jwt_cookie_auth_allows_safe_cookie_requests_without_csrf(user):
    auth = JWTCookieAuthentication()
    request = RequestFactory().get("/api/auth/me/")
    request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = jwt.encode(
        {"type": "access", "user_id": str(user.id)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_CONFIG["ALGORITHM"],
    )

    with patch("apps.accounts.authentication.enforce_csrf") as enforce:
        authenticated, _ = auth.authenticate(request)

    assert authenticated == user
    enforce.assert_not_called()


@pytest.mark.django_db
def test_get_or_create_skill_handles_new_and_existing_skill(monkeypatch):
    monkeypatch.setattr(skill_views, "normalize_skill", lambda value: value.strip().title())
    monkeypatch.setattr(skill_views, "encode_single", lambda *args, **kwargs: [0.1, 0.2])

    create = MagicMock()
    monkeypatch.setattr(skill_views.SkillEmbedding.objects, "create", create)

    first = skill_views.get_or_create_skill("python")
    second = skill_views.get_or_create_skill("python")

    assert first == second
    create.assert_called_once()


@pytest.mark.django_db
def test_create_user_skill_response_and_list_user_skills(user, monkeypatch):
    response = skill_views.create_user_skill_response(types.SimpleNamespace(data={}, user=user))
    assert response.status_code == 400

    monkeypatch.setattr(skill_views, "normalize_skill", lambda value: value.strip().title())
    monkeypatch.setattr(skill_views, "encode_single", lambda *args, **kwargs: [0.1, 0.2])
    monkeypatch.setattr(skill_views.SkillEmbedding.objects, "create", lambda **kwargs: None)

    created = skill_views.create_user_skill_response(
        types.SimpleNamespace(data={"name": "python"}, user=user)
    )
    assert created.status_code == 201

    list_request = RequestFactory().get("/api/skills/")
    force_authenticate(list_request, user=user)
    listed = skill_views.list_user_skills(list_request)
    assert listed.status_code == 200
    assert listed.data[0]["skill_name"] == "Python"


@pytest.mark.django_db
def test_extract_from_document_uses_fallback_documents(user, monkeypatch):
    from apps.documents.models import Document

    first_doc = Document.objects.create(user=user, parsed=False, extracted_text="Python and SQL")

    monkeypatch.setattr(skill_views, "extract_skills", lambda text, use_llm=False: ["Python", "SQL"] if use_llm else ["Python"])
    monkeypatch.setattr(skill_views, "normalize_skill", lambda value: value.strip().title())
    monkeypatch.setattr(skill_views, "encode_single", lambda *args, **kwargs: [0.1, 0.2])
    monkeypatch.setattr(skill_views.SkillEmbedding.objects, "create", lambda **kwargs: None)

    request = RequestFactory().post("/api/skills/extract/", {"use_llm": True})
    force_authenticate(request, user=user)

    response = skill_views.extract_from_document(request)
    assert response.status_code == 200
    assert response.data["extracted"] == ["Python", "SQL"]
    assert first_doc.extracted_text == "Python and SQL"


def test_build_faiss_index_command_handles_empty_and_success(monkeypatch):
    command = BuildFaissIndexCommand()
    out = []
    command.stdout.write = out.append
    command.style.SUCCESS = lambda msg: msg

    empty_roles = MagicMock()
    empty_roles.all.return_value = []
    empty_manager = MagicMock()
    empty_manager.prefetch_related.return_value = empty_roles
    monkeypatch.setattr("apps.embeddings.management.commands.build_faiss_index.Role.objects", empty_manager)

    command.handle()
    assert any("No roles found" in line for line in out)

    role = MagicMock()
    role.id = "1"
    role.title = "Backend Engineer"
    role.skills.all.return_value = [types.SimpleNamespace(skill=types.SimpleNamespace(name="Python"))]
    success_roles = MagicMock()
    success_roles.all.return_value = [role]
    success_manager = MagicMock()
    success_manager.prefetch_related.return_value = success_roles

    build = MagicMock()
    faiss_index = MagicMock(build=build)
    monkeypatch.setattr("apps.embeddings.management.commands.build_faiss_index.Role.objects", success_manager)
    monkeypatch.setattr("apps.embeddings.management.commands.build_faiss_index.encode", lambda texts: [[0.1, 0.2]])
    monkeypatch.setattr("apps.embeddings.management.commands.build_faiss_index.RoleEmbedding.objects.update_or_create", MagicMock())
    monkeypatch.setattr("apps.embeddings.management.commands.build_faiss_index.FAISSRoleIndex", lambda: faiss_index)

    command.handle()
    build.assert_called_once()


def test_build_role_csv_command_handles_success_and_error(monkeypatch):
    command = BuildRoleCsvCommand()
    messages = []
    command.stdout.write = messages.append
    command.style.SUCCESS = lambda msg: f"success:{msg}"
    command.style.ERROR = lambda msg: f"error:{msg}"

    pipeline = MagicMock(run=MagicMock())
    monkeypatch.setattr("apps.roles.management.commands.build_role_faiss_csv.RoleEmbeddingPipeline", lambda: pipeline)
    command.handle()
    assert any("success:" in msg for msg in messages)

    messages.clear()
    monkeypatch.setattr(
        "apps.roles.management.commands.build_role_faiss_csv.RoleEmbeddingPipeline",
        lambda: types.SimpleNamespace(run=MagicMock(side_effect=RuntimeError("failed"))),
    )
    command.handle()
    assert any("error:failed" == msg for msg in messages)


@pytest.mark.django_db
def test_seed_roles_helpers_and_command(monkeypatch):
    assert _importance(0, 0) == 1.0
    assert _importance(0, 3) == 1.0
    assert _importance(1, 3) == 0.75
    assert _importance(2, 3) == 0.5

    command = SeedRolesCommand()
    messages = []
    command.stdout.write = messages.append
    command.style.ERROR = lambda msg: f"error:{msg}"
    command.style.SUCCESS = lambda msg: f"success:{msg}"

    monkeypatch.setattr("apps.roles.management.commands.seed_roles.CSV_PATH", Path("missing.csv"))
    command.handle(clear=False)
    assert any(msg.startswith("error:CSV not found") for msg in messages)

    messages.clear()
    monkeypatch.setattr("apps.roles.management.commands.seed_roles.CSV_PATH", Path("roles.csv"))
    monkeypatch.setattr(Path, "exists", lambda self: True)
    monkeypatch.setattr(
        "apps.roles.management.commands.seed_roles.pd.read_csv",
        lambda *args, **kwargs: pd.DataFrame(
            [
                {"Job Title": "Backend Engineer", "Job Description": "APIs", "Skills": "Python, SQL"},
                {"Job Title": "", "Job Description": "skip", "Skills": "Skip"},
            ]
        ),
    )

    role = MagicMock()
    role_manager = MagicMock()
    role_manager.get_or_create.side_effect = [(role, True)]
    role_manager.count.return_value = 1
    role_manager.all.return_value.delete = MagicMock()
    monkeypatch.setattr("apps.roles.management.commands.seed_roles.Role.objects", role_manager)
    monkeypatch.setattr("apps.roles.management.commands.seed_roles._get_or_create_skill", lambda name: name)
    monkeypatch.setattr(
        "apps.roles.management.commands.seed_roles.RoleSkill.objects.get_or_create",
        MagicMock(side_effect=[(None, True), (None, True)]),
    )

    command.handle(clear=True)
    assert any("Loading 2 roles from CSV" in msg for msg in messages)
    role_manager.all.return_value.delete.assert_called_once()


def test_scheduler_functions(monkeypatch):
    monkeypatch.setattr(job_scheduler, "_scheduler", None)

    with patch("apps.roles.models.Role.objects.prefetch_related") as prefetch:
        prefetch.return_value.all.return_value = []
        assert job_scheduler.rebuild_faiss_index() == 0

    role = MagicMock()
    role.id = "1"
    role.title = "Backend Engineer"
    role.skills.all.return_value = [types.SimpleNamespace(skill=types.SimpleNamespace(name="Python"))]
    with (
        patch("apps.roles.models.Role.objects.prefetch_related") as prefetch,
        patch("core.services.embedding_service.encode", return_value=[[0.1, 0.2]]) as encode,
        patch("apps.embeddings.models.RoleEmbedding.objects.update_or_create"),
        patch("apps.roles.services.FAISSRoleIndex") as index_cls,
    ):
        prefetch.return_value.all.return_value = [role]
        index = index_cls.return_value
        assert job_scheduler.rebuild_faiss_index() == 1
        encode.assert_called_once()
        index.build.assert_called_once()

    sync_jobs = MagicMock(side_effect=[1] * len(job_scheduler._ROLE_KEYWORDS))
    purge_old_jobs = MagicMock(return_value=2)
    monkeypatch.setitem(sys.modules, "apps.jobs.services", types.SimpleNamespace(sync_jobs=sync_jobs, purge_old_jobs=purge_old_jobs))
    monkeypatch.setattr(job_scheduler, "rebuild_faiss_index", lambda: 3)
    job_scheduler.run_job_sync(startup=True)
    assert sync_jobs.call_args.kwargs["max_pages"] == 1

    scheduler = MagicMock()
    scheduler_cls = MagicMock(return_value=scheduler)
    monkeypatch.setattr(job_scheduler, "BackgroundScheduler", scheduler_cls)
    job_scheduler.start_scheduler()
    assert scheduler.add_job.call_count == 2
    job_scheduler.start_scheduler()
    scheduler.start.assert_called_once()
    job_scheduler.stop_scheduler()
    scheduler.shutdown.assert_called_once()


def test_role_embedding_pipeline_methods(monkeypatch):
    with pytest.raises(RolePipelineException):
        monkeypatch.setattr("apps.roles.services.role_embedding_pipeline.DOCUMENTS_DATA_CSV", Path("missing.csv"))
        RoleEmbeddingPipeline()

    dataset = Path("roles.csv")
    monkeypatch.setattr("apps.roles.services.role_embedding_pipeline.DOCUMENTS_DATA_CSV", dataset)
    monkeypatch.setattr(Path, "exists", lambda self: True)
    pipeline = RoleEmbeddingPipeline()

    df = pd.DataFrame(
        [
            {
                COL_TITLE: "Backend Engineer",
                COL_DESCRIPTION: "Build APIs",
                COL_SKILLS: "Python, SQL",
                COL_CERTS: "AWS",
            }
        ]
    )
    assert "Backend Engineer" in pipeline._build_role_text(df)[0]
    assert pipeline._build_metadata(df)[0]["certifications"] == "AWS"

    monkeypatch.setattr(
        "apps.roles.services.role_embedding_pipeline.pd.read_csv",
        lambda *args, **kwargs: df,
    )
    monkeypatch.setattr("apps.roles.services.role_embedding_pipeline.encode", lambda *args, **kwargs: [[0.1, 0.2]])
    manager = MagicMock()
    monkeypatch.setattr("apps.roles.services.role_embedding_pipeline.RoleFAISSManager", lambda: manager)
    pipeline.run()
    manager.create_index.assert_called_once()

    monkeypatch.setattr(
        "apps.roles.services.role_embedding_pipeline.pd.read_csv",
        lambda *args, **kwargs: pd.DataFrame([{COL_TITLE: "Only title"}]),
    )
    with pytest.raises(RolePipelineException):
        pipeline.run()


@pytest.mark.django_db
def test_load_courses_module_serializer_master_skills_and_test_command():
    module_name = "apps.recommendations.load_courses"
    fake_df = pd.DataFrame(
        [
            {
                "Title": "Python Basics",
                "URL": "https://example.com/python",
                "Site": "Example",
                "Skills": "Python, SQL",
                "Category": "Programming",
                "Sub-Category": "Backend",
            },
            {
                "Title": None,
                "URL": "https://example.com/skip",
                "Site": "Example",
                "Skills": "",
                "Category": "",
                "Sub-Category": "",
            },
        ]
    )

    with patch("pandas.read_csv", return_value=fake_df), patch(
        "apps.recommendations.models.Course.objects.bulk_create"
    ) as bulk_create:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)

    bulk_create.assert_called_once()

    serializer = CourseSerializer(
        instance=types.SimpleNamespace(
            id="1",
            title="Course",
            provider="Provider",
            url="https://example.com",
            skills_taught=["python"],
        )
    )
    assert serializer.data["title"] == "Course"
    assert "Python" in MASTER_SKILLS
    assert AccountsTestCommand.__name__ == "Command"
