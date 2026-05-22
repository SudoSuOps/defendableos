# Deploy · DefendableOS API on Fly.io

This is the one-page deploy guide that takes the platform API from
local-only to **`https://api.defendableos.com`** in ~15 minutes for ~$5/mo.

## What you'll have when this is done

- `api.defendableos.com/healthz` returns the live integrations object
- `api.defendableos.com/api/v1/public/verify/ddeed-dov-compute-000001-v2` returns the seeded RTX PRO 6000 record
- `api.defendableos.com/api/v1/public/lookup?hash=…` resolves any of the four lookup kinds
- The ledger + showcase pages on `defendableos.com` stop showing "Platform unreachable" and start showing real data
- Total cost: ~$5-10/mo (smallest Fly VM + smallest Fly Postgres)

## Cost breakdown

| | Tier | Monthly |
|---|---|---|
| Fly Machine (shared-cpu-1x · 512 MB) | `shared-cpu-1x` | ~$1.94 + bandwidth |
| Fly Postgres (development cluster) | `development` | ~$1.94 |
| Outbound bandwidth | first 160 GB free | $0 (for the demo state) |
| **Total** | | **~$4-6/mo** |

Scale up by editing `fly.toml` — `shared-cpu-2x` is $7.79/mo, `performance-1x` is $15.50/mo.

## Prerequisites (one-time, ~5 min)

```bash
# Install flyctl (macOS / Linux)
curl -L https://fly.io/install.sh | sh
export FLYCTL_INSTALL="/home/$USER/.fly"
export PATH="$FLYCTL_INSTALL/bin:$PATH"

# Sign in
fly auth signup        # if you don't have an account
fly auth login         # if you already do
```

## Deploy · 5 commands (~10 min)

From the repo root:

```bash
cd services/api

# 1. Launch the app · don't deploy yet, just create
fly launch --no-deploy --copy-config --name defendableos-api

# 2. Create a managed Postgres cluster · pick "Development - single node"
fly postgres create --name defendableos-pg --region iad --vm-size shared-cpu-1x --volume-size 3

# 3. Attach the Postgres cluster (this sets DATABASE_URL automatically)
fly postgres attach --app defendableos-api defendableos-pg

# 4. Set the required secrets · use long random values for prod
fly secrets set \
  JWT_SECRET="$(openssl rand -hex 32)" \
  SESSION_SECRET="$(openssl rand -hex 32)" \
  EDGE_ENROLLMENT_SECRET="$(openssl rand -hex 32)" \
  --app defendableos-api

# 5. Deploy · uses Dockerfile · runs migrations + seed via release.sh on boot
fly deploy --app defendableos-api --remote-only
```

When deploy lands you'll see:
```
==> Monitoring deployment
1 desired, 1 placed, 1 healthy, 0 unhealthy [health checks: 1 passing]
--> v0 deployed successfully
```

## Verify the deploy

```bash
# 1. Healthcheck
curl https://defendableos-api.fly.dev/healthz | jq .

# 2. Seeded deed should resolve
curl https://defendableos-api.fly.dev/api/v1/public/verify/ddeed-dov-compute-000001-v2 | jq .lifecycle

# 3. Ledger lookup
curl "https://defendableos-api.fly.dev/api/v1/public/lookup?hash=DDEED-DOV-COMPUTE-000001-v2" | jq .kind
```

## Point `api.defendableos.com` at Fly

The DNS record already exists in Cloudflare (`api.defendableos.com` CNAME → `defendable.pages.dev`). Two changes:

### A · Cloudflare DNS

1. Cloudflare → DNS → Records → edit `api.defendableos.com`
2. Change **Content** from `defendable.pages.dev` to `defendableos-api.fly.dev`
3. Keep **Proxy status: Proxied**
4. Save

### B · Cloudflare Pages → remove the api custom domain

Workers & Pages → defendable project → Custom domains → click `api.defendableos.com` → **Remove custom domain**.

This is required because CF Pages claims the DNS until you release it.

### C · Fly · attach the custom domain

```bash
fly certs add api.defendableos.com --app defendableos-api
```

Within ~60 seconds:
```bash
fly certs list --app defendableos-api
# Shows: api.defendableos.com  · status: Ready · cert issued
```

### D · Verify production URL

```bash
curl https://api.defendableos.com/healthz
# {"status": "ok", "service": "defendableos-api", ...}
```

The ledger + showcase pages on defendableos.com will now resolve live.

## Optional · add the model + research API keys

To turn on Brave / Kimi / OpenAI in production:

```bash
fly secrets set \
  BRAVE_API_KEY="…" \
  MOONSHOT_API_KEY="…" \
  OPENAI_API_KEY="…" \
  --app defendableos-api
```

Fly does a rolling restart automatically. New secrets land in <30 sec.

## Watch logs

```bash
fly logs --app defendableos-api
```

## Scale up later

```bash
# More CPU / RAM
fly scale vm shared-cpu-2x --memory 1024 --app defendableos-api

# More machines (for HA · spreads across regions)
fly scale count 2 --app defendableos-api
fly scale count 2 --region lhr --app defendableos-api    # add a London replica
```

## Migration to sovereign compute (later)

When you're ready to host on a swarmrail or Honey Box:

1. On the host: `cloudflared tunnel create defendableos-api`
2. `cloudflared tunnel route dns defendableos-api api.defendableos.com`
3. Run docker-compose (the same `infrastructure/docker-compose.yml` from this repo)
4. In Cloudflare DNS: change `api.defendableos.com` CNAME to the Tunnel hostname
5. `fly apps destroy defendableos-api`

Total downtime: ~30 sec during DNS propagation. Zero code changes.

## Rollback

```bash
fly releases --app defendableos-api          # list deploys
fly releases rollback v<N> --app defendableos-api
```
