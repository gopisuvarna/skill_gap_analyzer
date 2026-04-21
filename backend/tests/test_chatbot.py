"""Tests for chatbot API endpoint."""
import unittest
import secrets
from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class TestChatbot(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com')
        self.user.set_password(secrets.token_urlsafe(16))
        self.user.save(update_fields=['password'])
        self.client.force_authenticate(user=self.user)
    
    def test_chat_no_message(self):
        response = self.client.post('/api/chatbot/', {})
        self.assertEqual(response.status_code, 400)
    
    def test_chat_success(self):
        with patch('groq.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content='Test response'))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            response = self.client.generic('POST', '/api/chatbot/', data='{"messages": [{"role": "user", "content": "What skills do I need for Backend Developer?"}]}', content_type='application/json')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertIn('message', response.data)
    
    def test_chat_unauthenticated(self):
        client = APIClient()
        response = client.post('/api/chatbot/', {'message': 'test'})
        self.assertEqual(response.status_code, 403)