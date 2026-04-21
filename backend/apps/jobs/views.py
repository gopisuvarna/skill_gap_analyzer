"""Job listing and matching views."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.jobs.models import Job, JobSkill
from apps.skills.models import UserSkill


def _active_jobs():
    """Base queryset — excludes expired jobs."""
    return Job.objects.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )


def _job_dict(job, user_skill_ids=None):
    """Serialize a Job instance to a dict."""
    skills = list(job.skills.all())
    matched = (
        [s.skill.name for s in skills if s.skill_id in user_skill_ids]
        if user_skill_ids else []
    )
    return {
        "id":             str(job.id),
        "title":          job.title,
        "company":        job.company,
        "location":       job.location,
        "url":            job.url,
        "salary_min":     float(job.salary_min) if job.salary_min else None,
        "salary_max":     float(job.salary_max) if job.salary_max else None,
        "skills":         [s.skill.name for s in skills],
        "matched_skills": matched,
        "posted_at":      job.created_at.isoformat(),
        "expires_at":     job.expires_at.isoformat() if job.expires_at else None,
        "is_expired":     job.is_expired,
    }


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_jobs(request):
    """
    Paginated job list with optional search. Expired jobs are excluded.

    Query params:
        page        (int, default 1)
        per_page    (int, default 20, max 50)
        q           (str) — search title or company
    """
    page     = max(1, int(request.query_params.get("page", 1)))
    per_page = min(int(request.query_params.get("per_page", 20)), 50)
    q        = request.query_params.get("q", "").strip()
    offset   = (page - 1) * per_page

    qs = _active_jobs().prefetch_related(
        Prefetch("skills", queryset=JobSkill.objects.select_related("skill"))
    ).order_by("-created_at")

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__icontains=q))

    total = qs.count()
    jobs  = qs[offset : offset + per_page]

    return Response({
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "results":  [_job_dict(j) for j in jobs],
    })


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def matched_jobs(request):
    """
    Jobs whose required skills overlap with the user's skills.
    Ordered by number of matched skills (best match first).
    Expired jobs are excluded.

    Query params:
        limit   (int, default 20, max 50)
        q       (str) — filter by title / company
    """
    limit = min(int(request.query_params.get("limit", 20)), 50)
    q     = request.query_params.get("q", "").strip()

    user_skill_ids = set(
        UserSkill.objects.filter(user=request.user).values_list("skill_id", flat=True)
    )
    if not user_skill_ids:
        return Response({"results": [], "total": 0})

    # Find active jobs that share at least one skill with the user, ranked by match count
    active_job_ids = _active_jobs().values_list("id", flat=True)

    job_ids_ranked = (
        JobSkill.objects
        .filter(skill_id__in=user_skill_ids, job_id__in=active_job_ids)
        .values("job_id")
        .annotate(match_count=Count("id"))
        .order_by("-match_count")
        .values_list("job_id", flat=True)[:limit * 2]
    )

    qs = Job.objects.filter(id__in=job_ids_ranked).prefetch_related(
        Prefetch("skills", queryset=JobSkill.objects.select_related("skill"))
    )

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__icontains=q))

    job_map = {str(j.id): j for j in qs}
    ordered = [job_map[str(jid)] for jid in job_ids_ranked if str(jid) in job_map]

    return Response({
        "results": [_job_dict(j, user_skill_ids) for j in ordered[:limit]],
        "total":   len(ordered),
    })


@require_GET
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def job_stats(request):
    """
    Quick stats for the jobs page header:
    total active jobs in DB, how many match the user, last sync time.
    """
    user_skill_ids = set(
        UserSkill.objects.filter(user=request.user).values_list("skill_id", flat=True)
    )
    active_qs     = _active_jobs()
    total_jobs    = active_qs.count()
    matched_count = (
        JobSkill.objects
        .filter(skill_id__in=user_skill_ids, job__in=active_qs)
        .values("job_id").distinct().count()
        if user_skill_ids else 0
    )
    latest = Job.objects.order_by("-created_at").values_list("created_at", flat=True).first()

    return Response({
        "total_jobs":    total_jobs,
        "matched_count": matched_count,
        "last_synced":   latest.isoformat() if latest else None,
    })