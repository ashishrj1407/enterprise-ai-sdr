#!/bin/sh
set -e

role="${1:-api}"

case "$role" in
  api)
    # Steps 2–5 (platform → base → customer → seed), then API (step 6 with frontend).
    python -m app.core.migrate_all
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec celery -A app.core.celery_app.celery_app worker --loglevel=INFO --concurrency=2
    ;;
  beat)
    exec celery -A app.core.celery_app.celery_app beat --loglevel=INFO
    ;;
  *)
    exec "$@"
    ;;
esac
