"""Unit tests for authentication backend and JWT cookie auth."""
from unittest.mock import patch

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework import exceptions

from apps.accounts.authentication import JWTCookieAuthentication, enforce_csrf
from apps.accounts.backends import EmailBackend

User = get_user_model()


class TestEmailBackend(TestCase):
    def setUp(self):
        self.backend = EmailBackend()
        self.password = "strong-pass-123"
        self.user = User.objects.create_user(
            email="backend@example.com",
            password=self.password,
        )

    def test_authenticate_returns_none_when_missing_credentials(self):
        self.assertIsNone(self.backend.authenticate(None, username=None, password=self.password))
        self.assertIsNone(self.backend.authenticate(None, username=self.user.email, password=None))

    def test_authenticate_returns_user_for_valid_email_password(self):
        result = self.backend.authenticate(None, username=self.user.email, password=self.password)
        self.assertEqual(result, self.user)

    def test_authenticate_returns_none_for_wrong_or_unknown_credentials(self):
        self.assertIsNone(self.backend.authenticate(None, username=self.user.email, password="wrong-pass"))
        self.assertIsNone(self.backend.authenticate(None, username="unknown@example.com", password=self.password))


class TestEnforceCsrf(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_enforce_csrf_raises_when_csrf_fails(self):
        request = self.factory.post("/api/auth/login/")

        with patch("apps.accounts.authentication.authentication.CSRFCheck") as csrf_check:
            check_instance = csrf_check.return_value
            check_instance.process_view.return_value = "CSRF token missing"

            with self.assertRaises(exceptions.PermissionDenied) as ctx:
                enforce_csrf(request)

            self.assertIn("CSRF Failed", str(ctx.exception))

    def test_enforce_csrf_passes_when_no_failure_reason(self):
        request = self.factory.post("/api/auth/login/")

        with patch("apps.accounts.authentication.authentication.CSRFCheck") as csrf_check:
            check_instance = csrf_check.return_value
            check_instance.process_view.return_value = None

            enforce_csrf(request)


class TestJwtCookieAuthentication(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.auth = JWTCookieAuthentication()
        self.password = "strong-pass-123"
        self.user = User.objects.create_user(
            email="jwt@example.com",
            password=self.password,
        )

    def _access_token(self, user_id):
        return jwt.encode(
            {"type": "access", "user_id": str(user_id)},
            settings.SECRET_KEY,
            algorithm=settings.JWT_CONFIG["ALGORITHM"],
        )

    def test_authenticate_returns_none_when_no_cookie_or_header(self):
        request = self.factory.get("/api/auth/me/")
        self.assertIsNone(self.auth.authenticate(request))

    def test_authenticate_uses_authorization_header_when_cookie_missing(self):
        token = self._access_token(self.user.id)
        request = self.factory.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}")

        authenticated_user, used_token = self.auth.authenticate(request)
        self.assertEqual(authenticated_user, self.user)
        self.assertEqual(used_token, token)

    def test_authenticate_enforces_csrf_for_cookie_based_unsafe_method(self):
        token = self._access_token(self.user.id)
        request = self.factory.post("/api/auth/me/")
        request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = token

        with patch("apps.accounts.authentication.enforce_csrf") as csrf_check:
            authenticated_user, _ = self.auth.authenticate(request)

        self.assertEqual(authenticated_user, self.user)
        csrf_check.assert_called_once_with(request)

    def test_authenticate_rejects_non_access_token(self):
        request = self.factory.get("/api/auth/me/")
        request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = "cookie-token"

        with patch("apps.accounts.authentication.jwt.decode", return_value={"type": "refresh", "user_id": str(self.user.id)}):
            with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                self.auth.authenticate(request)

        self.assertIn("Invalid token type", str(ctx.exception))

    def test_authenticate_rejects_missing_user_id(self):
        request = self.factory.get("/api/auth/me/")
        request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = "cookie-token"

        with patch("apps.accounts.authentication.jwt.decode", return_value={"type": "access"}):
            with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                self.auth.authenticate(request)

        self.assertIn("Invalid token payload", str(ctx.exception))

    def test_authenticate_raises_not_authenticated_for_expired_token(self):
        request = self.factory.get("/api/auth/me/")
        request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = "expired-token"

        with patch("apps.accounts.authentication.jwt.decode", side_effect=jwt.ExpiredSignatureError):
            with self.assertRaises(exceptions.NotAuthenticated) as ctx:
                self.auth.authenticate(request)

        self.assertIn("Access token expired", str(ctx.exception))

    def test_authenticate_raises_authentication_failed_for_invalid_token(self):
        request = self.factory.get("/api/auth/me/")
        request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = "invalid-token"

        with patch("apps.accounts.authentication.jwt.decode", side_effect=jwt.InvalidTokenError):
            with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                self.auth.authenticate(request)

        self.assertIn("Invalid token", str(ctx.exception))

    def test_authenticate_raises_authentication_failed_when_user_not_found(self):
        request = self.factory.get("/api/auth/me/")
        request.COOKIES[settings.COOKIE_CONFIG["ACCESS_COOKIE_NAME"]] = "missing-user-token"

        with patch(
            "apps.accounts.authentication.jwt.decode",
            return_value={"type": "access", "user_id": "00000000-0000-0000-0000-000000000000"},
        ):
            with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                self.auth.authenticate(request)

        self.assertIn("User not found", str(ctx.exception))
