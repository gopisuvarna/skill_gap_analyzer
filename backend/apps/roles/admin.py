from django.contrib import admin
from .models import Role, RoleSkill


class RoleSkillInline(admin.TabularInline):
    model = RoleSkill
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    inlines = [RoleSkillInline]
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')


@admin.register(RoleSkill)
class RoleSkillAdmin(admin.ModelAdmin):
    list_display = ('role', 'skill', 'importance_weight')
    list_filter = ('role',)
