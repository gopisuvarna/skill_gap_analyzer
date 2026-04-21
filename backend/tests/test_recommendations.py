"""Tests for recommendations API endpoints."""
import secrets
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.skills.models import Skill, UserSkill
from apps.roles.models import Role, RoleSkill
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestTopRoles(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_top_roles_no_skills(self):
        response = self.client.get('/api/recommendations/roles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['roles'], [])
        self.assertEqual(response.data['message'], 'Add skills first')
    
    @patch('apps.recommendations.views.encode_single')
    @patch('apps.recommendations.views.get_faiss_index')
    def test_top_roles_with_skills(self, mock_faiss, mock_encode):
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill, source='manual')

        mock_encode.return_value = [0.1] * 384
        mock_index = MagicMock()
        mock_index.search.return_value = []
        mock_faiss.return_value = mock_index

        response = self.client.get('/api/recommendations/roles/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('roles', response.data)
    
    def test_top_roles_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/recommendations/roles/')
        self.assertEqual(response.status_code, 403)


class TestSkillGap(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_skill_gap_role_not_found(self):
        import uuid
        response = self.client.get(f'/api/recommendations/skill-gap/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)
    
    def test_skill_gap_success(self):
        role = Role.objects.create(title='Backend Developer')
        skill = Skill.objects.create(name='Python', normalized_name='python')
        RoleSkill.objects.create(role=role, skill=skill, importance_weight=0.8)

        response = self.client.get(f'/api/recommendations/skill-gap/{role.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('missing_skills', response.data)
    
    def test_skill_gap_unauthenticated(self):
        import uuid
        client = APIClient()
        response = client.get(f'/api/recommendations/skill-gap/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 403)


class TestLearningPlan(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_learning_plan_role_not_found(self):
        import uuid
        response = self.client.get(f'/api/recommendations/learning-plan/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 404)
    
    def test_learning_plan_success(self):
        role = Role.objects.create(title='Backend Developer')
        skill = Skill.objects.create(name='Python', normalized_name='python')
        RoleSkill.objects.create(role=role, skill=skill, importance_weight=0.8)

        response = self.client.get(f'/api/recommendations/learning-plan/{role.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('missing_skills', response.data)
    
    def test_learning_plan_unauthenticated(self):
        import uuid
        client = APIClient()
        response = client.get(f'/api/recommendations/learning-plan/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, 403)