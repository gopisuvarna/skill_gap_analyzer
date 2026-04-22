from unittest.mock import MagicMock, patch

import jwt
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.accounts.views import _create_tokens
from apps.jobs.models import Job, JobSkill
from apps.roles.models import Role, RoleSkill
from apps.skills.models import Skill, UserSkill
from apps.analytics import views as analytics_views
from apps.chatbot import views as chatbot_views


@pytest.fixture
def skill_factory(db):
    def make(name):
        return Skill.objects.create(name=name, normalized_name=name.lower())

    return make


@pytest.mark.django_db
def test_dashboard_builds_ranked_roles_gaps_learning_plan_and_jobs(user, skill_factory):
    client = APIClient()
    client.force_authenticate(user=user)
    python = skill_factory("Python")
    sql = skill_factory("SQL")
    UserSkill.objects.create(user=user, skill=python, source="manual")

    role = Role.objects.create(title="Backend Developer", description="Build APIs")
    RoleSkill.objects.create(role=role, skill=python, importance_weight=0.9)
    RoleSkill.objects.create(role=role, skill=sql, importance_weight=0.7)

    job = Job.objects.create(
        external_id="job-analytics",
        title="Python Developer",
        company="Example",
        location="Remote",
        url="https://example.com/jobs/python",
    )
    JobSkill.objects.create(job=job, skill=python)

    mock_index = MagicMock()
    mock_index.search.return_value = [(str(role.id), 0.99)]

    with (
        patch("apps.analytics.views.encode_single", return_value=[0.1, 0.2]),
        patch("apps.analytics.views.get_faiss_index", return_value=mock_index),
        patch("apps.analytics.views.get_courses_for_skills", return_value=[{"title": "Learn SQL"}]) as courses,
    ):
        response = client.get("/api/analytics/dashboard/")

    assert response.status_code == 200
    assert response.data["authenticated"] is True
    assert response.data["top_roles"][0]["title"] == "Backend Developer"
    assert response.data["skill_gaps"]["missing_skills"] == ["SQL"]
    assert response.data["learning_plan"] == [{"title": "Learn SQL"}]
    assert response.data["job_matches"][0]["title"] == "Python Developer"
    courses.assert_called_once_with(["SQL"])


@pytest.mark.django_db
def test_build_skill_gaps_fetches_role_skills_when_map_is_empty(skill_factory):
    python = skill_factory("Python")
    role = Role.objects.create(title="Python Engineer", description="")
    RoleSkill.objects.create(role=role, skill=python, importance_weight=0.5)

    gaps = analytics_views._build_skill_gaps(
        [{"id": str(role.id), "title": role.title, "match_score": 0.0}],
        {},
        set(),
    )

    assert gaps["per_role"][0]["missing_skills"] == ["Python"]
    assert gaps["learning_priority"][0]["skill_name"] == "Python"


@pytest.mark.django_db
def test_refresh_endpoint_handles_token_branches(user):
    client = APIClient()

    missing = client.post("/api/auth/refresh/")
    assert missing.status_code == 401
    assert missing.data["detail"] == "Refresh token required"

    access, refresh = _create_tokens(user)
    client.cookies[settings.COOKIE_CONFIG["REFRESH_COOKIE_NAME"]] = access
    wrong_type = client.post("/api/auth/refresh/")
    assert wrong_type.status_code == 401
    assert wrong_type.data["detail"] == "Invalid token type"

    payload = jwt.decode(
        refresh,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_CONFIG["ALGORITHM"]],
    )
    payload["user_id"] = "00000000-0000-0000-0000-000000000000"
    bad_user_refresh = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_CONFIG["ALGORITHM"],
    )
    client.cookies[settings.COOKIE_CONFIG["REFRESH_COOKIE_NAME"]] = bad_user_refresh
    bad_user = client.post("/api/auth/refresh/")
    assert bad_user.status_code == 401
    assert bad_user.data["detail"] == "Invalid refresh token"

    client.cookies[settings.COOKIE_CONFIG["REFRESH_COOKIE_NAME"]] = refresh
    ok = client.post("/api/auth/refresh/")
    assert ok.status_code == 200
    assert ok.data["email"] == user.email
    assert settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"] in ok.cookies


@pytest.mark.django_db
def test_chatbot_context_uses_faiss_roles_and_db_fallback(user, skill_factory):
    python = skill_factory("Python")
    sql = skill_factory("SQL")
    UserSkill.objects.create(user=user, skill=python)

    role = Role.objects.create(title="API Engineer", description="")
    RoleSkill.objects.create(role=role, skill=python, importance_weight=0.9)
    RoleSkill.objects.create(role=role, skill=sql, importance_weight=0.8)

    mock_index = MagicMock()
    mock_index.search.return_value = [(str(role.id), 1.0)]

    with (
        patch("core.services.embedding_service.encode_single", return_value=[0.1]),
        patch("apps.roles.services.get_faiss_index", return_value=mock_index),
        patch("apps.roles.services.re_rank", return_value=[{"id": str(role.id)}]),
    ):
        context = chatbot_views._build_context(user)

    assert "User skills: Python" in context
    assert "Role: API Engineer" in context
    assert "Missing skills: SQL" in context

    with patch("core.services.embedding_service.encode_single", side_effect=Exception("boom")):
        fallback = chatbot_views._build_context(user)

    assert "Role: API Engineer" in fallback


@pytest.mark.django_db
def test_top_roles_uses_faiss_candidates_and_attaches_required_skills(user, skill_factory):
    client = APIClient()
    client.force_authenticate(user=user)
    python = skill_factory("Python")
    sql = skill_factory("SQL")
    UserSkill.objects.create(user=user, skill=python)

    role = Role.objects.create(title="Backend Engineer", description="Build APIs")
    RoleSkill.objects.create(role=role, skill=python, importance_weight=0.9)
    RoleSkill.objects.create(role=role, skill=sql, importance_weight=0.8)

    mock_index = MagicMock()
    mock_index.search.return_value = [(str(role.id), 0.99)]

    with (
        patch("apps.recommendations.views.encode_single", return_value=[0.1, 0.2]),
        patch("apps.recommendations.views.get_faiss_index", return_value=mock_index),
        patch(
            "apps.recommendations.views.re_rank",
            return_value=[{"id": str(role.id), "title": role.title, "description": role.description}],
        ),
    ):
        response = client.get("/api/recommendations/roles/")

    assert response.status_code == 200
    returned = response.data["roles"][0]
    assert returned["title"] == "Backend Engineer"
    assert set(returned["required_skills"]) == {"Python", "SQL"}
    assert returned["match_score"] == 0.5
