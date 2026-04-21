"""
Seed ALL roles from IT_Job_Roles_Skills.csv into the roles_role and roles_roleskill tables.

Run once after migrations:
    python manage.py seed_roles

Then rebuild the DB-based FAISS index so recommendations and analytics work:
    python manage.py build_faiss_index
"""
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.roles.models import Role, RoleSkill
from apps.skills.models import Skill
from apps.skills.services import normalize_skill

CSV_PATH = (
    Path(__file__).resolve()
    .parent   # commands/
    .parent   # management/
    .parent   # roles/
    .parent   # apps/
    .parent   # backend/
    / "apps" / "documents" / "data" / "IT_Job_Roles_Skills.csv"
)

# Importance weights by skill position in the comma-separated list.
# First few skills listed tend to be the most critical for the role.
def _importance(index: int, total: int) -> float:
    if total == 0:
        return 1.0
    # Top-third → 1.0, middle-third → 0.75, bottom-third → 0.5
    pct = index / total
    if pct < 0.33:
        return 1.0
    if pct < 0.66:
        return 0.75
    return 0.5


def _get_or_create_skill(name: str) -> Skill:
    nm = normalize_skill(name.strip())
    skill, _ = Skill.objects.get_or_create(
        normalized_name=nm.lower(),
        defaults={"name": nm},
    )
    return skill


class Command(BaseCommand):
    help = "Seed all 493 IT roles from CSV into the roles_role and roles_roleskill tables."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing roles before seeding (use on fresh DB only).",
        )

    def handle(self, *args, **options):
        if not CSV_PATH.exists():
            self.stdout.write(self.style.ERROR(f"CSV not found: {CSV_PATH}"))
            return

        if options["clear"]:
            self.stdout.write("Clearing existing roles…")
            Role.objects.all().delete()

        df = pd.read_csv(CSV_PATH, encoding="latin1").dropna(subset=["Job Title", "Skills"])
        self.stdout.write(f"Loading {len(df)} roles from CSV…")

        roles_created = 0
        skills_linked = 0

        for _, row in df.iterrows():
            title       = str(row["Job Title"]).strip()
            description = str(row.get("Job Description", "")).strip()
            raw_skills  = str(row["Skills"]).strip()

            if not title:
                continue

            with transaction.atomic():
                role, created = Role.objects.get_or_create(
                    title=title,
                    defaults={"description": description},
                )
                if created:
                    roles_created += 1

                skill_names = [s.strip() for s in raw_skills.split(",") if s.strip()]
                total = len(skill_names)

                for idx, skill_name in enumerate(skill_names):
                    skill = _get_or_create_skill(skill_name)
                    _, sk_created = RoleSkill.objects.get_or_create(
                        role=role,
                        skill=skill,
                        defaults={"importance_weight": _importance(idx, total)},
                    )
                    if sk_created:
                        skills_linked += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {roles_created} new roles created, {skills_linked} role-skill links added.\n"
                f"Total roles in DB: {Role.objects.count()}\n\n"
                f"Next step: python manage.py build_faiss_index"
            )
        )