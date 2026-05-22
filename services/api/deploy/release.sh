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
# helpers) so it's safe to run on every cold start. If the user's data
# has diverged from the seed (e.g. they deleted the demo deed), the
# seed will quietly recreate the canonical illustrative record.
if [ "${SEED_DEMO_DATA:-true}" = "true" ]; then
  echo "[release] running idempotent demo seed"
  python -m app.services.seed || echo "[release] seed failed · continuing"
fi

echo "[release] starting uvicorn"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${UVICORN_WORKERS:-2}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
