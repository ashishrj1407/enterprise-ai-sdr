"""Job observability + manual trigger API (base product)."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.jobs.tracking import list_job_runs

router = APIRouter(prefix="/jobs", tags=["jobs"])

TRIGGERABLE = {
    "platform_heartbeat": "app.jobs.tasks.platform_heartbeat",
    "lead_status_sync": "app.jobs.tasks.lead_status_sync",
    "hourly_tenant_digest": "app.jobs.tasks.hourly_tenant_digest",
}


@router.get("/runs")
def job_runs(limit: int = 50) -> dict[str, Any]:
    """Recent Celery job runs from generic.job_runs (tracked history)."""
    return {"runs": list_job_runs(limit=min(limit, 200))}


@router.get("/schedule")
def job_schedule() -> dict[str, Any]:
    """Beat schedule currently configured (outside the API process)."""
    from app.core.celery_app import celery_app

    schedule = {}
    for name, entry in (celery_app.conf.beat_schedule or {}).items():
        sched = entry.get("schedule")
        schedule[name] = {
            "task": entry.get("task"),
            "schedule": str(sched),
        }
    return {
        "broker": "redis",
        "note": "Replaces in-process APScheduler from AI_SDR CampaignManagement",
        "schedule": schedule,
        "triggerable": sorted(TRIGGERABLE.keys()),
    }


@router.post("/trigger/{job_name}")
def trigger_job(job_name: str) -> dict[str, Any]:
    """Enqueue a job immediately (manual / demo)."""
    if job_name not in TRIGGERABLE:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown job. Choose one of: {sorted(TRIGGERABLE)}",
        )
    from app.core.celery_app import celery_app

    async_result = celery_app.send_task(TRIGGERABLE[job_name])
    return {"job_name": job_name, "task_id": async_result.id, "status": "queued"}
