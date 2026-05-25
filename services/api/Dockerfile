# DefendableOS API · production container.
# Used by Fly.io · also runs locally via `docker compose up api`.

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build-time toolchain (psycopg, bcrypt, pymupdf wheels are mostly precompiled
# but build-essential covers the edge cases) + curl for healthcheck + tailscale
# so the Fly machine can reach in-house model servers (smash · rails · whale)
# on the tailnet without exposing them to the public internet.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq5 \
    iptables \
    iproute2 \
 && curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg \
      | tee /usr/share/keyrings/tailscale-archive-keyring.gpg > /dev/null \
 && curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.tailscale-keyring.list \
      | tee /etc/apt/sources.list.d/tailscale.list > /dev/null \
 && apt-get update && apt-get install -y --no-install-recommends tailscale \
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

# tailscale-start.sh is OPTIONAL and FAILS OPEN · whether it succeeds, fails,
# or is killed mid-flight, release.sh MUST still run so uvicorn boots. The
# semicolon (not &&) guarantees the API rail is never blocked by a sidecar.
CMD ["bash", "-lc", "bash deploy/tailscale-start.sh; exec bash deploy/release.sh"]
