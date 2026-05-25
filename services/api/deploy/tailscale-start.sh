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
# Doctrine: sovereign hot path · never expose smash:8088 to the public
# internet · tailnet is the bridge.
set -euo pipefail

if [[ -z "${TS_AUTHKEY:-}" ]]; then
  echo "[tailscale-start] TS_AUTHKEY not set · skipping tailnet join · model_provider must stay on public providers"
  exit 0
fi

mkdir -p /var/lib/tailscale /var/run/tailscale

# Start tailscaled in userspace mode (no tun device required).
# socks5/http proxies expose tailnet reach for httpx · we plumb env in the
# next block so the API client picks it up automatically.
tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/var/run/tailscale/tailscaled.sock \
  --tun=userspace-networking \
  --socks5-server=localhost:1055 \
  --outbound-http-proxy-listen=localhost:1055 \
  >/var/log/tailscaled.log 2>&1 &

# Give it a beat to come up.
for i in {1..15}; do
  if tailscale --socket=/var/run/tailscale/tailscaled.sock status >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

HOSTNAME="${TS_HOSTNAME:-defendableos-api-$(hostname)}"
tailscale --socket=/var/run/tailscale/tailscaled.sock up \
  --authkey="${TS_AUTHKEY}" \
  --hostname="${HOSTNAME}" \
  --accept-routes \
  --accept-dns=false \
  --ssh=false

# Surface the tailnet IP for logging · helpful when grepping fly logs.
echo "[tailscale-start] joined tailnet as ${HOSTNAME}: $(tailscale --socket=/var/run/tailscale/tailscaled.sock ip -4 || echo unknown)"

# Export proxy env so httpx / requests / aiohttp pick up the tailnet route
# transparently. Append to /etc/environment so child processes inherit.
{
  echo "HTTP_PROXY=http://localhost:1055"
  echo "HTTPS_PROXY=http://localhost:1055"
  echo "ALL_PROXY=socks5://localhost:1055"
  echo "NO_PROXY=localhost,127.0.0.1,api.defendableos.com,*.fly.dev,*.upstash.io"
} >> /etc/environment || true

export HTTP_PROXY="http://localhost:1055"
export HTTPS_PROXY="http://localhost:1055"
export ALL_PROXY="socks5://localhost:1055"
export NO_PROXY="localhost,127.0.0.1,api.defendableos.com,*.fly.dev,*.upstash.io"

echo "[tailscale-start] proxy env exported · ready for sovereign model calls"
