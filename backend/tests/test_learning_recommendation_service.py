"""Unit tests for course recommendation service."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.recommendations.models import Course
from core.services.learning_recommendation_service import (
    TARGET,
    _match_static,
    get_courses_for_skills,
)


class TestLearningRecommendationService(TestCase):
    def test_match_static_returns_matched_courses(self):
        results = _match_static(["python", "sql"])
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), TARGET)
        for item in results:
            self.assertIn("matched_skills", item)
            self.assertTrue(item["matched_skills"])

    def test_get_courses_for_skills_returns_empty_for_empty_input(self):
        self.assertEqual(get_courses_for_skills([]), [])

    def test_get_courses_for_skills_falls_back_to_static_when_db_empty(self):
        results = get_courses_for_skills(["kubernetes"])
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), TARGET)

    def test_get_courses_for_skills_prefers_ranked_db_results(self):
        python_sql = Course.objects.create(
            title="Python and SQL",
            provider="P1",
            url="https://example.com/1",
            skills_taught=["python", "sql"],
        )
        sql_only = Course.objects.create(
            title="SQL only",
            provider="P2",
            url="https://example.com/2",
            skills_taught=["sql"],
        )

        results = get_courses_for_skills(["python", "sql"])

        self.assertGreaterEqual(len(results), 2)
        self.assertEqual(results[0]["id"], str(python_sql.id))
        self.assertEqual(results[1]["id"], str(sql_only.id))

    def test_get_courses_for_skills_uses_loose_substring_fallback(self):
        course = Course.objects.create(
            title="Python 3 in depth",
            provider="P3",
            url="https://example.com/3",
            skills_taught=["python3"],
        )

        results = get_courses_for_skills(["python"])

        ids = [r["id"] for r in results if r["id"] is not None]
        self.assertIn(str(course.id), ids)

    def test_match_static_skips_duplicate_titles(self):
        dup_courses = [
            {
                "title": "Duplicate Course",
                "provider": "P",
                "url": "https://example.com/a",
                "skills_taught": ["python"],
            },
            {
                "title": "Duplicate Course",
                "provider": "P",
                "url": "https://example.com/b",
                "skills_taught": ["python"],
            },
        ]

        with patch("core.services.learning_recommendation_service._STATIC_COURSES", dup_courses):
            results = _match_static(["python"])

        self.assertEqual(len(results), 1)

    def test_get_courses_for_skills_returns_static_when_db_pool_has_no_real_matches(self):
        fake_course = SimpleNamespace(
            id="fake-id",
            title="Unrelated",
            provider="PX",
            url="https://example.com/x",
            skills_taught=[],
        )
        fake_qs = [fake_course]

        with patch("core.services.learning_recommendation_service.Course.objects.filter") as filter_mock, patch(
            "core.services.learning_recommendation_service._match_static",
            return_value=[{"id": None, "title": "Static", "matched_skills": ["python"]}],
        ) as static_mock:
            filter_mock.return_value.distinct.return_value.__getitem__.return_value = fake_qs
            results = get_courses_for_skills(["python"])

        self.assertEqual(results[0]["title"], "Static")
        static_mock.assert_called_once()
