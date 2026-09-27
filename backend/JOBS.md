# Celery + Redis jobs POC

> Full developer architecture + adaptation guide:  
> **[../CELERY_REDIS_ARCHITECTURE_README.md](../CELERY_REDIS_ARCHITECTURE_README.md)**

Replaces the **in-process APScheduler** pattern used by
`AI_SDR_CampaignManagement-ElevenLabs` (`campaigns/jobs/runner.py` inside uvicorn).

## Why

| Today (ElevenLabs) | This POC |
|---|---|
| APScheduler in FastAPI process | Celery Beat (separate process) |
| `UVICORN_WORKERS=1` required | API can scale independently of jobs |
| Logs-only / weak history | `generic.job_runs` table |
| Overlap guarded ad hoc in MySQL | `acks_late` + per-tenant task units + retries |
| ~25 crons mixed with API | Small demo schedule + fan-out pattern |

## Architecture

```text
Celery Beat  --schedule-->  Redis  --queue-->  Celery Worker
                                |
                                v
                         generic.job_runs
                                |
                         FastAPI /api/jobs/*
```

Tenant fan-out (same idea as campaign crons per client schema):

```text
lead_status_sync (beat)
    ├── tenant_lead_status_sync(customer-1)  → may use customers/customer_1/jobs.py
    ├── tenant_lead_status_sync(customer-2)  → base only
    └── tenant_lead_status_sync(customer-3)  → base only
```

## Services (Compose)

| Service | Role |
|---|---|
| `redis` | Broker + result backend |
| `beat` | Schedules (was APScheduler) |
| `worker` | Executes tasks |
| `backend` | API only — no embedded cron |

## Demo schedule

| Beat entry | Interval | Maps to ElevenLabs idea |
|---|---|---|
| `lead-status-sync` | 60s | `status_sync_cron` |
| `platform-heartbeat` | 30s | Scheduler liveness |
| `hourly-tenant-digest` | crontab hourly | Crontab-style jobs |

## Try it

```bash
docker compose up --build

# Schedule + triggerable names
curl -s http://localhost:8000/api/jobs/schedule | jq

# Manual enqueue
curl -s -X POST http://localhost:8000/api/jobs/trigger/lead_status_sync | jq

# Tracked history (wait a few seconds)
curl -s 'http://localhost:8000/api/jobs/runs?limit=20' | jq
```

Customer-1 rows include `solar_note` from `app/customers/customer_1/jobs.py`.

## Mapping a real ElevenLabs cron later

1. Move job body from `definitions.py` into a Celery `@task`
2. Register schedule in `app/core/celery_app.py` `beat_schedule` (or dynamic DB schedule)
3. Pass `customer_id` / tenant context explicitly — never rely on process-local state
4. Write start/finish rows via `app.jobs.tracking` (or shared observability lib)
5. Keep FastAPI free of `AsyncIOScheduler`
