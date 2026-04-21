"""Tests for roles API endpoints."""
import secrets
from django.test import TestCase
from apps.roles.models import Role, RoleSkill
from apps.skills.models import Skill
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestListRoles(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_roles_empty(self):
        response = self.client.get('/api/roles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        self.assertEqual(response.data['results'], [])
    
    def test_list_roles_with_data(self):
        role = Role.objects.create(title='Backend Developer')
        skill = Skill.objects.create(name='Python', normalized_name='python')
        RoleSkill.objects.create(role=role, skill=skill, importance_weight=0.8)

        response = self.client.get('/api/roles/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Backend Developer')
    
    def test_list_roles_pagination(self):
        for i in range(25):
            Role.objects.create(title=f'Role {i}')

        response = self.client.get('/api/roles/?page=1&per_page=10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['total'], 25)
    
    def test_list_roles_search(self):
        Role.objects.create(title='Python Developer')
        Role.objects.create(title='Java Developer')

        response = self.client.get('/api/roles/?q=python')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
    
    def test_list_roles_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/roles/')
        self.assertEqual(response.status_code, 403)


class TestRolesFilterBySkill(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_filter_roles_by_skill(self):
        python = Skill.objects.create(name='Python', normalized_name='python')
        java = Skill.objects.create(name='Java', normalized_name='java')
        
        role1 = Role.objects.create(title='Python Developer')
        role2 = Role.objects.create(title='Java Developer')
        role3 = Role.objects.create(title='Full Stack Developer')
        
        RoleSkill.objects.create(role=role1, skill=python, importance_weight=0.9)
        RoleSkill.objects.create(role=role2, skill=java, importance_weight=0.9)
        RoleSkill.objects.create(role=role3, skill=python, importance_weight=0.5)
        RoleSkill.objects.create(role=role3, skill=java, importance_weight=0.5)

        response = self.client.get('/api/roles/?skill=python')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 2)
    
    def test_filter_roles_by_multiple_skills(self):
        python = Skill.objects.create(name='Python', normalized_name='python')
        django = Skill.objects.create(name='Django', normalized_name='django')
        
        role1 = Role.objects.create(title='Python Django Dev')
        role2 = Role.objects.create(title='Python Flask Dev')
        
        RoleSkill.objects.create(role=role1, skill=python, importance_weight=0.8)
        RoleSkill.objects.create(role=role1, skill=django, importance_weight=0.9)
        RoleSkill.objects.create(role=role2, skill=python, importance_weight=0.9)

        response = self.client.get('/api/roles/?skill=python&skill=django')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)


class TestRolesSorting(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_roles_sort_by_title_asc(self):
        Role.objects.create(title='Zebra Developer')
        Role.objects.create(title='Alpha Developer')
        Role.objects.create(title='Beta Developer')

        response = self.client.get('/api/roles/?sort=title&order=asc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['title'], 'Alpha Developer')
    
    def test_roles_sort_by_title_desc(self):
        Role.objects.create(title='Zebra Developer')
        Role.objects.create(title='Alpha Developer')
        Role.objects.create(title='Beta Developer')

        response = self.client.get('/api/roles/?sort=title&order=desc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['title'], 'Zebra Developer')


class TestRolesEdgeCases(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_roles_invalid_page(self):
        for i in range(5):
            Role.objects.create(title=f'Role {i}')
        
        response = self.client.get('/api/roles/?page=999')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])
    
    def test_roles_negative_page(self):
        Role.objects.create(title='Test Role')
        
        response = self.client.get('/api/roles/?page=-1')
        self.assertEqual(response.status_code, 200)
    
    def test_roles_search_case_insensitive(self):
        Role.objects.create(title='PYTHON DEVELOPER')
        Role.objects.create(title='python developer')
        
        response = self.client.get('/api/roles/?q=Python')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 2)
    
    def test_roles_empty_search(self):
        Role.objects.create(title='Test Role')
        
        response = self.client.get('/api/roles/?q=')
        self.assertEqual(response.status_code, 200)
    
    def test_filter_roles_by_nonexistent_skill(self):
        role = Role.objects.create(title='Python Developer')
        python = Skill.objects.create(name='Python', normalized_name='python')
        RoleSkill.objects.create(role=role, skill=python)
        
        response = self.client.get('/api/roles/?skill=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
    
    def test_filter_roles_multiple_skills_no_match(self):
        python = Skill.objects.create(name='Python', normalized_name='python')
        Skill.objects.create(name='Django', normalized_name='django')
        
        role = Role.objects.create(title='Python Only')
        RoleSkill.objects.create(role=role, skill=python)
        
        response = self.client.get('/api/roles/?skill=python&skill=ruby')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
    
    def test_filter_roles_by_skill_case_insensitive(self):
        python = Skill.objects.create(name='Python', normalized_name='python')
        role = Role.objects.create(title='Developer')
        RoleSkill.objects.create(role=role, skill=python)
        
        response = self.client.get('/api/roles/?skill=PYTHON')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)