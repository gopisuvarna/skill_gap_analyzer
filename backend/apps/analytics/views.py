"""Analytics API: skill distribution, match score, top roles, skill gaps, learning plan, job matches."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Prefetch

from apps.skills.models import UserSkill
from apps.roles.models import Role, RoleSkill
from apps.jobs.models import Job, JobSkill
from core.services.embedding_service import encode_single
from core.services.learning_recommendation_service import get_courses_for_skills
from apps.roles.services import get_faiss_index, re_rank, compute_skill_gap


def _get_top_roles(user_skill_names: list, user_skill_ids: set) -> tuple:
    """Run FAISS search + re-rank. Returns (top_roles, role_skills_map)."""
    if not user_skill_names:
        return [], {}

    user_vec = encode_single(' '.join(user_skill_names))
    faiss_index = get_faiss_index()
    candidates = faiss_index.search(user_vec, k=30)

    if not candidates:
        top_roles = [
            {'id': str(r.id), 'title': r.title, 'match_score': 0.0}
            for r in Role.objects.prefetch_related('skills').order_by('?')[:5]
        ]
        return top_roles, {}

    role_ids = [rid for rid, _ in candidates]
    roles = Role.objects.filter(id__in=role_ids).prefetch_related(
        Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
    )
    role_map = {str(r.id): r for r in roles}
    role_list = [{'id': str(rid), 'title': role_map[rid].title} for rid in role_ids if rid in role_map]
    role_skills_map = {
        str(r.id): [
            {'skill_id': str(rs.skill_id), 'skill_name': rs.skill.name, 'importance_weight': rs.importance_weight}
            for rs in r.skills.all()
        ]
        for r in roles
    }
    top_roles = re_rank(role_list, user_skill_ids, user_skill_names, role_skills_map, top_k=5)
    return top_roles, role_skills_map


def _build_skill_gaps(top_roles: list, role_skills_map: dict, user_skill_ids: set) -> dict:
    """Compute per-role and combined skill gaps."""
    per_role_gaps = []
    combined: dict = {}

    for role_entry in top_roles:
        rid = role_entry.get('id')
        rs_list = role_skills_map.get(rid) or []
        if not rs_list:
            role_obj = Role.objects.prefetch_related(
                Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
            ).filter(id=rid).first()
            if role_obj:
                rs_list = [
                    {'skill_id': str(rs.skill_id), 'skill_name': rs.skill.name, 'importance_weight': rs.importance_weight}
                    for rs in role_obj.skills.all()
                ]

        gap = compute_skill_gap(user_skill_ids, rs_list)
        per_role_gaps.append({
            'role_id':           rid,
            'role_title':        role_entry.get('title', ''),
            'match_score':       role_entry.get('match_score', 0.0),
            'missing_skills':    gap['missing_skills'],
            'coverage_percent':  gap['coverage_percent'],
            'learning_priority': gap['learning_priority'],
        })
        for s in rs_list:
            sid = str(s['skill_id'])
            if sid not in combined or s['importance_weight'] > combined[sid]['importance_weight']:
                combined[sid] = s

    combined_gap = compute_skill_gap(user_skill_ids, list(combined.values()))
    return {
        'per_role':        per_role_gaps,
        'missing_skills':  combined_gap['missing_skills'],
        'coverage_percent': combined_gap['coverage_percent'],
        'learning_priority': combined_gap['learning_priority'],
    }


def _build_job_matches(user_skill_ids: set) -> list:
    """Return top 5 jobs matching user skills."""
    job_ids = (
        JobSkill.objects
        .filter(skill_id__in=user_skill_ids)
        .values_list('job_id', flat=True)
        .distinct()[:10]
    )
    jobs = Job.objects.filter(id__in=job_ids).prefetch_related(
        Prefetch('skills', queryset=JobSkill.objects.select_related('skill'))
    )[:5]
    return [
        {
            'id':             str(j.id),
            'title':          j.title,
            'company':        j.company,
            'location':       j.location or '',
            'url':            j.url,
            'matched_skills': [js.skill.name for js in j.skills.all() if js.skill_id in user_skill_ids],
        }
        for j in jobs
    ]


@api_view(['GET'])
@permission_classes([AllowAny])
def dashboard(request):
    """Dashboard analytics: skills, top roles, gaps, learning plan, job matches."""
    user = request.user
    if not user or not getattr(user, "is_authenticated", False):
        return Response({
            'skill_distribution': [],
            'match_score': 0.0,
            'top_roles': [],
            'skill_gaps': {
                'missing_skills': [], 'coverage_percent': 100.0,
                'learning_priority': [], 'matched_skills': [], 'match_score': 100.0,
            },
            'learning_plan': [],
            'job_matches': [],
            'authenticated': False,
        })

    user_skills = list(
        UserSkill.objects.filter(user=user)
        .select_related('skill')
        .values('skill_id', 'skill__name')
    )
    user_skill_ids = {str(s['skill_id']) for s in user_skills}
    user_skill_names = [s['skill__name'] for s in user_skills]
    skill_distribution = [{'skill': s['skill__name']} for s in user_skills]

    top_roles, role_skills_map = _get_top_roles(user_skill_names, user_skill_ids)

    skill_gaps = _build_skill_gaps(top_roles, role_skills_map, user_skill_ids) if top_roles else {}

    learning_plan = []
    if skill_gaps:
        priority_skills = [
            p['skill_name']
            for p in skill_gaps.get('learning_priority', [])
            if p.get('skill_name')
        ]
        ordered_skills = priority_skills or skill_gaps.get('missing_skills', [])
        if ordered_skills:
            learning_plan = get_courses_for_skills(ordered_skills[:8])

    job_matches = _build_job_matches(user_skill_ids)

    return Response({
        'skill_distribution': skill_distribution,
        'match_score':        top_roles[0]['match_score'] if top_roles else 0.0,
        'top_roles':          top_roles,
        'skill_gaps':         skill_gaps,
        'learning_plan':      learning_plan,
        'job_matches':        job_matches,
        'authenticated':      True,
    })