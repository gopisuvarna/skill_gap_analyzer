from django.contrib import admin
from .models import SkillEmbedding, RoleEmbedding


@admin.register(SkillEmbedding)
class SkillEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('skill', 'created_at')


@admin.register(RoleEmbedding)
class RoleEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('role', 'created_at')
