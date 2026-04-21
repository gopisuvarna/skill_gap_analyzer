from django.contrib import admin
from .models import Skill, UserSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'normalized_name', 'created_at')
    search_fields = ('name', 'normalized_name')


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'source', 'created_at')
    list_filter = ('source',)
