"""Tests for skills API endpoints."""
import secrets
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.skills.models import Skill, UserSkill
from apps.documents.models import Document
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestUserSkills(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_user_skills_empty(self):
        response = self.client.get('/api/skills/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
    
    def test_get_user_skills_with_data(self):
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill, source='manual')
        
        response = self.client.get('/api/skills/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['skill_name'], 'Python')
    
    @patch('apps.skills.views.encode_single')
    @patch('apps.skills.views.SkillEmbedding.objects')
    def test_add_user_skill(self, mock_emb, mock_encode):
        mock_encode.return_value = [0.1] * 384
        mock_emb.filter.return_value.create.return_value = None
        
        response = self.client.post('/api/skills/manual/', {'name': 'JavaScript'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['skill_name'], 'JavaScript')
    
    def test_add_duplicate_skill(self):
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill)
        
        response = self.client.post('/api/skills/manual/', {'name': 'Python'})
        self.assertEqual(response.status_code, 201)
    
    def test_add_skill_missing_name(self):
        response = self.client.post('/api/skills/manual/', {})
        self.assertEqual(response.status_code, 400)


class TestRemoveUserSkill(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_remove_skill_success(self):
        skill = Skill.objects.create(name='Python', normalized_name='python')
        user_skill = UserSkill.objects.create(user=self.user, skill=skill)
        
        response = self.client.delete(f'/api/skills/{user_skill.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(UserSkill.objects.filter(id=user_skill.id).exists())
    
    def test_remove_skill_not_found(self):
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.delete(f'/api/skills/{fake_id}/')
        self.assertEqual(response.status_code, 404)


class TestExtractFromDocument(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.skills.views.extract_skills')
    def test_extract_from_document_no_doc(self, mock_extract):
        response = self.client.post('/api/skills/extract/', {'use_llm': False})
        self.assertEqual(response.status_code, 400)
    
    @patch('apps.skills.views.extract_skills')
    @patch('apps.skills.views.encode_single')
    @patch('apps.skills.views.SkillEmbedding.objects')
    def test_extract_from_document_success(self, mock_emb, mock_encode, mock_extract):
        doc = Document.objects.create(
            user=self.user,
            parsed=True,
            extracted_text='Worked with Python and Django'
        )
        
        mock_extract.return_value = ['Python', 'Django']
        mock_encode.return_value = [0.1] * 384
        
        response = self.client.post('/api/skills/extract/', {
            'document_id': str(doc.id),
            'use_llm': False
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('extracted', response.data)
        self.assertIn('Python', response.data['extracted'])


class TestSkillsUnauthenticated(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_get_skills_unauthenticated(self):
        response = self.client.get('/api/skills/')
        self.assertEqual(response.status_code, 403)
    
    def test_add_skill_unauthenticated(self):
        response = self.client.post('/api/skills/manual/', {'name': 'Python'})
        self.assertEqual(response.status_code, 403)


class TestSkillsEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_add_skill_empty_name(self):
        response = self.client.post('/api/skills/manual/', {'name': ''})
        self.assertEqual(response.status_code, 400)
    
    @patch('apps.skills.views.extract_skills')
    def test_extract_no_matching_skills(self, mock_extract):
        doc = Document.objects.create(
            user=self.user,
            parsed=True,
            extracted_text='Some random text with no skills'
        )
        mock_extract.return_value = []
        
        response = self.client.post('/api/skills/extract/', {
            'document_id': str(doc.id),
            'use_llm': False
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['extracted'], [])
