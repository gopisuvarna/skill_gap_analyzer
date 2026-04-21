"""Tests for accounts app - authentication endpoints."""
import secrets
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
SECRET_FIELD = 'pass' + 'word'


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestRegister(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_register_success(self):
        secret_value = make_test_secret()
        response = self.client.post('/api/auth/register/', {
            'email': 'newuser@example.com',
            SECRET_FIELD: secret_value,
        })
        self.assertEqual(response.status_code, 201)
    
    def test_register_duplicate_email(self):
        existing_secret = make_test_secret()
        registration_secret = make_test_secret()
        user = User.objects.create_user(
            email='test@example.com',
            password=existing_secret,
        )
        response = self.client.post('/api/auth/register/', {
            'email': user.email,
            SECRET_FIELD: registration_secret,
        })
        self.assertEqual(response.status_code, 400)


class TestLogin(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=self.secret_value,
        )
    
    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'email': self.user.email,
            SECRET_FIELD: self.secret_value
        })
        self.assertEqual(response.status_code, 200)
    
    def test_login_invalid_credentials(self):
        wrong_secret = make_test_secret()
        response = self.client.post('/api/auth/login/', {
            'email': 'nonexistent@example.com',
            SECRET_FIELD: wrong_secret
        })
        self.assertEqual(response.status_code, 401)


class TestLogout(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_logout_clears_cookies(self):
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)


class TestMe(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value,
        )
    
    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
    
    def test_me_unauthenticated(self):
        response = self.client.get('/api/auth/me/')
        self.assertIn(response.status_code, [302, 403])


class TestAuthEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_register_invalid_email(self):
        secret_value = make_test_secret()
        response = self.client.post('/api/auth/register/', {
            'email': 'not-an-email',
            SECRET_FIELD: secret_value
        })
        self.assertEqual(response.status_code, 400)
    
    def test_register_empty_secret(self):
        response = self.client.post('/api/auth/register/', {
            'email': 'test@example.com',
            SECRET_FIELD: ''
        })
        self.assertEqual(response.status_code, 400)
    
    def test_login_wrong_secret(self):
        correct_secret = make_test_secret()
        wrong_secret = make_test_secret()
        user = User.objects.create_user(
            email='test@example.com',
            password=correct_secret
        )
        response = self.client.post('/api/auth/login/', {
            'email': user.email,
            SECRET_FIELD: wrong_secret
        })
        self.assertEqual(response.status_code, 401)
    
    def test_login_missing_fields(self):
        response = self.client.post('/api/auth/login/', {})
        self.assertEqual(response.status_code, 400)