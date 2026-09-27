# Celery + Redis Jobs Architecture — Developer Guide

**Audience:** developers adapting `AI_SDR_CampaignManagement-ElevenLabs` (and similar apps) away from in-process APScheduler toward Celery + Redis.  
**Whole POC architecture (FE + BE + DB + jobs):** [ARCHITECTURE_README.md](./ARCHITECTURE_README.md)  
**Reference implementation:** this folder — `customer-architecture-poc`.  
**Quick ops cheat sheet:** [backend/JOBS.md](./backend/JOBS.md)

---

## 1. Problem we are solving

In **AI_SDR_CampaignManagement-ElevenLabs**, scheduled work is registered with **APScheduler inside the FastAPI/uvicorn process** (`campaigns/jobs/runner.py` on app startup).

That causes:

| Pain | Impact |
|---|---|
| Scheduler lives in the API process | Must keep `UVICORN_WORKERS=1` or jobs duplicate |
| Poor run tracking | Mostly logs; hard to answer “did status_sync run for tenant X?” |
| Weak retries / visibility | Failures are easy to miss; no standard dead-letter path |
| Overlap handled ad hoc | DB locks / `is_processing` scattered in job code |
| API and jobs coupled | Scaling HTTP traffic scales (or breaks) cron behaviour |
| Hard to reason about ownership | ~25 crons mixed with request handlers |

**Goal of this POC:** show a small, production-shaped alternative that developers can copy into the real campaign service.

---

## 2. Target architecture (what to explain)

```text
┌─────────────────┐     schedule      ┌─────────┐     queue      ┌─────────────────┐
│  Celery Beat    │ ───────────────►  │  Redis  │ ─────────────► │  Celery Worker  │
│  (scheduler)    │                   │ broker  │                │  (executors)    │
└─────────────────┘                   └────┬────┘                └────────┬────────┘
                                           │                              │
                                           │                         write runs
                                           ▼                              ▼
                                    ┌──────────────┐              ┌──────────────────┐
                                    │ FastAPI API  │◄─────────────│ generic.job_runs │
                                    │ /api/jobs/*  │   query      │ (platform DB)    │
                                    └──────────────┘              └──────────────────┘
```

### Process responsibilities

| Process | Does | Does **not** |
|---|---|---|
| **API** (`backend`) | HTTP, enqueue manual triggers, read `job_runs` | Own a scheduler loop |
| **Beat** | Fire schedules on time | Run heavy business logic |
| **Worker** | Execute tasks, retries, tenant fan-out | Serve HTTP |
| **Redis** | Broker + result backend | Store business data (MySQL still owns that) |
| **MySQL `generic`** | Tenant catalog + **job run history** | Replace Redis as queue |

### Why this is better for multi-tenant SDR

Campaign / status / deliverability jobs almost always need a **tenant context** (`customer_id` → schema).  

Pattern used in the POC:

```text
Beat:  lead_status_sync          (platform / orchestrator task)
Worker fan-out:
         tenant_lead_status_sync(customer-1)
         tenant_lead_status_sync(customer-2)
         tenant_lead_status_sync(customer-3)
```

Each child task:

1. Receives explicit `customer_id` (no process-local “current tenant”)
2. Touches only that tenant’s schema
3. Writes its own row to `generic.job_runs`
4. Optionally loads customer-specific enrichment from `app/customers/<id>/jobs.py`

That mirrors how frontend/backend already use **base + customer folder overrides**.

---

## 3. Mapping: ElevenLabs today → POC tomorrow

| ElevenLabs (today) | POC / target | Notes |
|---|---|---|
| `AsyncIOScheduler` in `main.py` startup | Celery **Beat** container | Scheduler outside API |
| `campaigns/jobs/runner.py` `add_job(...)` | `celery_app.conf.beat_schedule` | Declarative schedule |
| `campaigns/jobs/definitions.py` functions | `@celery_app.task` in `app/jobs/tasks.py` | Pure callables → tasks |
| In-process callback | Worker process | Horizontally scalable |
| Log lines only | `generic.job_runs` + `/api/jobs/runs` | Auditable history |
| `UVICORN_WORKERS=1` constraint | Remove for job reasons | API workers free to scale |
| Per-campaign DB locks | Still useful **plus** Celery `acks_late` / retries | Locks protect data; queue protects execution |
| Optional `max_instances=1` | Prefer one Beat + idempotent tasks | Avoid multi-Beat without a lock/leader |

### Suggested first migrations from ElevenLabs (lowest risk)

1. **Invoice hourly / daily** — already self-contained runners  
2. **One deliverability poll** (e.g. Smartlead reply or Mailgun poll)  
3. **One campaign tick** (e.g. `status_sync_cron` or `email_campaign_cron`) with explicit tenant fan-out  

Do **not** move all ~25 jobs in one PR. Use this POC as the template for the first 1–3.

---

## 4. Code map in this repository

| Path | Purpose |
|---|---|
| `docker-compose.yml` | `redis`, `backend`, `worker`, `beat`, `db`, `frontend` |
| `backend/app/core/celery_app.py` | Celery app + `beat_schedule` |
| `backend/app/jobs/tasks.py` | Task implementations + tenant fan-out |
| `backend/app/jobs/tracking.py` | Start/finish writes to `job_runs` |
| `backend/app/jobs/routes.py` | `GET /api/jobs/schedule`, `GET /api/jobs/runs`, `POST /api/jobs/trigger/{name}` |
| `backend/app/customers/customer_1/jobs.py` | Optional customer override (`enrich_status_sync`) |
| `backend/migrations/platform/versions/p002_job_runs.py` | Platform table for run history |
| `backend/docker-entrypoint.sh` | `api` \| `worker` \| `beat` roles |

### Demo schedules in the POC

| Beat name | Interval | Analogy |
|---|---|---|
| `lead-status-sync` | every 60s | `status_sync_cron` |
| `platform-heartbeat` | every 30s | Scheduler liveness |
| `hourly-tenant-digest` | crontab hourly | Crontab-style jobs |

---

## 5. How to run the POC (for demos)

```bash
cd customer-architecture-poc
docker compose up --build
```

```bash
# What Beat is configured to run
curl -s http://localhost:8000/api/jobs/schedule | jq

# Manually enqueue (same path workers use)
curl -s -X POST http://localhost:8000/api/jobs/trigger/lead_status_sync | jq

# Tracked history (includes Beat + manual)
curl -s 'http://localhost:8000/api/jobs/runs?limit=20' | jq
```

Expect:

- Parent `lead_status_sync` with `enqueued: 3`
- Child rows for `customer-1`, `customer-2`, `customer-3`
- `customer-1` result includes `solar_note` (customer override)

---

## 6. Adaptation playbook (for ElevenLabs / production)

Use this checklist when porting a real cron.

### Step A — Isolate the job body

1. Find the function in `definitions.py` (or invoice/deliverability module).  
2. Remove FastAPI/request dependencies.  
3. Accept explicit args: `customer_id`, ids, window timestamps, etc.

### Step B — Wrap as a Celery task

```python
@celery_app.task(name="campaigns.tasks.status_sync", bind=True, max_retries=3)
def status_sync(self, customer_id: str) -> dict:
    run_id = start_job_run(job_name="status_sync", customer_id=customer_id, celery_task_id=self.request.id)
    try:
        result = do_status_sync(customer_id)  # existing business logic
        finish_job_run(run_id, status="success", result=result)
        return result
    except Exception as exc:
        finish_job_run(run_id, status="failed", error=str(exc))
        raise self.retry(exc=exc)
```

### Step C — Register schedule in Beat (not in FastAPI lifespan)

```python
beat_schedule = {
    "status-sync": {
        "task": "campaigns.tasks.status_sync_fanout",  # or per-tenant entries
        "schedule": crontab(minute="*/15"),
    },
}
```

### Step D — Remove APScheduler registration

- Delete / stop calling `setup_campaign_cron_jobs()` from API startup for migrated jobs.  
- Keep a feature flag during rollout: `USE_CELERY_FOR_STATUS_SYNC=true`.

### Step E — Deploy three runtimes

| Runtime | Command (pattern) |
|---|---|
| API | `uvicorn ...` |
| Worker | `celery -A ... worker` |
| Beat | `celery -A ... beat` |

Same image, different command (as in this POC’s `docker-entrypoint.sh`).

### Step F — Verify

- [ ] Job appears in `/api/jobs/runs` (or your metrics/UI)  
- [ ] API can run with `UVICORN_WORKERS>1` without duplicate schedules  
- [ ] Killing API does **not** stop Beat/Worker  
- [ ] Tenant A failure does not block Tenant B child tasks  
- [ ] Retries are visible as failed → success (or exhausted) runs  

---

## 7. Design rules (non-negotiable for adaptation)

1. **API has no scheduler.** FastAPI may *enqueue*; it must not *own* cron loops.  
2. **Tenant context is an argument.** Never rely on thread-locals or “whatever customer the API last saw.”  
3. **Track every run** (start + finish + error) in a durable store (`generic.job_runs` or equivalent).  
4. **Prefer small tasks.** Fan-out orchestrator + per-tenant unit beats one giant multi-tenant loop.  
5. **Customer overrides stay in customer folders** (`customers/<id>/jobs.py`), same as FE/BE.  
6. **Idempotency.** Tasks may retry; business writes must tolerate re-entry (or use locks carefully).  
7. **One Beat in an environment** unless you add distributed locking / leader election.  
8. **Schema still follows platform → base → customer migrations**; `job_runs` is a **platform** table.

---

## 8. Alignment with the rest of this POC

This jobs change fits the same product model already used for UI/API/DB:

| Layer | Base | Customer override |
|---|---|---|
| Frontend | `frontend/app/core/` | `frontend/app/customers/<id>/` |
| Backend API | `backend/app/core/`, `domains/` | `backend/app/customers/<id>/` |
| DB | `migrations/base` | `customers/<id>/migrations` |
| **Jobs** | `backend/app/jobs/` | `customers/<id>/jobs.py` |

Install order reminder:

1. Bootstrap empty DBs (`db/init`)  
2. Platform Alembic (`generic`, including `job_runs`)  
3. Base fan-out  
4. Customer migrations  
5. Seed  
6. Deploy **API → Worker/Beat → Frontend**

---

## 9. Talking points for the team

Use these when presenting:

1. **“We are not deleting jobs — we are relocating them.”** Same business logic; different runtime.  
2. **“Beat replaces APScheduler; Worker replaces in-process callbacks; Redis is the queue.”**  
3. **“`job_runs` gives us the tracking we never had.”**  
4. **“API scaling is no longer blocked by cron duplication.”**  
5. **“Multi-tenant fan-out is explicit and testable.”**  
6. **“Migrate incrementally — start with 1–3 crons behind a flag.”**

---

## 10. Out of scope for this POC (call out honestly)

- Celery Flower / full ops dashboard  
- Dynamic schedules stored in DB (possible later)  
- Redis as distributed lock service for every legacy DB lock  
- Moving all ElevenLabs deliverability/invoice/campaign crons  
- Multi-region Beat HA  

Those can follow once the pattern is proven on the first migrated jobs.

---

## 11. Related docs

| Doc | Contents |
|---|---|
| [README.md](./README.md) | Full customer-architecture POC |
| [backend/JOBS.md](./backend/JOBS.md) | Short runbook + demo curls |
| [backend/migrations/README.md](./backend/migrations/README.md) | Platform / base / customer migration order |
| [db/README.md](./db/README.md) | Bootstrap-only DB creation |

---

## 12. Success criteria for “architecture adapted”

Developers can claim the change is adopted when:

- [ ] At least one former APScheduler job runs only via Celery Beat + Worker  
- [ ] That job writes durable run history  
- [ ] API process no longer registers that job  
- [ ] Staging can run API with multiple workers without duplicate schedules  
- [ ] Runbook exists for adding the next cron using this template  
