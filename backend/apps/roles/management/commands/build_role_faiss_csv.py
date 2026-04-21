"""Build FAISS index for IT roles from CSV (roles/data/IT_Job_Roles_Skills.csv)."""
from django.core.management.base import BaseCommand

from apps.roles.services.role_embedding_pipeline import RoleEmbeddingPipeline


class Command(BaseCommand):
    help = 'Build FAISS index from IT_Job_Roles_Skills.csv in roles/data/'

    def handle(self, *args, **options):
        try:
            pipeline = RoleEmbeddingPipeline()
            pipeline.run()
            self.stdout.write(self.style.SUCCESS('FAISS index built successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(str(e)))
