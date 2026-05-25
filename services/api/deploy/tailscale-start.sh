#!/usr/bin/env bash
# Optional tailscale sidecar for the Fly machine.
#
# When TS_AUTHKEY is set (Fly secret), join the Swarm & Bee tailnet so the
# API can reach in-house model servers (smash · rails · whale) over private
# WireGuard. When unset · no-op · the container behaves as before.
#
# Userspace networking is required because Fly machines do not give us
# access to the kernel /dev/net/tun device by default.
#
# CRITICAL · this script MUST NEVER block release.sh / uvicorn from booting.
# Tailscale is an optional sidecar · a failure here MUST NOT take the API
# down. The script always exits 0 · logs problems · keeps moving. If you
# need to debug tailnet reach, check /var/log/tailscaled.log inside the
# machine via `flyctl ssh console`.
#
# Doctrine: sovereign hot path · never expose smash:8088 to the public
# internet · tailnet is the bridge. But the API takes precedence · so this
# sidecar fails OPEN to keep the production rail serving.
set -u  # nounset only · NEVER set -e here · we trap our own errors

if [[ -z "${TS_AUTHKEY:-}" ]]; then
  echo "[tailscale-start] TS_AUTHKEY not set · skipping tailnet join · model_provider must stay on public providers"
  exit 0
fi

mkdir -p /var/lib/tailscale /var/run/tailscale

# Start tailscaled in userspace mode (no tun device required).
# socks5/http proxies expose tailnet reach for httpx · we plumb env in the
# next block so the API client picks it up automatically.
if ! command -v tailscaled >/dev/null 2>&1; then
  echo "[tailscale-start] tailscaled binary missing · cannot join tailnet · failing OPEN (API still boots)"
  exit 0
fi

tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/var/run/tailscale/tailscaled.sock \
  --tun=userspace-networking \
  --socks5-server=localhost:1055 \
  --outbound-http-proxy-listen=localhost:1055 \
  >/var/log/tailscaled.log 2>&1 &

TAILSCALED_PID=$!

# Give it a beat to come up · max 15s.
for _ in $(seq 1 15); do
  if tailscale --socket=/var/run/tailscale/tailscaled.sock status >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

HOSTNAME_FROM_ENV="${TS_HOSTNAME:-defendableos-api-$(hostname 2>/dev/null || echo unknown)}"

# tailscale up · with a timeout so we never block release.sh forever.
# Any failure here just logs · we still fall through to release.sh.
if ! timeout 30 tailscale --socket=/var/run/tailscale/tailscaled.sock up \
      --authkey="${TS_AUTHKEY}" \
      --hostname="${HOSTNAME_FROM_ENV}" \
      --accept-routes \
      --accept-dns=false \
      --ssh=false >/var/log/tailscale-up.log 2>&1; then
  echo "[tailscale-start] tailscale up failed or timed out · check /var/log/tailscale-up.log · API will still boot · model_provider must stay on public providers"
  # Leave tailscaled running so a later retry could work without restarting the pod.
  exit 0
fi

# Surface the tailnet IP for logging · helpful when grepping fly logs.
TS_IP=$(tailscale --socket=/var/run/tailscale/tailscaled.sock ip -4 2>/dev/null || echo unknown)
echo "[tailscale-start] joined tailnet as ${HOSTNAME_FROM_ENV}: ${TS_IP}"

# Export proxy env so httpx / requests / aiohttp pick up the tailnet route
# transparently. Append to /etc/environment so child processes inherit.
{
  echo "HTTP_PROXY=http://localhost:1055"
  echo "HTTPS_PROXY=http://localhost:1055"
  echo "ALL_PROXY=socks5://localhost:1055"
  echo "NO_PROXY=localhost,127.0.0.1,api.defendableos.com,*.fly.dev,*.upstash.io"
} >> /etc/environment 2>/dev/null || true

# These env exports are only inherited by the current shell · the CMD chain
# that follows uses a sibling process, so /etc/environment + the explicit
# `source /etc/environment` in release.sh handle propagation. The exports
# here are belt-and-suspenders for any immediate child of THIS shell.
export HTTP_PROXY="http://localhost:1055"
export HTTPS_PROXY="http://localhost:1055"
export ALL_PROXY="socks5://localhost:1055"
export NO_PROXY="localhost,127.0.0.1,api.defendableos.com,*.fly.dev,*.upstash.io"

echo "[tailscale-start] proxy env exported · ready for sovereign model calls"
exit 0
