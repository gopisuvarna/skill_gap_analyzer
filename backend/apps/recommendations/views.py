"""Recommendations: role matching, skill gap, learning plan."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch

from apps.skills.models import UserSkill
from apps.roles.models import Role, RoleSkill
from core.services.embedding_service import encode_single
from core.services.learning_recommendation_service import get_courses_for_skills
from apps.roles.services import get_faiss_index, re_rank, compute_skill_gap


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_roles(request):
    """User Vector → FAISS Top 30 → Re-rank → Top 5 Roles."""
    user_skills = list(
        UserSkill.objects
        .filter(user=request.user)
        .select_related('skill')
        .values('skill_id', 'skill__name')
    )
    if not user_skills:
        return Response({'roles': [], 'message': 'Add skills first'})

    user_skill_ids   = {str(s['skill_id']) for s in user_skills}
    user_skill_names = [s['skill__name'] for s in user_skills]
    user_text        = ' '.join(user_skill_names)
    user_vec         = encode_single(user_text)

    faiss_index = get_faiss_index()
    candidates  = faiss_index.search(user_vec, k=30)

    if not candidates:
        roles = Role.objects.prefetch_related(
            Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
        )[:5]
        role_list = [
            {'id': str(r.id), 'title': r.title, 'description': r.description}
            for r in roles
        ]
    else:
        role_ids = [rid for rid, _ in candidates]
        roles = Role.objects.filter(id__in=role_ids).prefetch_related(
            Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
        )
        role_map  = {str(r.id): r for r in roles}
        role_list = [
            {'id': str(rid), 'title': role_map[rid].title, 'description': role_map[rid].description}
            for rid in role_ids if rid in role_map
        ]

    # Build role → skills map (used by re_rank AND returned to frontend)
    role_skills_map = {}
    for r in roles:
        role_skills_map[str(r.id)] = [
            {
                'skill_id':         str(rs.skill_id),
                'skill_name':       rs.skill.name,
                'importance_weight': rs.importance_weight,
            }
            for rs in r.skills.all()
        ]

    ranked = re_rank(role_list, user_skill_ids, user_skill_names, role_skills_map, top_k=5)

    # Attach required_skills and match_score to every ranked role so the
    # frontend can display the match bar without a second request.
    for role in ranked:
        rid            = role['id']
        rs_list        = role_skills_map.get(rid, [])
        skill_names    = [rs['skill_name'] for rs in rs_list]
        matched_count  = sum(1 for n in skill_names if n.lower() in {u.lower() for u in user_skill_names})
        role['required_skills'] = skill_names
        role['match_score']     = round(matched_count / len(skill_names), 4) if skill_names else 0.0

    return Response({'roles': ranked})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skill_gap(request, role_id):
    """Skill Gap = Role Skills - User Skills."""
    user_skill_ids = {
        str(sid)
        for sid in UserSkill.objects.filter(user=request.user).values_list('skill_id', flat=True)
    }

    role = Role.objects.prefetch_related(
        Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
    ).filter(id=role_id).first()
    if not role:
        return Response({'detail': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

    rs_list = [
        {
            'skill_id':         str(rs.skill_id),
            'skill_name':       rs.skill.name,
            'importance_weight': rs.importance_weight,
        }
        for rs in role.skills.all()
    ]
    gap = compute_skill_gap(user_skill_ids, rs_list)
    return Response(gap)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def learning_plan(request, role_id):
    """Missing skills → courses. Top recommendations per missing skill."""
    user_skill_ids = {
        str(sid)
        for sid in UserSkill.objects.filter(user=request.user).values_list('skill_id', flat=True)
    }

    role = Role.objects.prefetch_related(
        Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
    ).filter(id=role_id).first()
    if not role:
        return Response({'detail': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

    missing = [
        rs.skill.name for rs in role.skills.all()
        if str(rs.skill_id) not in user_skill_ids
    ]
    courses = get_courses_for_skills(missing)
    return Response({'missing_skills': missing, 'courses': courses})