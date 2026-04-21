"""Embedding storage for skills and roles."""
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


class SkillEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    skill = models.OneToOneField('skills.Skill', on_delete=models.CASCADE, related_name='embedding')
    vector = ArrayField(models.FloatField(), size=384)
    created_at = models.DateTimeField(auto_now_add=True)


class RoleEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.OneToOneField('roles.Role', on_delete=models.CASCADE, related_name='embedding')
    vector = ArrayField(models.FloatField(), size=384)
    created_at = models.DateTimeField(auto_now_add=True)