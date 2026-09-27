"""Celery tasks — base schedules + per-tenant fan-out.

Mirrors AI_SDR CampaignManagement crons without embedding them in uvicorn:
  lead_status_sync     ≈ status_sync_cron (fan-out per tenant)
  tenant_lead_status_sync ≈ per-customer work unit
  platform_heartbeat   ≈ scheduler liveness
  hourly_tenant_digest ≈ crontab-style job
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import create_engine, text

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.jobs.tracking import finish_job_run, start_job_run
from migrations.env_common import database_url_for_schema

logger = logging.getLogger(__name__)


def _list_tenant_ids() -> list[str]:
    settings = get_settings()
    url = database_url_for_schema(settings.database_url, settings.platform_database)
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT customer_id FROM tenants ORDER BY customer_id")
            ).fetchall()
            return [r[0] for r in rows]
    finally:
        engine.dispose()


def _count_leads(customer_id: str) -> int:
    from app.core.database import CUSTOMER_SCHEMAS

    schema = CUSTOMER_SCHEMAS.get(customer_id)
    if not schema:
        return 0
    settings = get_settings()
    url = database_url_for_schema(settings.database_url, schema)
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return int(conn.execute(text("SELECT COUNT(*) FROM leads")).scalar() or 0)
    finally:
        engine.dispose()


def _customer_tick_note(customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Optional customer override — same preference pattern as FE/BE folders."""
    module_name = f"app.customers.{customer_id.replace('-', '_')}.jobs"
    try:
        import importlib

        module = importlib.import_module(module_name)
        enrich = getattr(module, "enrich_status_sync", None)
        if callable(enrich):
            return enrich(payload)
    except ModuleNotFoundError:
        pass
    return payload


@celery_app.task(name="app.jobs.tasks.platform_heartbeat", bind=True)
def platform_heartbeat(self) -> dict[str, Any]:
    run_id = start_job_run(
        job_name="platform_heartbeat",
        celery_task_id=self.request.id,
    )
    try:
        result = {"ok": True, "scope": "platform"}
        finish_job_run(run_id, status="success", result=result)
        return result
    except Exception as exc:  # noqa: BLE001
        finish_job_run(run_id, status="failed", error=str(exc))
        raise


@celery_app.task(name="app.jobs.tasks.lead_status_sync", bind=True)
def lead_status_sync(self) -> dict[str, Any]:
    """Beat entry: enqueue one tracked task per tenant (no work inside API)."""
    run_id = start_job_run(
        job_name="lead_status_sync",
        celery_task_id=self.request.id,
    )
    try:
        tenant_ids = _list_tenant_ids()
        children = []
        for customer_id in tenant_ids:
            async_result = tenant_lead_status_sync.delay(customer_id)
            children.append(
                {"customer_id": customer_id, "task_id": async_result.id}
            )
        result = {"enqueued": len(children), "children": children}
        finish_job_run(run_id, status="success", result=result)
        return result
    except Exception as exc:  # noqa: BLE001
        finish_job_run(run_id, status="failed", error=str(exc))
        raise


@celery_app.task(
    name="app.jobs.tasks.tenant_lead_status_sync",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def tenant_lead_status_sync(self, customer_id: str) -> dict[str, Any]:
    """Per-tenant unit of work — stand-in for campaign status sync."""
    run_id = start_job_run(
        job_name="tenant_lead_status_sync",
        customer_id=customer_id,
        celery_task_id=self.request.id,
    )
    try:
        lead_count = _count_leads(customer_id)
        payload: dict[str, Any] = {
            "customer_id": customer_id,
            "lead_count": lead_count,
            "source": "base",
        }
        payload = _customer_tick_note(customer_id, payload)
        finish_job_run(run_id, status="success", result=payload)
        logger.info("tenant_lead_status_sync %s → %s", customer_id, payload)
        return payload
    except Exception as exc:  # noqa: BLE001
        finish_job_run(run_id, status="failed", error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="app.jobs.tasks.hourly_tenant_digest", bind=True)
def hourly_tenant_digest(self) -> dict[str, Any]:
    """Crontab-style schedule demo (hourly at :00)."""
    run_id = start_job_run(
        job_name="hourly_tenant_digest",
        celery_task_id=self.request.id,
    )
    try:
        tenant_ids = _list_tenant_ids()
        digest = {
            cid: {"lead_count": _count_leads(cid)} for cid in tenant_ids
        }
        result = {"tenants": digest}
        finish_job_run(run_id, status="success", result=result)
        return result
    except Exception as exc:  # noqa: BLE001
        finish_job_run(run_id, status="failed", error=str(exc))
        raise
