"""
Skill extraction from text.

Two extractors:
  SkillExtractor     — spaCy phrase matcher against skill.txt (fast, no API cost)
  LLMSkillExtractor  — Groq LLaMA 3.3 (higher recall, used for resume uploads only)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

import spacy
from spacy.matcher import PhraseMatcher
from groq import Groq

from django.conf import settings


class SkillExtractorError(RuntimeError):
    """Raised when the spaCy skill extractor fails to initialise."""


class SkillExtractor:
    """spaCy phrase-matcher against apps/skills/data/skill.txt."""

    _nlp = None
    _matcher = None

    @classmethod
    def _initialize(cls) -> None:
        if cls._nlp is not None:
            return
        try:
            print("[SkillExtractor] Loading spaCy model...")
            cls._nlp = spacy.load("en_core_web_sm")
            matcher = PhraseMatcher(cls._nlp.vocab, attr="LOWER")
            skills_path = Path(__file__).resolve().parent.parent / "data" / "skill.txt"
            if not skills_path.exists():
                raise FileNotFoundError("skill.txt not found in apps/skills/data/")
            skills = [
                line.strip().lower()
                for line in skills_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            patterns = [cls._nlp.make_doc(skill) for skill in skills]
            matcher.add("SKILLS", patterns)
            cls._matcher = matcher
            print(f"[SkillExtractor] Initialized with {len(skills)} skills.")
        except OSError as e:
            raise SkillExtractorError(f"Failed to initialize SkillExtractor: {e}") from e

    @classmethod
    def extract(cls, text: str) -> List[str]:
        """Return sorted list of matched skill strings (lowercased)."""
        if not text:
            return []
        cls._initialize()
        doc = cls._nlp(text)
        matches = cls._matcher(doc)
        skills = {doc[start:end].text.lower() for _, start, end in matches}
        return sorted(skills)


class LLMSkillExtractorError(RuntimeError):
    """Raised when the Groq LLM skill extractor encounters an unrecoverable error."""


_groq_client = Groq(api_key=settings.GROQ_API_KEY)

_LLM_SYSTEM_PROMPT = """
You are an expert resume parsing system.

Your task is to extract ALL professional technical skills from the provided resume text.

INCLUDE:
- Programming languages, frameworks and libraries, databases, cloud platforms,
  DevOps tools, ML/data science tools, web technologies, OS, version control,
  software tools and platforms, technical methodologies.

EXCLUDE:
- Soft skills, personal traits, hobbies, company names (unless they are technologies).

RULES:
- Return ONLY valid JSON. No explanation, no markdown, no extra text.
- Lowercase everything. Remove duplicates.
- Extract both explicitly mentioned and strongly implied technical skills.

FORMAT:
{"skills": ["python", "django", "aws", "machine learning"]}

If no skills are found, return: {"skills": []}
"""


class LLMSkillExtractor:
    """Groq LLaMA 3.3 extractor — higher recall, API cost per call."""

    def extract(self, resume_text: str) -> List[str]:
        """Return deduplicated lowercase skill list from LLM response."""
        if not resume_text:
            return []
        try:
            response = _groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Resume:\n{resume_text}"},
                ],
                temperature=0.0,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"```json|```", "", text).strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            json_text = match.group(0) if match else text
            data = json.loads(json_text)
            skills = data.get("skills", [])
            if not isinstance(skills, list):
                return []
            return list({skill.lower() for skill in skills})
        except (ValueError, KeyError) as e:
            print("[LLMSkillExtractor] Groq extraction error:", e)
            return []