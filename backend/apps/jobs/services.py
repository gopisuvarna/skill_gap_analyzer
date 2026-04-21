"""
Job ingestion service: fetch from Adzuna, store in DB, extract skills,
and upsert Role + RoleSkill rows so the recommendation engine stays fresh.

Flow for every new job:
  1. Save Job row
  2. Extract skills via spaCy (no LLM — zero token cost)
  3. Save Skill + JobSkill rows
  4. Upsert Role row using the search keyword as the canonical role title
  5. Upsert RoleSkill rows — importance weight based on skill position in list
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.services.adzuna_service import fetch_jobs
from apps.skills.services import extract_skills, normalize_skill
from apps.jobs.models import Job, JobSkill
from apps.skills.models import Skill
from apps.roles.models import Role, RoleSkill

logger = logging.getLogger(__name__)


def _get_or_create_skill(name: str) -> Skill:
    nm = normalize_skill(name)
    skill, _ = Skill.objects.get_or_create(
        normalized_name=nm.lower(),
        defaults={"name": nm},
    )
    return skill


def _importance_weight(index: int, total: int) -> float:
    """Top third → 1.0, middle → 0.75, bottom → 0.5"""
    if total == 0:
        return 1.0
    pct = index / total
    if pct < 0.33:
        return 1.0
    if pct < 0.66:
        return 0.75
    return 0.5


def _normalize_role_title(keyword: str) -> str:
    return " ".join(w.capitalize() for w in keyword.strip().split())


def _upsert_role_skills(role: Role, skills: list) -> None:
    total = len(skills)
    for idx, skill in enumerate(skills):
        weight = _importance_weight(idx, total)
        rs, created = RoleSkill.objects.get_or_create(
            role=role,
            skill=skill,
            defaults={"importance_weight": weight},
        )
        if not created and rs.importance_weight < weight:
            rs.importance_weight = weight
            rs.save(update_fields=["importance_weight"])


def purge_old_jobs(days: int) -> int:
    """Delete jobs that have passed their expires_at date. Returns count deleted."""
    cutoff = timezone.now() - timedelta(days=days)
    count, _ = Job.objects.filter(expires_at__lte=cutoff).delete()
    return count


def _get_or_create_role(what: str):
    """Return a Role for the given keyword, or None if no keyword given."""
    if not what:
        return None
    role_title = _normalize_role_title(what)
    role, _ = Role.objects.get_or_create(
        title=role_title,
        defaults={"description": f"Role extracted from live job listings for '{role_title}'."},
    )
    return role


def _build_job_defaults(r: dict) -> dict:
    """Extract Job field values from a raw Adzuna result dict."""
    return {
        "title":       r.get("title", "")[:512],
        "company":     r.get("company", {}).get("display_name", "")[:256],
        "location":    r.get("location", {}).get("display_name", "")[:256],
        "description": r.get("description", "")[:10_000],
        "url":         r.get("redirect_url", ""),
        "salary_min":  r.get("salary_min"),
        "salary_max":  r.get("salary_max"),
        "expires_at":  timezone.now() + timedelta(days=10),
    }


def _process_new_job(job: Job, role) -> None:
    """Extract skills from a newly created job and link them to role."""
    text = f"{job.title} {job.description}"
    skill_names = extract_skills(text, use_llm=False)[:20]

    skill_objects = []
    for name in skill_names:
        skill = _get_or_create_skill(name)
        JobSkill.objects.get_or_create(job=job, skill=skill)
        skill_objects.append(skill)

    if role and skill_objects:
        _upsert_role_skills(role, skill_objects)


def _sync_page(page: int, country: str, what: str, role, seen: set) -> tuple:
    """Sync a single page of Adzuna results. Returns (created_count, stop)."""
    results = fetch_jobs(country=country, page=page, what=what)
    if not results:
        return 0, True

    created = 0
    for r in results:
        ext_id = r.get("id")
        if not ext_id or str(ext_id) in seen:
            continue
        seen.add(str(ext_id))

        with transaction.atomic():
            job, created_flag = Job.objects.get_or_create(
                external_id=str(ext_id),
                defaults=_build_job_defaults(r),
            )
            if created_flag:
                created += 1
                _process_new_job(job, role)

    return created, False


def sync_jobs(
    country: str = "in",
    max_pages: int = 2,
    what: str = "",
) -> int:
    """
    Fetch jobs from Adzuna and write to:
      jobs_job, skills_skill, jobs_jobskill, roles_role, roles_roleskill

    Returns number of new jobs created.
    """
    role = _get_or_create_role(what)
    seen: set = set()
    total_created = 0

    for page in range(1, max_pages + 1):
        created, stop = _sync_page(page, country, what, role, seen)
        total_created += created
        if stop:
            break

    logger.info(
        "sync_jobs done — country=%s, what=%r, new_jobs=%d, role=%s",
        country, what, total_created, role.title if role else "none",
    )
    return total_created