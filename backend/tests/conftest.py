"""Test configuration and fixtures."""
import secrets
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    secret_value = make_test_secret()
    return User.objects.create_user(
        email='test@example.com',
        password=secret_value
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def teacher(db):
    secret_value = make_test_secret()
    return User.objects.create_user(
        email='teacher@example.com',
        password=secret_value
    )


@pytest.fixture
def authenticated_teacher(api_client, teacher):
    api_client.force_authenticate(user=teacher)
    return api_client