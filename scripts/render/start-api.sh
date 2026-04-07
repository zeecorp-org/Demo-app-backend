#!/bin/sh
set -eu

MAX_ATTEMPTS="${MIGRATION_MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${MIGRATION_RETRY_DELAY_SECONDS:-2}"
ATTEMPT=0

until alembic upgrade head; do
  ATTEMPT=$((ATTEMPT + 1))
  if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
    echo "Migrations failed after ${MAX_ATTEMPTS} attempts"
    exit 1
  fi
  echo "Migration attempt ${ATTEMPT}/${MAX_ATTEMPTS} failed, retrying in ${SLEEP_SECONDS}s..."
  sleep "$SLEEP_SECONDS"
done

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
