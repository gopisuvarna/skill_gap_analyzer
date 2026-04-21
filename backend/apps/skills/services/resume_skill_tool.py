"""
Backwards-compatible re-export.

All existing imports of the form:
    from apps.skills.services.resume_skill_tool import SkillTool, normalize_skill, extract_skills
continue to work without any changes elsewhere in the codebase.
"""
from .skill_normalizer import normalize_skill          # noqa: F401
from .skill_extractor  import SkillExtractor           # noqa: F401
from .skill_extractor  import LLMSkillExtractor        # noqa: F401
from .skill_extractor  import SkillExtractorError      # noqa: F401
from .skill_extractor  import LLMSkillExtractorError   # noqa: F401
from .skill_matcher    import SkillTool, extract_skills # noqa: F401