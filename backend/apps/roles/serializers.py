"""Role serializers."""
from rest_framework import serializers
from .models import Role, RoleSkill


class RoleSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = RoleSkill
        fields = ('skill_id', 'skill_name', 'importance_weight')


class RoleSerializer(serializers.ModelSerializer):
    skills = RoleSkillSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ('id', 'title', 'description', 'skills')
