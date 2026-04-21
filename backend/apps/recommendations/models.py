"""Course model for learning recommendations."""
import uuid
from django.db import models


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=512)
    provider = models.CharField(max_length=256)
    url = models.URLField(max_length=1024)
    skills_taught = models.JSONField(default=list)  # List of skill names/IDs
    created_at = models.DateTimeField(auto_now_add=True)
