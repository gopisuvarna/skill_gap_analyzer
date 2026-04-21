from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import fitz  # PyMuPDF
import threading
import numpy as np

from django.db import transaction
from django.conf import settings

from .models import Document
from apps.skills.services.resume_skill_tool import SkillTool, normalize_skill
from apps.skills.models import Skill, UserSkill
from apps.embeddings.models import SkillEmbedding
from core.services.embedding_service import encode
from apps.roles.services.role_faiss_manager import get_role_faiss_manager


def _sync_jobs_for_roles(role_titles: list) -> None:
    """Background thread: fetch Adzuna jobs for the user's recommended roles."""
    try:
        from apps.jobs.services import sync_jobs
        total_created = sum(sync_jobs(what=title, max_pages=2) for title in role_titles)
        print(f"✅ Background job sync complete — {total_created} new jobs added")
    except Exception as e:
        print(f"❌ Background job sync failed: {e}")


def _extract_text(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc)


def _save_skills_and_embeddings(user, all_skills: list) -> dict:
    """Persist Skill, UserSkill, and SkillEmbedding rows. Returns skill_name → Skill map."""
    skill_objects = {}
    with transaction.atomic():
        for skill_name in all_skills:
            nm = normalize_skill(skill_name)
            if not nm:
                continue
            skill_obj, _ = Skill.objects.get_or_create(
                normalized_name=nm.lower(),
                defaults={"name": nm},
            )
            UserSkill.objects.get_or_create(
                user=user,
                skill=skill_obj,
                defaults={"source": "document"},
            )
            skill_objects[nm] = skill_obj

    if skill_objects:
        skill_names = list(skill_objects.keys())
        skill_vectors = encode(skill_names, normalize=True, return_numpy=False)
        with transaction.atomic():
            for skill_name, vector in zip(skill_names, skill_vectors):
                SkillEmbedding.objects.update_or_create(
                    skill=skill_objects[skill_name],
                    defaults={"vector": vector},
                )

    return skill_objects


def _search_recommended_roles(all_skills: list) -> list:
    """Run FAISS search and return list of role dicts sorted by score."""
    if not all_skills:
        return []
    skills_vectors_np = encode(all_skills, normalize=True, return_numpy=True)
    query_vector = np.mean(skills_vectors_np, axis=0, keepdims=True)
    results = get_role_faiss_manager().search(query_vector, top_k=30)
    return [
        {
            "role":        meta.get("role", ""),
            "description": meta.get("description", ""),
            "skills":      meta.get("skills", ""),
            "score":       round(score, 4),
        }
        for score, meta in results
    ]


class ResumeUploadView(APIView):
    """
    Upload PDF → Extract Text → Extract Skills (NLP + LLM)
                → Save Document + UserSkills + SkillEmbeddings
                → Trigger background Adzuna sync
                → Return skills + recommended roles
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            file = request.FILES.get("file")
            if not file:
                return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            if not (file.name or "").lower().endswith(".pdf"):
                return Response({"error": "Only PDF files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

            pdf_bytes = file.read()
            extracted_text = _extract_text(pdf_bytes)

            if not extracted_text.strip():
                return Response({"error": "No text extracted from PDF"}, status=status.HTTP_400_BAD_REQUEST)

            skills_data = SkillTool.run(extracted_text)
            _save_skills_and_embeddings(request.user, skills_data["all_skills"])
            recommended_roles = _search_recommended_roles(skills_data["all_skills"])

            Document.objects.create(
                user=request.user,
                parsed=True,
                extracted_text=extracted_text,
                recommended_roles=recommended_roles,
            )

            role_titles = [r["role"] for r in recommended_roles[:5] if r.get("role")]
            if role_titles and not getattr(settings, "TESTING", False):
                threading.Thread(
                    target=_sync_jobs_for_roles,
                    args=(role_titles,),
                    daemon=True,
                ).start()

            return Response({
                "message":           "Skills extracted and saved successfully",
                "rule_based_skills": skills_data["rule_based_skills"],
                "llm_skills":        skills_data["llm_skills"],
                "all_skills":        skills_data["all_skills"],
                "recommended_roles": recommended_roles,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("❌ Upload API Error:", str(e))
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def latest_resume_roles(request):
    """Return recommended_roles from the user's most recent uploaded document."""
    doc = Document.objects.filter(
        user=request.user,
        parsed=True,
    ).order_by("-uploaded_at").first()

    if not doc:
        return Response({"recommended_roles": []})
    return Response({"recommended_roles": doc.recommended_roles or []})