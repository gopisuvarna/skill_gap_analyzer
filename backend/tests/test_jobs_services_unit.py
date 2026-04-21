"""Unit tests for jobs service internals."""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.jobs.models import Job, JobSkill
from apps.roles.models import Role, RoleSkill
from apps.skills.models import Skill
from apps.jobs import services


class TestJobsServicesInternals(TestCase):
    def test_importance_weight_branches(self):
        self.assertEqual(services._importance_weight(0, 0), 1.0)
        self.assertEqual(services._importance_weight(0, 10), 1.0)
        self.assertEqual(services._importance_weight(4, 10), 0.75)
        self.assertEqual(services._importance_weight(9, 10), 0.5)

    def test_normalize_role_title(self):
        self.assertEqual(services._normalize_role_title("  data   scientist  "), "Data Scientist")

    @patch("apps.jobs.services.normalize_skill", return_value="Python")
    def test_get_or_create_skill(self, _):
        skill = services._get_or_create_skill("PYTHON")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.normalized_name, "python")

    def test_upsert_role_skills_updates_weight_only_when_higher(self):
        role = Role.objects.create(title="Backend Engineer", description="x")
        s1 = Skill.objects.create(name="Python", normalized_name="python")
        s2 = Skill.objects.create(name="Django", normalized_name="django")

        services._upsert_role_skills(role, [s1, s2])
        first = RoleSkill.objects.get(role=role, skill=s1)
        second = RoleSkill.objects.get(role=role, skill=s2)
        self.assertEqual(first.importance_weight, 1.0)
        self.assertEqual(second.importance_weight, 0.75)

        first.importance_weight = 0.2
        first.save(update_fields=["importance_weight"])

        services._upsert_role_skills(role, [s1])
        first.refresh_from_db()
        self.assertEqual(first.importance_weight, 1.0)

    def test_purge_old_jobs_deletes_expired_rows(self):
        old_job = Job.objects.create(
            external_id="old-1",
            title="Old",
            expires_at=timezone.now() - timedelta(days=20),
        )
        Job.objects.create(
            external_id="new-1",
            title="New",
            expires_at=timezone.now() + timedelta(days=1),
        )

        deleted = services.purge_old_jobs(days=10)

        self.assertEqual(deleted, 1)
        self.assertFalse(Job.objects.filter(id=old_job.id).exists())

    def test_get_or_create_role(self):
        self.assertIsNone(services._get_or_create_role(""))

        role = services._get_or_create_role("ml engineer")
        self.assertIsNotNone(role)
        self.assertEqual(role.title, "Ml Engineer")

    def test_build_job_defaults_truncates_fields(self):
        payload = {
            "title": "t" * 600,
            "company": {"display_name": "c" * 300},
            "location": {"display_name": "l" * 300},
            "description": "d" * 12000,
            "redirect_url": "https://example.com/job",
            "salary_min": 10,
            "salary_max": 20,
        }

        data = services._build_job_defaults(payload)

        self.assertEqual(len(data["title"]), 512)
        self.assertEqual(len(data["company"]), 256)
        self.assertEqual(len(data["location"]), 256)
        self.assertEqual(len(data["description"]), 10000)
        self.assertEqual(data["url"], "https://example.com/job")

    @patch("apps.jobs.services.extract_skills", return_value=["python", "django"])
    def test_process_new_job_creates_jobskill_and_role_links(self, _):
        role = Role.objects.create(title="Python Developer", description="x")
        job = Job.objects.create(external_id="j-1", title="Python Dev", description="Uses Django")

        services._process_new_job(job, role)

        self.assertEqual(JobSkill.objects.filter(job=job).count(), 2)
        self.assertEqual(RoleSkill.objects.filter(role=role).count(), 2)

    @patch("apps.jobs.services.fetch_jobs", return_value=[])
    def test_sync_page_stops_on_empty_results(self, _):
        created, stop = services._sync_page(1, "in", "python", None, set())
        self.assertEqual(created, 0)
        self.assertTrue(stop)

    @patch("apps.jobs.services.fetch_jobs")
    def test_sync_page_creates_once_and_skips_seen(self, fetch_mock):
        fetch_mock.return_value = [
            {"id": "1", "title": "Python Dev", "company": {"display_name": "A"}},
            {"id": "1", "title": "Python Dev", "company": {"display_name": "A"}},
        ]

        with patch("apps.jobs.services.extract_skills", return_value=[]):
            created, stop = services._sync_page(1, "in", "python", None, set())

        self.assertEqual(created, 1)
        self.assertFalse(stop)
        self.assertEqual(Job.objects.count(), 1)

    @patch("apps.jobs.services._sync_page", side_effect=[(2, False), (0, True)])
    @patch("apps.jobs.services._get_or_create_role")
    def test_sync_jobs_stops_early_when_sync_page_requests_stop(self, get_role_mock, _):
        get_role_mock.return_value = None
        total = services.sync_jobs(country="in", max_pages=5, what="")
        self.assertEqual(total, 2)
