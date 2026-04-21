"""Tests for jobs API endpoints."""
import secrets
from django.test import TestCase
from apps.jobs.models import Job, JobSkill
from apps.skills.models import Skill, UserSkill
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


def make_test_secret() -> str:
    return secrets.token_urlsafe(16)


class TestListJobs(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_list_jobs_empty(self):
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 0)
        self.assertEqual(response.data['results'], [])
    
    def test_list_jobs_with_data(self):
        job = Job.objects.create(
            external_id='ext-123',
            title='Python Developer',
            company='TechCorp',
            location='Remote',
            description='Backend developer needed'
        )
        skill = Skill.objects.create(name='Python', normalized_name='python')
        JobSkill.objects.create(job=job, skill=skill)
        
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Developer')
    
    def test_list_jobs_pagination(self):
        for i in range(25):
            Job.objects.create(
                external_id=f'ext-{i}',
                title=f'Job {i}',
                company='Test Corp'
            )
        
        response = self.client.get('/api/jobs/?page=1&per_page=10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['total'], 25)
        self.assertEqual(response.data['per_page'], 10)
    
    def test_list_jobs_search(self):
        Job.objects.create(external_id='ext-1', title='Python Developer', company='Corp1')
        Job.objects.create(external_id='ext-2', title='Java Developer', company='Corp2')
        
        response = self.client.get('/api/jobs/?q=python')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
        self.assertIn('python', response.data['results'][0]['title'].lower())
    
    def test_list_jobs_unauthenticated(self):
        client = APIClient()
        response = client.get('/api/jobs/')
        self.assertEqual(response.status_code, 403)


class TestMatchedJobs(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_matched_jobs_empty_skills(self):
        response = self.client.get('/api/jobs/matched/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])
    
    def test_matched_jobs_with_matches(self):
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill, source='manual')
        
        job = Job.objects.create(
            external_id='ext-1',
            title='Python Developer',
            company='TechCorp'
        )
        JobSkill.objects.create(job=job, skill=skill)
        
        response = self.client.get('/api/jobs/matched/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('python', [s.lower() for s in response.data['results'][0]['matched_skills']])
    
    def test_matched_jobs_no_match(self):
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill)
        
        job = Job.objects.create(
            external_id='ext-1',
            title='Java Developer',
            company='TechCorp'
        )
        java_skill = Skill.objects.create(name='Java', normalized_name='java')
        JobSkill.objects.create(job=job, skill=java_skill)
        
        response = self.client.get('/api/jobs/matched/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], [])


class TestJobStats(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_job_stats_empty(self):
        response = self.client.get('/api/jobs/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_jobs'], 0)
        self.assertEqual(response.data['matched_count'], 0)
    
    def test_job_stats_with_data(self):
        job = Job.objects.create(
            external_id='ext-1',
            title='Test Job',
            company='Test Corp'
        )
        skill = Skill.objects.create(name='Python', normalized_name='python')
        UserSkill.objects.create(user=self.user, skill=skill)
        JobSkill.objects.create(job=job, skill=skill)
        
        response = self.client.get('/api/jobs/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_jobs'], 1)
        self.assertEqual(response.data['matched_count'], 1)


class TestJobsFiltering(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_filter_jobs_by_skill(self):
        python = Skill.objects.create(name='Python', normalized_name='python')
        job1 = Job.objects.create(external_id='ext-1', title='Python Dev', company='Corp1')
        Job.objects.create(external_id='ext-2', title='Java Dev', company='Corp2')
        JobSkill.objects.create(job=job1, skill=python)
        
        response = self.client.get('/api/jobs/?q=python')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
    
    def test_filter_jobs_by_company(self):
        Job.objects.create(external_id='ext-1', title='Dev', company='Google')
        Job.objects.create(external_id='ext-2', title='Dev', company='Microsoft')
        
        response = self.client.get('/api/jobs/?q=google')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total'], 1)
    
    def test_filter_jobs_multiple_params(self):
        python = Skill.objects.create(name='Python', normalized_name='python')
        job = Job.objects.create(external_id='ext-1', title='Python Dev', company='Google', location='Remote')
        JobSkill.objects.create(job=job, skill=python)
        
        response = self.client.get('/api/jobs/?q=python+google')
        self.assertEqual(response.status_code, 200)


class TestJobsSorting(TestCase):
    def setUp(self):
        self.client = APIClient()
        secret_value = make_test_secret()
        self.user = User.objects.create_user(
            email='test@example.com',
            password=secret_value
        )
        self.client.force_authenticate(user=self.user)
    
    def test_jobs_default_sort(self):
        Job.objects.create(external_id='ext-1', title='Zebra Job', company='A')
        Job.objects.create(external_id='ext-2', title='Alpha Job', company='B')
        
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)