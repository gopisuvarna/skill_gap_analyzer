"""
APScheduler: sync fresh jobs on startup and every 6 hours,
then automatically rebuild the FAISS index so recommendations
stay current — no manual commands needed after deployment.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
_scheduler = None

_ROLE_KEYWORDS = [
    # Software Engineering
    "software engineer",
    "software developer",
    "python developer",
    "java developer",
    "javascript developer",
    "nodejs developer",
    "react developer",
    "angular developer",
    "vue developer",
    "full stack developer",
    "frontend developer",
    "backend developer",
 
    # Mobile
    "mobile developer",
    "android developer",
    "ios developer",
    "flutter developer",
    "react native developer",
 
    # Data & AI
    "data scientist",
    "data analyst",
    "data engineer",
    "machine learning engineer",
    "ai engineer",
    "nlp engineer",
    "computer vision engineer",
    "deep learning engineer",
    "business intelligence analyst",
    "data architect",
 
    # Cloud & DevOps
    "devops engineer",
    "cloud engineer",
    "aws engineer",
    "azure engineer",
    "site reliability engineer",
    "platform engineer",
    "infrastructure engineer",
    "kubernetes engineer",
 
    # Security
    "cybersecurity engineer",
    "security analyst",
    "penetration tester",
 
    # Database
    "database administrator",
    "sql developer",
 
    # QA & Testing
    "qa engineer",
    "test automation engineer",
 
    # Architecture & Leadership
    "solutions architect",
    "software architect",
    "technical lead",
    "engineering manager",
    "product manager",
    "scrum master",
 
    # Emerging
    "blockchain developer",
    "web3 developer",
    "embedded systems engineer",
    "game developer",
]

def rebuild_faiss_index() -> int:
    from django.db.models import Prefetch
    from apps.roles.models import Role, RoleSkill
    from apps.embeddings.models import RoleEmbedding
    from core.services.embedding_service import encode
    from apps.roles.services import FAISSRoleIndex

    roles = list(
        Role.objects.prefetch_related(
            Prefetch("skills", queryset=RoleSkill.objects.select_related("skill"))
        ).all()
    )

    if not roles:
        print("[Scheduler] No roles in DB — skipping FAISS rebuild")
        return 0

    texts, role_ids = [], []
    for r in roles:
        skill_names = [rs.skill.name for rs in r.skills.all()]
        texts.append(f"{r.title} {' '.join(skill_names)}")
        role_ids.append(str(r.id))

    vectors = encode(texts)

    for role, vec in zip(roles, vectors):
        RoleEmbedding.objects.update_or_create(
            role=role, defaults={"vector": vec}
        )

    index = FAISSRoleIndex()
    index.build(vectors, role_ids)
    print(f"[Scheduler] FAISS index rebuilt — {len(roles)} roles indexed")
    return len(roles)


def run_job_sync(startup: bool = False):
    pages = 1 if startup else 3
    mode = "startup (light)" if startup else "full (6h interval)"
    print(f"[Scheduler] Job sync started — mode={mode}, pages_per_keyword={pages}")

    try:
        from apps.jobs.services import sync_jobs, purge_old_jobs

        # Step 1 — purge old jobs
        removed = purge_old_jobs(days=10)
        if removed:
            print(f"[Scheduler] Purged {removed} stale jobs (>10 days)")

        # Step 2 — sync India
        total_created = 0
        for keyword in _ROLE_KEYWORDS:
            created = sync_jobs(country="in", what=keyword, max_pages=pages)
            total_created += created
            print(f"[Scheduler] IN '{keyword}' → {created} new jobs")

        print(f"[Scheduler] Sync complete — {total_created} new jobs added total")

        # Step 3 — rebuild FAISS (isolated)
        try:
            indexed = rebuild_faiss_index()
            print(f"[Scheduler] Recommendations updated — {indexed} roles in index")
        except Exception as faiss_err:
            print(f"[Scheduler] FAISS rebuild failed (jobs were saved): {faiss_err}")

    except Exception as e:
        print(f"[Scheduler] Sync failed: {e}")
        logger.exception("Job sync failed: %s", e)


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        print("[Scheduler] Already running — skipping duplicate start")
        return

    _scheduler = BackgroundScheduler()

    # Immediate startup sync (light)
    _scheduler.add_job(
        run_job_sync,
        id="job_sync_startup",
        trigger="date",
        kwargs={"startup": True},
    )

    # Full sync every 6 hours
    _scheduler.add_job(
        run_job_sync,
        id="job_sync_interval",
        trigger=IntervalTrigger(hours=6),
        kwargs={"startup": False},
    )

    _scheduler.start()
    print("[Scheduler] APScheduler running — startup sync queued, full sync every 6h")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        print("[Scheduler] Stopped")