# DefendableOS Finality Lock · Open Gaps Register

> Honest log of what remains before the product is sealed end-to-end.
> All items here require operator action OR an external deploy trigger
> I cannot perform from inside this repo.

Last updated: 2026-05-23 · branch `feat/finality-lock-sprint`

---

## Priority 1 · Durable Bakery storage · OPEN

**State:** Production runs with `CLAW_BAKERY_STORAGE_DRIVER=<unset>` (defaults
to `local` = Fly ephemeral disk). All 5 required S3 secrets are NOT set on Fly.

```
S3_ENDPOINT_URL              · unset
S3_ACCESS_KEY_ID             · unset
S3_SECRET_ACCESS_KEY         · unset
S3_REGION                    · unset
S3_PRIVATE_EVIDENCE_BUCKET   · unset
```

**Why this matters:** bakery artifacts (intake records · sold-comps ·
ComputeClaw intakes · validator review sessions · receipts) are written to
Fly's ephemeral machine disk. They survive normal restarts but are LOST on
any redeploy that allocates a new machine.

**Operator action required:**

1. Provision an S3-compatible bucket (recommended: Fly's Tigris service or
   Cloudflare R2). Bucket should be PRIVATE.

2. Set the secrets:
```bash
flyctl secrets set \
  S3_ENDPOINT_URL="REPLACE_IN_TERMINAL_ONLY" \
  S3_ACCESS_KEY_ID="REPLACE_IN_TERMINAL_ONLY" \
  S3_SECRET_ACCESS_KEY="REPLACE_IN_TERMINAL_ONLY" \
  S3_REGION="auto" \
  S3_PRIVATE_EVIDENCE_BUCKET="defendableos-private-evidence-prod" \
  CLAW_BAKERY_STORAGE_DRIVER="s3" \
  --app defendableos-api
```

3. Verify after Fly restart:
```bash
curl -s https://api.defendableos.com/api/v1/claw-bakery/healthcheck \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('driver:',d['driver'])"
# Expected: driver: s3
```

4. Smoke a controlled write:
```bash
# Run a controlled ComputeClaw intake (NOT customer data)
curl -s -X POST https://api.defendableos.com/api/v1/compute-claw/intake \
  -H 'Content-Type: application/json' \
  -d '{ "asset_owner_attested": true, "asset_type": "GPU",
        "asset_category": "premium_agent_gpu",
        "manufacturer": "NVIDIA", "model_name": "RTX PRO 6000 Blackwell Workstation",
        "vram_gb": 96, "quantity": 1, "condition_claimed": "Controlled demo",
        "intended_outcome": "prepare_proof_of_value_package",
        "use_case": ["S3 persistence verification"],
        "evidence_supplied": {}, "operator_notes": "S3 smoke",
        "consent": {"store_for_review": true} }' | python3 -m json.tool
```

5. Verify the artifact persists across a `flyctl deploy`.

---

## Priority 2 · eBay production credential rotation · OPEN

**State:** Production keyset on Fly has:
```
EBAY_ENVIRONMENT             · production
EBAY_APP_ID                  · swarmbee-defendab-PRD-... (valid format)
EBAY_CERT_ID                 · placeholder text from a prior chat suggestion
EBAY_DEV_ID                  · valid UUID
EBAY_ADMIN_TOKEN             · set
EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN · set
EBAY_ACCOUNT_DELETION_NOTIFICATIONS_ENABLED · true
COMPUTECLAW_MARKET_OBSERVATION_ENABLED · set
```

Any live OAuth call returns clean HTTP 401 (the cert is invalid) → our
admin route maps to HTTP 502 with no secret leak. Safe state · NOT usable.

**Operator action required:**

1. Rotate the production Cert ID directly in the eBay Developer Portal
   (Application Keys → Production tab → Rotate (Reset) Cert ID).
   Both prior production Cert ID values were exposed in chat history.

2. Set the new value:
```bash
# Generate locally · paste only in this single command · clear shell history
flyctl secrets set EBAY_CERT_ID="REPLACE_IN_TERMINAL_ONLY" --app defendableos-api
```

3. Verify:
```bash
ADMIN_TOK=<your existing EBAY_ADMIN_TOKEN>
curl -s -X POST -H "X-Ebay-Admin-Token: $ADMIN_TOK" \
  https://api.defendableos.com/api/v1/admin/ebay/oauth/token-refresh \
  | python3 -m json.tool
# Expected: "refreshed": true · token_prefix: "v^1.1#..."
```

**Compliance note:** the Marketplace Account Deletion notification endpoint
uses a separate `EBAY_ACCOUNT_DELETION_VERIFICATION_TOKEN` · rotation of
the OAuth Cert ID does NOT affect the deletion endpoint. The deletion
endpoint must remain verified.

---

## Priority 3 · First production market-observation receipt · BLOCKED on 1 + 2

Cannot execute until Priority 1 (durable storage) and Priority 2 (working
Cert ID) are both resolved. Runbook is in
`docs/SOLD_COMP_PROD_ACTIVATION.md` · 7 steps · returns to this register
once a successful observation receipt is recorded.

---

## Priority 4 · First platform_admin · TOOL READY · OPEN

**State:** Admin JWT routes are wired (5 bakery + 4 ComputeClaw). Zero
platform_admin users exist in Postgres. No JWT can be issued until an
admin is created.

**Operator action required:**

```bash
# From inside the live Fly machine (interactive · getpass reads /dev/tty)
flyctl ssh console --app defendableos-api --command \
  'python scripts/create_platform_admin.py'

# Or locally against a dev DB:
cd services/api && .venv/bin/python scripts/create_platform_admin.py
```

The script:
- Refuses passwords < 16 chars
- Refuses to overwrite an existing user
- Reads password via `getpass.getpass` (no echo · no argv · no env var)
- Never logs the password or the generated JWT
- 11 unit tests for the validation paths

After the admin exists:
```bash
# Issue a JWT
curl -s -X POST https://api.defendableos.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "<admin-email>", "password": "<password>"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])"

# Use it on an admin route
curl -s -H "Authorization: Bearer <jwt>" \
  https://api.defendableos.com/api/v1/claw-bakery/admin/pair-candidates
```

---

## Priority 5 · Public frontend deployment · CONFIRMED FAILING

**State:** Verified via direct HTTP probes 2026-05-23 ~16:43 UTC.

| URL | HTTP | Title | Reality |
|---|---|---|---|
| `https://defendableos.com/` | 200 | `DefendableOS · Proof of Value` | Landing site home · OK |
| `https://defendableos.com/claw-bakery` | 200 | **`DefendableOS · Proof of Value`** | **WRONG · SPA-fallback to home** |
| `https://defendableos.com/compute-claw` | 200 | **`DefendableOS · Proof of Value`** | **WRONG · SPA-fallback to home** |
| `https://defendableos.com/defend-the-claw` | 200 | `Defend The Claw™ ...` | Landing site has this page · OK |
| `https://app.defendableos.com/claw-bakery` | 200 | `DefendableOS · Proof of Value` | **Body grep finds NONE of the actual page hero copy** ("Every claw inspected" · "HONEY" · "PROPOLIS" all absent) |
| `https://app.defendableos.com/compute-claw` | 200 | `DefendableOS · Proof of Value` | Same · body has none of the ComputeClaw hero copy |

**Diagnosis:** The Cloudflare Pages deployment for `app.defendableos.com` is
serving stale content (or wrong build output). The pages I built and tested
locally + committed to `main` are NOT in the live build.

**Operator action required:**

1. Identify the Cloudflare Pages project that serves `app.defendableos.com`.
2. Verify the build config points to `apps/web/.next` as the output directory.
3. Trigger a redeploy from the latest commit on `main`.

Alternative: if `apps/web` is supposed to be deployed via a different
mechanism (Fly Machines · Vercel · self-hosted) · point me at the deploy
target and I can wire it.

**Also: the landing repo problem.** The `https://defendableos.com/claw-bakery`
and `/compute-claw` URLs need to exist on the LANDING site (different repo
at `~/Desktop/defendable`) · either as marketing pages or as 301 redirects
to the platform portal. Right now the landing site SPA-falls-back to its
home page on unknown paths · which silently hides the issue.

---

## Priority 6 · SEO/GEO for the new product pages · PARTIAL

**Completed in this sprint (apps/web):**
- `/claw-bakery` and `/compute-claw` pages now have:
  - canonical URLs pointing to `https://defendableos.com/{path}`
  - OpenGraph tags (title · description · url · siteName · type)
  - Twitter card tags
  - robots: index/follow allowed
  - Truthful descriptions (no "all 6 agents live" claims)

**Cannot complete from this repo:**
- Adding `/claw-bakery` and `/compute-claw` to the LANDING repo's
  `sitemap.xml`
- Adding entries to the landing repo's `llms.txt`
- Adding header/footer nav links from the landing site to these pages
- These are SEPARATE-REPO changes for `defendable/` at `~/Desktop/defendable`

**Operator action required (landing repo):**
Open the `defendable` landing repo and add the new pages to its SEO surface
the same way `/defend-the-claw` was added. The canonical URLs in this
repo's metadata already point to `defendableos.com` · they're ready to be
served from there once the landing repo catches up.

---

## Priority 7 · Truthful role status · COMPLETE in code

**Verified:** the `roles_summary()` function returns:
```json
{
  "intake":      { "status": "LIVE" },
  "inspector":   { "status": "SCAFFOLDED" },
  "benchmarker": { "status": "SCAFFOLDED" },
  "tribunal":    { "status": "SCAFFOLDED" },
  "validator":   { "status": "SCAFFOLDED" },
  "deedmaker":   { "status": "SCAFFOLDED" }
}
```

**Verified:** no source-grep hit for any claim like "6 agents live" /
"all kimi agents live" in `services/api/` or `apps/web/` (the only
match was a node_modules false positive in `@types/node/http.d.ts`).

**Added this sprint:**
- `apps/web/components/bakery/RoleStatusTable.tsx` · 4-column table that
  visibly distinguishes Kimi-agent status vs deterministic-platform-code
  status per role
- Rendered on `/claw-bakery` as a new section
- Operators reading the page will see "1 of 6 Kimi agents currently calls
  a live model" directly · no inference required

---

## NOT touched in this sprint (correctly · per spec)

- ClawForge: stays disabled
- Bulk synthetic pair generation: NOT done
- Agent training / fine-tuning: NOT done
- Deed issuance: NEVER automated
- Additional claw roles: NOT built
- Sold-comp claims: NEVER claimed without verified data
- Affiliate monetization: NOT touched
- Marketplace deletion endpoint: NOT modified (still verified · still receiving real eBay POSTs)

---

## Net new test count this sprint

11 new tests (admin-creation script validation) · all passing · backend
total 289/289 · zero regression.
