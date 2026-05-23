# Claw Bakery · Doctrine + Operator Guide

> Every Claw Inspected Strengthens the Defense.
> Every failure becomes a pair.
> Every pair becomes Honey only after Tribunal.
> Every Honey release makes the bakery smarter.

Claw Bakery is the DefendableOS module that turns ClawCheck interactions
into structured evidence, validator-reviewed repair pairs, adversarial
benchmark cases, and hashed receipts — without allowing the platform to
certify or train itself blindly.

## Doctrine (non-negotiable)

```yaml
real_time_ingestion: allowed
real_time_candidate_pair_creation: allowed
real_time_hash_receipts: allowed
synthetic_case_generation: allowed_in_controlled_queue
automatic_positive_labeling: prohibited
automatic_training_on_raw_records: prohibited
tribunal_required_before_training_admission: true
validator_required_before_deed_eligibility: true
raw_evidence_is_immutable: true
training_requires_redaction_and_consent: true
holdout_contamination: prohibited
```

## What the platform may do

- Capture real-time ClawCheck intake records
- Store immutable raw evidence records
- Compute preliminary risk snapshots (code, NOT model)
- Create pair candidates (always PENDING by default)
- Generate synthetic benchmark and adversarial candidates (when ClawForge is enabled)
- Redact and classify eligible data
- Create SHA-256 receipts and dataset manifests
- Queue records for Validator / Tribunal review
- Create DRAFT dataset releases after approval

## What the platform must NOT do

- Automatically train or fine-tune a production model from raw user conversations
- Place private customer evidence into training datasets without explicit consent
- Treat model-generated answers as automatically approved Honey
- Alter original evidence after receipt creation
- Issue a Defendable Agent Deed automatically
- Expose private raw intake records publicly
- Place secrets, credentials, tokens, private documents, email addresses, addresses, or customer identifiers into a reusable training corpus

## Pipeline

```
Intake → Risk Snapshot → Validator → Tribunal → Pair Factory → Object Vault → Dataset Release → Specialist Agent
```

| Stage | What | Module |
|---|---|---|
| Intake | Conversational ClawCheck collection | `services/api/app/services/claw_swarm/intake_agent.py` |
| Risk Snapshot | Evidence-specific rule eval | `services/api/app/services/claw_swarm/risk.py` |
| Validator | Reviewer chain (admin) | reserved · admin auth |
| Tribunal | HONEY / JELLY / PROPOLIS | `services/api/app/services/claw_bakery/pair_factory.py` |
| Pair Factory | Tribunal-gated pair candidates | same |
| Object Vault | Immutable artifact + receipt store | `services/api/app/services/claw_bakery/bakery_storage.py` |
| Dataset Release | DRAFT manifests, never auto-APPROVED | `services/api/app/services/claw_bakery/dataset_release.py` |
| Specialist Agent | Trains only from approved releases | future |

## Tribunal labels

```yaml
PENDING:
  description: Awaiting validator + tribunal review.
  training_eligible: false

HONEY:
  description: Evidence-specific, safe, accurate, structurally complete output.
  training_eligible: only_after_consent_and_redaction

JELLY:
  description: Useful but incomplete, generic, unsupported, or missing controls.
  training_eligible: false_until_repaired

JELLY_REPAIRED_TO_HONEY:
  description: Validated repair pair preserving raw error and approved target.
  training_eligible: only_after_consent_and_redaction

PROPOLIS:
  description: Material unsafe behavior · adversarial-eval lane only.
  training_eligible_as_positive: false

QUARANTINED:
  description: Sensitive, ambiguous, unconsented, or policy-blocked.
  training_eligible: false
```

## Risk rules (evidence-specific · v2 · grounded)

| rule_id | tier | trigger summary |
|---|---|---|
| `ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE` | ELEVATED | customer / business data + memory + comms + approval boundaries intact |
| `HIGH_FINANCIAL_AUTONOMOUS_ACTION` | HIGH | Payments authority + autonomous outbound action (RefundRanger-class) |
| `HIGH_PRIVILEGED_OPERATIONS_COMPROMISE` | HIGH | sudo shell + untrusted channel + creds / infra / code authority (RootClaw-class) |

Every rule cites only the evidence flags actually detected. Bug fixed
this session: the original v1 generic line `"Shell or Payments + outbound
messaging = autonomous-action exposure"` is gone · RootClaw findings no
longer mention Payments, RefundRanger findings no longer mention Shell.

## Storage layout

```
claw-bakery/
├── raw-evidence/{intakes,snapshots,validator-reviews}/
├── redacted/{approved-for-evaluation,approved-for-training}/
├── pair-candidates/{pending,honey,jelly,jelly-repaired,propolis-failures,quarantined}/
├── benchmark-packs/
├── holdouts/{sealed,manifests}/
├── dataset-releases/
├── receipts/{sha256,manifests,merkle-ready}/
├── deeds/{draft,eligible,issued,denied}/
└── events/
```

Two storage drivers:
- **`local`** (default) · plain filesystem rooted at `CLAW_BAKERY_LOCAL_ROOT`
- **`s3`** · S3-compatible (Tigris, R2, MinIO, AWS) via boto3 · uses the existing `s3_private_evidence_bucket`

Raw-evidence writes use `write_immutable` which refuses overwrite. Derived
redacted copies are SEPARATE artifacts under `redacted/`.

## Environment variables (Claw Bakery only)

```env
CLAW_BAKERY_STORAGE_DRIVER=local            # local | s3
CLAW_BAKERY_LOCAL_ROOT=./data/claw-bakery   # local driver root
CLAW_BAKERY_CLAWFORGE_ENABLED=false         # disabled by default
```

S3-driver credentials are read from the existing `s3_*` settings in
`services/api/app/core/config.py` · no new credential plumbing.

## Endpoints

```
POST /api/v1/agent-swarm/clawcheck/intake             (existing · now bakery-wired)
GET  /api/v1/agent-swarm/healthcheck                  (existing)

GET  /api/v1/claw-bakery/healthcheck                  (new)
GET  /api/v1/claw-bakery/public-metrics               (new · aggregate-only)
GET  /api/v1/claw-bakery/seeded-fixtures              (new · public demo data)
GET  /api/v1/claw-bakery/admin/pair-candidates        (reserved · 501 until auth)
POST /api/v1/claw-bakery/admin/pair-candidates/{id}/tribunal  (reserved)
POST /api/v1/claw-bakery/admin/clawforge/generate     (reserved)
GET  /api/v1/claw-bakery/admin/events                 (reserved)
```

## Pages

- `/claw-bakery` · public DefendableOS Claw Bakery page
- `/admin/claw-bakery` · admin readiness placeholder (auth gate required)

## Tests

```bash
# Backend (166 total · 25 bakery)
cd services/api && .venv/bin/pytest -q app/tests/test_claw_bakery.py

# Frontend
cd apps/web && npx tsc --noEmit && npm run build

# Refund agent pack
python3 -m pytest -q packs/refund_agent_v1/tests/    # 52 passing
```

## What is live now vs staged

| Capability | Status |
|---|---|
| Public `/claw-bakery` page | LIVE |
| `/admin/claw-bakery` placeholder | LIVE (no admin route gate yet) |
| ClawCheck intake → immutable raw store | LIVE |
| Snapshot computation (evidence-specific) | LIVE |
| PENDING pair candidate creation | LIVE |
| SHA-256 receipts | LIVE |
| Bakery event outbox | LIVE |
| Public metrics endpoint | LIVE |
| Seeded fixture endpoint | LIVE |
| ClawForge generation | DISABLED · controlled preview |
| Admin pair-candidate review routes | STAGED (501 until auth wired) |
| Synthetic Forge UI in admin | STAGED |
| `refund_agent_v1` pack loader wire-up in AgentGrade runner | STAGED |
| `business_agent_v1` per-task YAMLs | STAGED (manifest + catalogue only) |
| `coding_ops_agent_v1` per-task YAMLs | STAGED (manifest + catalogue only) |
| Dataset release APPROVED status | DRAFT only · APPROVED never auto |
