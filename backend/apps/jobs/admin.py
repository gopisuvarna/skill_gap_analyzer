from django.contrib import admin
from .models import Job, JobSkill


class JobSkillInline(admin.TabularInline):
    model = JobSkill
    extra = 0


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    inlines = [JobSkillInline]
    list_display = ('title', 'company', 'created_at')
    search_fields = ('title', 'company', 'description')


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = ('job', 'skill')
