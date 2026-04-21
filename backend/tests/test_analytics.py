"""Tests for analytics API endpoints."""
import secrets
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.skills.models import Skill, UserSkill
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestDashboard(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
    
    def test_dashboard_unauthenticated(self):
        response = self.client.get('/api/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['authenticated'])
        self.assertEqual(response.data['skill_distribution'], [])
    
    @patch('apps.analytics.views.encode_single')
    @patch('apps.analytics.views.get_faiss_index')
    def test_dashboard_authenticated_no_skills(self, mock_faiss, mock_encode):
        self.client.force_authenticate(user=self.user)
        mock_encode.return_value = [0.1] * 384
        mock_index = MagicMock()
        mock_index.search.return_value = []
        mock_faiss.return_value = mock_index

        response = self.client.get('/api/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['authenticated'])
        self.assertEqual(response.data['match_score'], 0.0)
        self.assertEqual(response.data['top_roles'], [])
    
    @patch('apps.analytics.views.encode_single')
    @patch('apps.analytics.views.get_faiss_index')
    def test_dashboard_with_skills_and_matches(self, mock_faiss, mock_encode):
        self.client.force_authenticate(user=self.user)
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill, source='manual')

        mock_encode.return_value = [0.1] * 384
        mock_index = MagicMock()
        mock_index.search.return_value = []
        mock_faiss.return_value = mock_index

        response = self.client.get('/api/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['skill_distribution']), 1)


class TestAnalyticsEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
    
    @patch('apps.analytics.views.encode_single')
    @patch('apps.analytics.views.get_faiss_index')
    def test_dashboard_handles_faiss_error(self, mock_faiss, mock_encode):
        self.client.force_authenticate(user=self.user)
        mock_encode.return_value = [0.1] * 384
        mock_faiss.side_effect = Exception('FAISS not available')
        
        response = self.client.get('/api/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['match_score'], 0.0)
    
    @patch('apps.analytics.views.encode_single')
    @patch('apps.analytics.views.get_faiss_index')
    def test_dashboard_empty_faiss_results(self, mock_faiss, mock_encode):
        self.client.force_authenticate(user=self.user)
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill)
        
        mock_encode.return_value = [0.1] * 384
        mock_index = MagicMock()
        mock_index.search.return_value = []
        mock_faiss.return_value = mock_index
        
        response = self.client.get('/api/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['top_roles'], [])