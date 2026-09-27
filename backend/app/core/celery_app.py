"""Celery application — broker Redis; beat schedule lives outside the API process.

Maps the AI_SDR CampaignManagement pattern (APScheduler inside uvicorn) to:
  Beat  → schedules (was AsyncIOScheduler in FastAPI startup)
  Worker → executes (was in-process cron callbacks)
  Redis → broker + result backend
  generic.job_runs → durable run history (was logs-only)
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "customer_architecture_poc",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.jobs.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        # Demo stand-in for campaign status_sync_cron (was */15 in ElevenLabs).
        "lead-status-sync": {
            "task": "app.jobs.tasks.lead_status_sync",
            "schedule": 60.0,  # every 60s for an observable POC
        },
        # Platform heartbeat — proves Beat is alive without tenant fan-out.
        "platform-heartbeat": {
            "task": "app.jobs.tasks.platform_heartbeat",
            "schedule": 30.0,
        },
        # Example of crontab-style schedule (daily-ish demo at :00 of each hour).
        "hourly-tenant-digest": {
            "task": "app.jobs.tasks.hourly_tenant_digest",
            "schedule": crontab(minute=0),
        },
    },
    task_always_eager=settings.celery_task_always_eager,
)
