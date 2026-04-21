"""Role and role-skill models for matching engine."""
import uuid
from django.db import models


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255,unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class RoleSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='role_skills')
    importance_weight = models.FloatField(default=1.0)  # 0.0-1.0
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'skill')
        indexes = [models.Index(fields=('role', 'skill'))]
