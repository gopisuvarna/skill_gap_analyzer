"""Skill serializers."""
from rest_framework import serializers
from .models import Skill, UserSkill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name', 'normalized_name')


class UserSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = UserSkill
        fields = ('id', 'skill', 'skill_name', 'source', 'created_at')
