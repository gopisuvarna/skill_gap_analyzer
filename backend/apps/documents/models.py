"""Document model for user uploads."""
import uuid
from django.conf import settings
from django.db import models


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed = models.BooleanField(default=False)
    extracted_text = models.TextField(blank=True)
    recommended_roles = models.JSONField(default=list, blank=True)