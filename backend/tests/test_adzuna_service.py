"""Unit tests for Adzuna integration service."""
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
import requests

from core.services.adzuna_service import fetch_jobs


class TestAdzunaService(SimpleTestCase):
    @override_settings(ADZUNA_CONFIG={"APP_ID": "", "API_KEY": "", "BASE_URL": "https://example.com"})
    def test_fetch_jobs_returns_empty_when_credentials_missing(self):
        with patch("core.services.adzuna_service._session.get") as get_mock:
            self.assertEqual(fetch_jobs(), [])
        get_mock.assert_not_called()

    @override_settings(ADZUNA_CONFIG={"APP_ID": "id", "API_KEY": "key", "BASE_URL": "https://example.com"})
    def test_fetch_jobs_success_returns_results_and_lowercases_what(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"results": [{"id": "1"}]}

        with patch("core.services.adzuna_service.time.sleep") as sleep_mock, patch(
            "core.services.adzuna_service._session.get", return_value=response
        ) as get_mock:
            result = fetch_jobs(country="in", page=2, what="PyThOn")

        self.assertEqual(result, [{"id": "1"}])
        get_mock.assert_called_once()
        call_kwargs = get_mock.call_args.kwargs
        self.assertEqual(call_kwargs["params"]["what"], "python")
        sleep_mock.assert_called_once()

    @override_settings(ADZUNA_CONFIG={"APP_ID": "id", "API_KEY": "key", "BASE_URL": "https://example.com"})
    def test_fetch_jobs_retries_once_on_429_then_succeeds(self):
        first = Mock(status_code=429)
        second = Mock(status_code=200)
        second.json.return_value = {"results": [{"id": "2"}]}

        with patch("core.services.adzuna_service.time.sleep") as sleep_mock, patch(
            "core.services.adzuna_service._session.get", side_effect=[first, second]
        ):
            result = fetch_jobs(what="data")

        self.assertEqual(result, [{"id": "2"}])
        self.assertEqual(sleep_mock.call_count, 2)

    @override_settings(ADZUNA_CONFIG={"APP_ID": "id", "API_KEY": "key", "BASE_URL": "https://example.com"})
    def test_fetch_jobs_returns_empty_when_429_twice(self):
        first = Mock(status_code=429)
        second = Mock(status_code=429)

        with patch("core.services.adzuna_service.time.sleep"), patch(
            "core.services.adzuna_service._session.get", side_effect=[first, second]
        ):
            result = fetch_jobs()

        self.assertEqual(result, [])

    @override_settings(ADZUNA_CONFIG={"APP_ID": "id", "API_KEY": "key", "BASE_URL": "https://example.com"})
    def test_fetch_jobs_returns_empty_on_http_error(self):
        response = Mock(status_code=500)
        response.raise_for_status.side_effect = requests.HTTPError("bad request")

        with patch("core.services.adzuna_service.time.sleep"), patch(
            "core.services.adzuna_service._session.get", return_value=response
        ):
            result = fetch_jobs()

        self.assertEqual(result, [])

    @override_settings(ADZUNA_CONFIG={"APP_ID": "id", "API_KEY": "key", "BASE_URL": "https://example.com"})
    def test_fetch_jobs_returns_empty_on_unexpected_exception(self):
        with patch("core.services.adzuna_service.time.sleep"), patch(
            "core.services.adzuna_service._session.get", side_effect=Exception("boom")
        ):
            result = fetch_jobs()

        self.assertEqual(result, [])
