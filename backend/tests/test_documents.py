"""Tests for documents API endpoints."""
import secrets
from django.test import TestCase
from unittest.mock import patch, MagicMock
from apps.documents.models import Document
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestResumeUpload(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_upload_pdf_success(self):
        with patch('apps.documents.views.fitz') as mock_fitz_module, \
             patch('apps.documents.views.SkillTool') as mock_skill_tool_class, \
             patch('apps.documents.views.encode') as mock_encode, \
             patch('apps.documents.views.get_role_faiss_manager') as mock_get_faiss, \
             patch('apps.documents.views.SkillEmbedding') as mock_skill_emb, \
             patch('builtins.print'):
            
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = 'Test content with Python and Django skills'
            mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
            mock_fitz_module.open.return_value = mock_doc
            
            mock_tool_instance = MagicMock()
            mock_tool_instance.run.return_value = {
                'rule_based_skills': ['Python'],
                'llm_skills': ['Django'],
                'all_skills': ['Python', 'Django']
            }
            mock_skill_tool_class.run = mock_tool_instance.run
            
            mock_encode.return_value = [[0.1] * 384]
            
            mock_manager = MagicMock()
            mock_manager.search.return_value = [(0.95, {'role': 'Backend Dev', 'skills': 'Python', 'description': 'Test'})]
            mock_get_faiss.return_value = mock_manager
            
            mock_emb_manager = MagicMock()
            mock_emb_manager.filter.return_value.bulk_create.return_value = None
            mock_skill_emb.objects = mock_emb_manager

            import io
            pdf_file = io.BytesIO(b'%PDF-1.4 test content')
            pdf_file.name = 'test.pdf'
            
            response = self.client.post('/api/documents/', {
                'file': pdf_file
            }, format='multipart')
            
            self.assertEqual(response.status_code, 200, response.data)
    
    def test_upload_no_file(self):
        response = self.client.post('/api/documents/')
        self.assertEqual(response.status_code, 400)
    
    def test_upload_non_pdf(self):
        import io
        txt_file = io.BytesIO(b'not a pdf')
        txt_file.name = 'test.txt'
        
        response = self.client.post('/api/documents/', {
            'file': txt_file
        }, format='multipart')
        self.assertEqual(response.status_code, 400)
    
    def test_upload_unauthenticated(self):
        import io
        client = APIClient()
        pdf_file = io.BytesIO(b'%PDF-1.4 test')
        pdf_file.name = 'test.pdf'
        
        response = client.post('/api/documents/', {
            'file': pdf_file
        }, format='multipart')
        self.assertEqual(response.status_code, 403)


class TestLatestResumeRoles(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_roles_no_documents(self):
        response = self.client.get('/api/documents/latest-roles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['recommended_roles'], [])
    
    def test_get_roles_with_document(self):
        Document.objects.create(
            user=self.user,
            parsed=True,
            recommended_roles=[{'role': 'Backend Dev', 'score': 0.9}]
        )
        
        response = self.client.get('/api/documents/latest-roles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['recommended_roles']), 1)
        self.assertEqual(response.data['recommended_roles'][0]['role'], 'Backend Dev')
    
    def test_get_roles_unparsed_document(self):
        Document.objects.create(
            user=self.user,
            parsed=False
        )
        
        response = self.client.get('/api/documents/latest-roles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['recommended_roles'], [])


class TestDocumentsEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_secret = make_test_secret()
        user2_secret = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=user_secret
        )
        self.user2 = User.objects.create_user(
            email='other@example.com',
            password=user2_secret
        )
        self.client.force_authenticate(user=self.user)
    
    def test_cannot_access_other_user_documents(self):
        doc = Document.objects.create(user=self.user2, parsed=True)
        
        response = self.client.get(f'/api/documents/{doc.id}/')
        self.assertEqual(response.status_code, 404)