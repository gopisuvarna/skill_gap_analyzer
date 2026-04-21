"""Base test case for all tests."""
import secrets
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class BaseTestCase(TestCase):
    """Base test case with common setup for authenticated tests."""
    
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    @property
    def authenticated_client(self):
        return self.client
    
    @property
    def current_user(self):
        return self.user


class UnauthenticatedTestCase(TestCase):
    """Base test case for unauthenticated tests."""
    
    def setUp(self):
        self.client = APIClient()
    
    @property
    def api_client(self):
        return self.client


class APITestMixin:
    """Mixin for common API testing utilities."""
    
    def assert_response_200(self, response):
        self.assertEqual(response.status_code, 200)
    
    def assert_response_201(self, response):
        self.assertEqual(response.status_code, 201)
    
    def assert_response_400(self, response):
        self.assertEqual(response.status_code, 400)
    
    def assert_response_401(self, response):
        self.assertEqual(response.status_code, 401)
    
    def assert_response_403(self, response):
        self.assertEqual(response.status_code, 403)
    
    def assert_response_404(self, response):
        self.assertEqual(response.status_code, 404)
    
    def assert_response_204(self, response):
        self.assertEqual(response.status_code, 204)