"""Skill extraction and management views."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_http_methods

from apps.documents.models import Document
from apps.embeddings.models import SkillEmbedding
from core.services.embedding_service import encode_single
from .models import Skill, UserSkill
from .serializers import UserSkillSerializer
from .services import extract_skills, normalize_skill


def get_or_create_skill(name: str):
    nm = normalize_skill(name)
    skill, created = Skill.objects.get_or_create(
        normalized_name=nm.lower(),
        defaults={"name": nm},
    )
    # If this is a brand-new skill, generate and save its embedding immediately
    if created:
        vector = encode_single(nm, normalize=True)
        SkillEmbedding.objects.create(skill=skill, vector=vector)
    return skill


def create_user_skill_response(request):
    skill_name = request.data.get("name")
    if not skill_name:
        return Response(
            {"detail": "name required"}, status=status.HTTP_400_BAD_REQUEST
        )

    skill = get_or_create_skill(skill_name)  # embedding saved inside if new
    us, _ = UserSkill.objects.get_or_create(
        user=request.user,
        skill=skill,
        defaults={"source": "manual"},
    )
    return Response(UserSkillSerializer(us).data, status=status.HTTP_201_CREATED)


@require_POST
@csrf_protect
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def extract_from_document(request):
    """Extract skills from a parsed document and persist UserSkills."""
    doc_id = request.data.get("document_id")
    use_llm = request.data.get("use_llm", False)

    if doc_id:
        doc = Document.objects.filter(user=request.user, id=doc_id).first()
    else:
        doc = Document.objects.filter(user=request.user, parsed=True).first()
        if not doc:
            doc = Document.objects.filter(user=request.user).first()

    if not doc or not doc.extracted_text:
        return Response(
            {"detail": "No parsed document text available"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    skills = extract_skills(doc.extracted_text, use_llm=use_llm)
    with transaction.atomic():
        for s in skills:
            skill = get_or_create_skill(s)  # embedding saved inside if new
            UserSkill.objects.get_or_create(
                user=request.user,
                skill=skill,
                defaults={"source": "document"},
            )

    return Response({
        "extracted": skills,
        "user_skills": UserSkillSerializer(
            UserSkill.objects.filter(user=request.user), many=True
        ).data,
    })


@csrf_protect
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def list_user_skills(request):
    if request.method == "POST":
        return create_user_skill_response(request)

    qs = UserSkill.objects.filter(user=request.user).select_related("skill")
    return Response(UserSkillSerializer(qs, many=True).data)


@require_POST
@csrf_protect
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_user_skill(request):
    return create_user_skill_response(request)


@require_http_methods(["DELETE"])
@csrf_protect
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_user_skill(request, pk):
    deleted, _ = UserSkill.objects.filter(user=request.user, pk=pk).delete()
    if not deleted:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)
