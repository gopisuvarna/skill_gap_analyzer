"""Skills app business logic.

Single source of truth for skill extraction lives in ``resume_skill_tool``.
"""
from .resume_skill_tool import extract_skills, normalize_skill, SkillTool

__all__ = [
    "extract_skills",
    "normalize_skill",
    "SkillTool",
]
