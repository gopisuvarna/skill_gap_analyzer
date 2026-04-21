"""Build FAISS role index and embeddings."""
import logging
from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from apps.roles.models import Role, RoleSkill
from apps.embeddings.models import RoleEmbedding
from core.services.embedding_service import encode
from apps.roles.services import FAISSRoleIndex

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Build FAISS index and role embeddings'

    def handle(self, *args, **options):
        roles = Role.objects.prefetch_related(
            Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
        ).all()
        if not roles:
            self.stdout.write('No roles found. Create roles first.')
            return

        texts = []
        role_ids = []
        for r in roles:
            skill_names = [rs.skill.name for rs in r.skills.all()]
            text = f"{r.title} {' '.join(skill_names)}"
            texts.append(text)
            role_ids.append(str(r.id))

        vectors = encode(texts)
        for role, vec in zip(roles, vectors):
            RoleEmbedding.objects.update_or_create(
                role=role,
                defaults={'vector': vec},
            )

        index = FAISSRoleIndex()
        index.build(vectors, role_ids)
        self.stdout.write(self.style.SUCCESS(f'Built FAISS index for {len(roles)} roles'))
