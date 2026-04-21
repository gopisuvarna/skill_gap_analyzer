"""Skill and user skill models."""
import uuid
from django.conf import settings
from django.db import models


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    normalized_name = models.CharField(max_length=128, db_index=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class UserSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_skills')
    source = models.CharField(max_length=32, default='document')  # document, manual, job
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'skill')
        indexes = [models.Index(fields=('user', 'skill'))]
