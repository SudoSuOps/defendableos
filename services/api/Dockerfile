# DefendableOS API · production container.
# Used by Fly.io · also runs locally via `docker compose up api`.

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build-time toolchain (psycopg, bcrypt, pymupdf wheels are mostly precompiled
# but build-essential covers the edge cases) + curl for healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq5 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Healthcheck · Fly uses /healthz directly via fly.toml, but Docker
# native healthcheck helps when the same image runs under docker-compose.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

EXPOSE 8000

# release.sh runs alembic + the idempotent demo seed on every deploy.
# Then exec's into uvicorn so the container PID 1 is the API process.
CMD ["bash", "deploy/release.sh"]
