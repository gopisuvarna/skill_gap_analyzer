"""Job model for Adzuna real-time ingestion."""
import uuid
from django.db import models
from django.utils import timezone

JOB_EXPIRY_DAYS = 10


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=256, unique=True, db_index=True)
    title = models.CharField(max_length=512)
    company = models.CharField(max_length=256, blank=True)
    location = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=1024, blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return timezone.now() >= self.expires_at


class JobSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='job_skills')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job', 'skill')