"""
SkillTool — combines spaCy and LLM extractors.
Also exposes extract_skills(), the unified public API used across the project.

Usage:
    from apps.skills.services.skill_matcher import SkillTool, extract_skills
"""
from __future__ import annotations

from typing import List, Set

from .skill_extractor import SkillExtractor, LLMSkillExtractor
from .skill_normalizer import normalize_skill


class SkillTool:
    """
    Combines rule-based (spaCy) and LLM (Groq) extractors.

    use_llm=True  → spaCy + Groq LLaMA  (resume upload — full recall)
    use_llm=False → spaCy only           (jobs sync, seeding — zero token cost)
    """

    rule_extractor = SkillExtractor()
    llm_extractor  = LLMSkillExtractor()

    @staticmethod
    def run(text: str, use_llm: bool = True) -> dict:
        if not text:
            return {"rule_based_skills": [], "llm_skills": [], "all_skills": []}

        rule_skills: Set[str] = set(SkillTool.rule_extractor.extract(text))
        llm_skills: Set[str]  = set(SkillTool.llm_extractor.extract(text)) if use_llm else set()
        final_skills = sorted(rule_skills | llm_skills)

        return {
            "rule_based_skills": sorted(rule_skills),
            "llm_skills":        sorted(llm_skills),
            "all_skills":        final_skills,
        }


def extract_skills(text: str, use_llm: bool = False) -> List[str]:
    """
    Unified extraction API used across the project.

    use_llm=True  → spaCy + Groq LLM  (resume upload only)
    use_llm=False → spaCy only         (jobs sync, role seeding)

    Returns deduplicated, normalized skill list.
    """
    if not text or not text.strip():
        return []

    raw_skills = SkillTool.run(text, use_llm=use_llm).get("all_skills") or []
    seen: set = set()
    result: List[str] = []
    for s in raw_skills:
        ns = normalize_skill(s)
        if not ns:
            continue
        key = ns.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(ns)
    return result