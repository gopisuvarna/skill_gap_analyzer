"""Unit tests for custom middleware."""
import json
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.middleware import CSRFCookieMiddleware, RateLimitMiddleware


class TestRateLimitMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda request: HttpResponse("ok"))

    def test_process_request_ignores_non_auth_paths(self):
        request = self.factory.get("/api/jobs/")
        response = self.middleware.process_request(request)
        self.assertIsNone(response)

    def test_process_request_allows_request_under_limit(self):
        request = self.factory.post("/api/auth/login/", REMOTE_ADDR="10.0.0.1")

        with patch.object(self.middleware, "_load", return_value={"10.0.0.1": [1.0, 2.0]}), patch.object(
            self.middleware,
            "_save",
        ) as save_mock, patch("core.middleware.time.time", return_value=3.0):
            response = self.middleware.process_request(request)

        self.assertIsNone(response)
        save_mock.assert_called_once()

    def test_process_request_blocks_when_limit_exceeded(self):
        request = self.factory.post("/api/auth/register/", REMOTE_ADDR="10.0.0.1")
        recent_timestamps = [10.0] * self.middleware.RATE_LIMIT

        with patch.object(self.middleware, "_load", return_value={"10.0.0.1": recent_timestamps}), patch(
            "core.middleware.time.time",
            return_value=20.0,
        ):
            response = self.middleware.process_request(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(json.loads(response.content), {"detail": "Rate limit exceeded"})

    def test_get_client_ip_prefers_x_forwarded_for(self):
        request = self.factory.get("/api/auth/login/", HTTP_X_FORWARDED_FOR="203.0.113.4, 198.51.100.1")
        self.assertEqual(self.middleware._get_client_ip(request), "203.0.113.4")

    def test_load_returns_empty_dict_when_file_missing(self):
        self.middleware._store_path = "not-a-real-path.json"
        self.assertEqual(self.middleware._load(), {})

    def test_load_returns_empty_dict_when_json_invalid(self):
        with patch("builtins.open", side_effect=json.JSONDecodeError("bad", "doc", 0)):
            self.assertEqual(self.middleware._load(), {})

    def test_save_swallows_os_error(self):
        with patch("builtins.open", side_effect=OSError):
            self.middleware._save({"127.0.0.1": [1.0]})


class TestCsrfCookieMiddleware(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CSRFCookieMiddleware(lambda request: HttpResponse("ok"))

    def test_process_response_sets_csrf_for_api_without_cookie(self):
        request = self.factory.get("/api/roles/")
        response = HttpResponse("ok")

        with patch("django.middleware.csrf.get_token", return_value="token") as get_token:
            returned = self.middleware.process_response(request, response)

        self.assertEqual(returned, response)
        get_token.assert_called_once_with(request)

    def test_process_response_skips_non_api_paths(self):
        request = self.factory.get("/health/")
        response = HttpResponse("ok")

        with patch("django.middleware.csrf.get_token") as get_token:
            returned = self.middleware.process_response(request, response)

        self.assertEqual(returned, response)
        get_token.assert_not_called()

    def test_process_response_skips_when_csrf_cookie_exists(self):
        request = self.factory.get("/api/roles/")
        response = HttpResponse("ok")
        response.set_cookie("csrftoken", "already-present")

        with patch("django.middleware.csrf.get_token") as get_token:
            returned = self.middleware.process_response(request, response)

        self.assertEqual(returned, response)
        get_token.assert_not_called()
