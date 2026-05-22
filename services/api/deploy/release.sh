#!/usr/bin/env bash
# Production release script · runs on every Fly.io deploy.
#
#   1. Run any pending Alembic migrations
#   2. Run the idempotent demo seed (so /verify/{slug} and the ledger
#      have something to resolve on first launch)
#   3. Exec into uvicorn as PID 1
#
# This script is intentionally idempotent · re-running on each cold start
# is safe and helps recover from partial deploys.

set -euo pipefail

echo "═══ DefendableOS API · release ═══"

# Fail fast if the database URL isn't set · the FastAPI process would
# crash later anyway but with a less actionable error.
: "${DATABASE_URL:?DATABASE_URL must be set in fly secrets}"

echo "[release] running alembic upgrade head"
alembic upgrade head

# Seed is best-effort · the seed script is idempotent (uses _ensure_*
# helpers) so it's safe to run on every cold start. If it fails, we
# explicitly dump the full traceback to logs (instead of swallowing it)
# so prod-only failures are diagnosable from `fly logs`. The boot does
# not abort · the API still comes up; the deed just won't resolve until
# the issue is fixed.
if [ "${SEED_DEMO_DATA:-true}" = "true" ]; then
  echo "[release] running idempotent demo seed"
  if ! python -m app.services.seed; then
    echo "[release] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "[release] ⚠ SEED FAILED · the API will boot without the demo deed."
    echo "[release]   Re-run after the fix:"
    echo "[release]     fly ssh console --app defendableos-api -C 'python -m app.services.seed'"
    echo "[release] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  fi
fi

echo "[release] starting uvicorn"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${UVICORN_WORKERS:-2}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
