"""Role listing view — paginated."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch

from .models import Role, RoleSkill
from .serializers import RoleSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_roles(request):
    """
    Paginated role listing with optional search and filtering.

    Query params:
        page      (int, default 1)
        per_page  (int, default 20, max 50)
        q         (str) — search by role title
        skill     (str) — filter by skill name (supports multiple: skill=python&skill=django)
        sort      (str) — sort field (title, created_at)
        order     (str) — sort order (asc, desc)
    """
    page     = max(1, int(request.query_params.get('page', 1)))
    per_page = min(int(request.query_params.get('per_page', 20)), 50)
    q        = request.query_params.get('q', '').strip()
    skills   = request.query_params.getlist('skill')
    sort     = request.query_params.get('sort', 'id')
    order    = request.query_params.get('order', 'asc')
    offset   = (page - 1) * per_page

    qs = Role.objects.prefetch_related(
        Prefetch('skills', queryset=RoleSkill.objects.select_related('skill'))
    )

    if q:
        qs = qs.filter(title__icontains=q)

    if skills:
        for skill in skills:
            qs = qs.filter(skills__skill__normalized_name__exact=skill.lower())
        qs = qs.distinct()

    if sort == 'title':
        order_by = f'{"-" if order == "desc" else ""}title'
    else:
        order_by = f'{"-" if order == "desc" else ""}id'
    qs = qs.order_by(order_by)

    total = qs.count()
    roles = qs[offset: offset + per_page]

    return Response({
        'total':    total,
        'page':     page,
        'per_page': per_page,
        'results':  RoleSerializer(roles, many=True).data,
    })