"""
AI Career Mentor chatbot using Groq.
"""

import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.db.models import Prefetch

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

import groq

from apps.skills.models import UserSkill
from apps.roles.models import Role
from apps.roles.services import compute_skill_gap

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """ You are an AI Skill Gap & Career Assistant for a very specific purpose.
The user has already run a resume/skill analysis.

YOUR ALLOWED SCOPE (you MUST stay inside this):
1) Resume / roles / skills:
   - Discuss the user's resume, current roles, target roles, matched skills, and missing skills.
   - Summarize and explain skill gaps and strengths.
2) Roadmaps & learning resources:
   - For missing or weak skills, create step‑by‑step learning roadmaps (beginner → intermediate → advanced where relevant).
   - Suggest practical activities (projects, practice tasks) and reputable online resources
     (official docs, vendor learning paths, Coursera, edX, Udemy, freeCodeCamp, YouTube channels, etc.).
   - When possible, include several concrete links per major skill, but NEVER invent fake course names or URLs.
3) Job‑specific requirements from job descriptions:
   - When the user asks about a specific job, use ONLY the job description text provided in the analysis/context
     to extract and list the important requirements:
       • key responsibilities
       • required hard skills and tools/technologies
       • required soft skills
       • experience/seniority level
   - Do NOT add skills or requirements that are not clearly implied by the job description.

OUT‑OF‑SCOPE (you MUST refuse):
- Any question that is not about:
  • resumes, roles, matched skills, missing skills, OR
  • learning roadmaps and online resources for missing skills, OR
  • important requirements/skills for a specific job based on its job description.
- For all such questions, answer with a short refusal such as:
  "I’m a specialized career and skill-gap assistant and can only help with resumes, roles, skills, job descriptions, and learning roadmaps."

STRICT RULES:
- Answer ONLY from the analysis context and retrieved context you are given. Do NOT re-run tools or fetch new data.
- NEVER invent courses, job titles, companies, skills, roles, certifications, or URLs. If something is not in the analysis or retrieved context, say you don't have that information or ask the user to update their analysis.
- Stay unbiased and factual; do not exaggerate matches or make speculative recommendations.
- When prioritizing missing skills, use the provided analysis data (e.g., missing_skills per role, match_score) to order them where possible.
- Keep answers concise, structured, and easy to skim (use headings and bullet points).
"""


# -----------------------------------
# Build Dynamic User Context
# -----------------------------------
def _build_context(user) -> str:
    # Fetch user's skills
    user_skills = list(
        UserSkill.objects.filter(user=user)
        .select_related("skill")
        .values_list("skill__name", flat=True)
    )

    user_skill_ids = {
        str(sid)
        for sid in UserSkill.objects.filter(user=user).values_list(
            "skill_id", flat=True
        )
    }

    # Use top roles from FAISS re-rank (same logic as recommendations endpoint)
    # Falls back to 3 DB roles ordered by creation date if FAISS is unavailable.
    roles = []
    try:
        from core.services.embedding_service import encode_single
        from apps.roles.services import get_faiss_index, re_rank
        from apps.roles.models import RoleSkill

        if user_skills:
            user_vec = encode_single(" ".join(user_skills))
            faiss_index = get_faiss_index()
            candidates = faiss_index.search(user_vec, k=10)
            if candidates:
                role_ids = [rid for rid, _ in candidates]
                role_objs = Role.objects.filter(id__in=role_ids).prefetch_related(
                    Prefetch("skills", queryset=RoleSkill.objects.select_related("skill"))
                )
                role_map = {str(r.id): r for r in role_objs}
                role_list = [{"id": str(rid), "title": role_map[rid].title} for rid in role_ids if rid in role_map]
                role_skills_map = {
                    str(r.id): [
                        {"skill_id": str(rs.skill_id), "skill_name": rs.skill.name, "importance_weight": rs.importance_weight}
                        for rs in r.skills.all()
                    ]
                    for r in role_objs
                }
                top = re_rank(role_list, user_skill_ids, user_skills, role_skills_map, top_k=3)
                roles = [role_map[r["id"]] for r in top if r["id"] in role_map]
    except Exception:
        logger.warning("FAISS context build failed — using DB fallback", exc_info=True)

    # Fallback: stable ordering (not random)
    if not roles:
        roles = list(
            Role.objects.prefetch_related(
                Prefetch("skills", queryset=RoleSkill.objects.select_related("skill"))
            ).order_by("created_at")[:3]
        )

    context_parts = [
        f"User skills: {', '.join(user_skills) if user_skills else 'None'}"
    ]

    for role in roles:
        rs_list = [
            {
                "skill_id": str(rs.skill_id),
                "skill_name": rs.skill.name,
                "importance_weight": rs.importance_weight,
            }
            for rs in role.skills.all()
        ]

        gap = compute_skill_gap(user_skill_ids, rs_list)

        context_parts.append(
            f"Role: {role.title}\n"
            f"Missing skills: {', '.join(gap['missing_skills']) if gap['missing_skills'] else 'None'}\n"
            f"Coverage: {gap['coverage_percent']}%"
        )

    return "\n\n".join(context_parts)


# -----------------------------------
# Chat API
# -----------------------------------
@csrf_protect
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    messages = request.data.get("messages", [])

    if not messages:
        return Response(
            {"detail": "messages required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Initialize Groq client
        client = groq.Groq(api_key=settings.GROQ_API_KEY)

        # Build user-specific context
        context = _build_context(request.user)

        system_message = f"{SYSTEM_PROMPT}\n\nContext:\n{context}"

        # Format conversation history
        formatted_messages = [
            {"role": "system", "content": system_message}
        ]

        for msg in messages:
            role = "user" if msg.get("role") == "user" else "assistant"
            formatted_messages.append(
                {
                    "role": role,
                    "content": msg.get("content", ""),
                }
            )

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Change if needed
            messages=formatted_messages,
            temperature=0.7,
            max_tokens=800,
        )

        reply = response.choices[0].message.content.strip()

        return Response({"message": reply})

    except Exception as e:
        logger.exception("Chatbot error: %s", e)
        return Response(
            {"detail": "Chatbot unavailable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )