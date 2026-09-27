"""Persist Celery job runs into the platform catalog (`generic.job_runs`)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from migrations.env_common import database_url_for_schema


def _platform_engine():
    settings = get_settings()
    url = database_url_for_schema(settings.database_url, settings.platform_database)
    return create_engine(url)


def start_job_run(
    *,
    job_name: str,
    customer_id: str | None = None,
    celery_task_id: str | None = None,
) -> int:
    engine = _platform_engine()
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text(
                    "INSERT INTO job_runs "
                    "(job_name, customer_id, status, celery_task_id) "
                    "VALUES (:job_name, :customer_id, 'started', :celery_task_id)"
                ),
                {
                    "job_name": job_name,
                    "customer_id": customer_id,
                    "celery_task_id": celery_task_id,
                },
            )
            return int(result.lastrowid)
    finally:
        engine.dispose()


def finish_job_run(
    run_id: int,
    *,
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    engine = _platform_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE job_runs SET status = :status, result_json = :result_json, "
                    "error = :error, finished_at = :finished_at WHERE id = :id"
                ),
                {
                    "id": run_id,
                    "status": status,
                    "result_json": json.dumps(result) if result is not None else None,
                    "error": error,
                    "finished_at": datetime.now(timezone.utc).replace(tzinfo=None),
                },
            )
    finally:
        engine.dispose()


def list_job_runs(limit: int = 50) -> list[dict[str, Any]]:
    engine = _platform_engine()
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT id, job_name, customer_id, status, celery_task_id, "
                    "result_json, error, started_at, finished_at "
                    "FROM job_runs ORDER BY id DESC LIMIT :limit"
                ),
                {"limit": limit},
            ).mappings().all()
            out: list[dict[str, Any]] = []
            for row in rows:
                item = dict(row)
                for key in ("started_at", "finished_at"):
                    if item.get(key) is not None:
                        item[key] = item[key].isoformat()
                if item.get("result_json"):
                    try:
                        item["result"] = json.loads(item["result_json"])
                    except json.JSONDecodeError:
                        item["result"] = item["result_json"]
                item.pop("result_json", None)
                out.append(item)
            return out
    finally:
        engine.dispose()
