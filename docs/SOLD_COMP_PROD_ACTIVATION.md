# Sold-Comp Tribunal · Production Activation Playbook

> Single-page runbook for flipping Compute Market Watch's sold-comp evidence
> rail from sandbox (empty compute catalog) to production (real RTX 3090 /
> 4090 / PRO 6000 / H100 / A100 sold comps from the full eBay catalog).

## State today (2026-05-23)

- **Code:** complete · `services/api/app/services/compute_market_watch/` ·
  shipped on `main` at commit `59b8b5f`
- **Tests:** 14/14 green · pack + tribunal + ingest covered
- **Sandbox:** verified end-to-end · 0 RTX 3090 results (expected · sandbox
  has no compute test catalog)
- **Production blocker:** `EBAY_CERT_ID` on Fly is currently the placeholder
  text `<rotated PRD cert id from portal>` · not a real cert. The OAuth call
  cleanly returns HTTP 401 · our code maps to HTTP 502 · no leak. Safe
  state but not usable for live comps.
- **OAuth scope:** `buy.marketplace.insights` already granted on this app
  (verified during sandbox smoke 2026-05-23)

## Activation · operator commands

### Step 1 · rotate the production Cert ID in eBay portal

1. Open https://developer.ebay.com · sign in
2. **Application Keys** page · **Production** tab
3. Find the `defendable` keyset (App ID starts with `swarmbee-defendab-PRD-`)
4. Click **Rotate (Reset) Cert ID**
5. Copy the new value from the portal (starts with `PRD-`)

### Step 2 · push the rotated cert to Fly

```bash
# Generate locally first so no clipboard contamination is possible.
# Open the new cert in a GUI text editor (gedit), Ctrl+A · Ctrl+C, then:
PRD_CERT="<paste-the-rotated-cert-from-clipboard>"

flyctl secrets set EBAY_CERT_ID="$PRD_CERT" --app defendableos-api

unset PRD_CERT   # purge from shell history
```

Fly auto-restarts the machine. Wait ~30 seconds.

### Step 3 · verify production OAuth works

```bash
ADMIN_TOK=<your existing EBAY_ADMIN_TOKEN>
curl -s -X POST -H "X-Ebay-Admin-Token: $ADMIN_TOK" \
  https://api.defendableos.com/api/v1/admin/ebay/oauth/token-refresh \
  | python3 -m json.tool

# Expected: HTTP 200 · "refreshed": true · environment: "production" ·
# token_prefix: "v^1.1#..." · expires_in_seconds: ~7200
```

If this returns 502 with `EbayOAuthError`, the cert is still wrong · re-run Step 1+2.

### Step 4 · live Browse smoke against production catalog

```bash
curl -s -H "X-Ebay-Admin-Token: $ADMIN_TOK" \
  "https://api.defendableos.com/api/v1/admin/ebay/browse/search?q=RTX+3090&limit=3" \
  | python3 -m json.tool

# Expected: sample_size: 3 · real RTX 3090 listings from production eBay
```

### Step 5 · first sold-comp ingest (DRY-RUN · safe)

```bash
curl -s -X POST -H "X-Ebay-Admin-Token: $ADMIN_TOK" \
  "https://api.defendableos.com/api/v1/admin/ebay/sold-comps/ingest-compute?dry_run=true&limit_per_sku=10" \
  -H "Content-Type: application/json" \
  -d 'null' \
  | python3 -m json.tool

# Expected · per-SKU counts grouped by tribunal label:
#   · HONEY      · clean confirmed-sale evidence
#   · JELLY      · non-USD currency · price-band drift
#   · PROPOLIS   · zero price · sandbox markers · sanity-ceiling breach
#   · QUARANTINED · title doesn't match any known compute SKU
```

### Step 6 · LIVE ingest (writes immutable bakery artifacts)

```bash
curl -s -X POST -H "X-Ebay-Admin-Token: $ADMIN_TOK" \
  "https://api.defendableos.com/api/v1/admin/ebay/sold-comps/ingest-compute?dry_run=false&limit_per_sku=10" \
  -H "Content-Type: application/json" \
  -d 'null' \
  | python3 -m json.tool
```

### Step 7 · inspect what landed

```bash
flyctl ssh console --app defendableos-api --command \
  'sh -c "ls -1 /app/data/claw-bakery/compute-market-watch/sold-comps/honey/ 2>/dev/null | wc -l"'
```

## Default SKU list

When `sku_aliases` is omitted, the ingest runs against:
`RTX 3090` · `RTX 4090` · `RTX A6000` · `RTX 4500 Ada` ·
`RTX PRO 6000 Blackwell` · `NVIDIA H100` · `NVIDIA A100`

## What this unlocks

1. **ComputeClaw ValueComposer** can wire HONEY sold-comps into
   `market_observation_summary` for any matching AIOV draft
2. **Defendable Compute Deed evidence vault** gains a confirmed-sale comp
   class · the highest-grade `PERMISSIONED_CONNECTED_SALE` signal
3. **Per-SKU price-band tracking** · real time-series of confirmed
   transactions per GPU model
4. **Marketplace deletion compliance** stays unchanged · sold-comps are
   PUBLIC marketplace observations, NOT user-account-linked data

## What does NOT auto-happen

- No deed issued · `ValueComposer` always produces DRAFT
- No training data admission · still requires dataset-release + Validator review
- No scheduled job · operator-triggered until a cron is added

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `oauth/token-refresh` returns 502 | Cert ID still placeholder | Re-run Step 1+2 with actual rotated cert |
| Browse `total_reported: 0` | Sandbox env still active | Check `oauth/readiness` · should say `production` |
| Lots of QUARANTINED | Search too broad · matching non-compute | Pass narrower `sku_aliases` |
| Lots of PROPOLIS | Sandbox test catalog · NOT prod | Verify `EBAY_ENVIRONMENT=production` |
| Admin endpoint 401 | Missing/wrong `X-Ebay-Admin-Token` | Check Fly secret · regenerate if lost |
| Admin endpoint 503 | `EBAY_ADMIN_TOKEN` not set on Fly | `flyctl secrets set EBAY_ADMIN_TOKEN=...` |

## Doctrine reminders

- HONEY sold-comps are `PERMISSIONED_CONNECTED_SALE` class · highest signal grade
- PROPOLIS sold-comps preserved as adversarial evidence · NEVER positive comp
- Tribunal is pure code · no LLM · adding new SKU = add `ComputeSkuSpec` to `compute_skus.py`
- All artifacts immutable · sha256 receipts per artifact + per-run manifest
