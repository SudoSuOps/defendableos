# Evidence Vault · Object Storage Doctrine

> The vault stores the evidence.
> The hash protects the trail.
> The validator judges the claim.
> The Deed publishes only what survives review.

This doc is the **public-doctrine companion** to
[`OBJECT_STORAGE_POLICY.md`](./OBJECT_STORAGE_POLICY.md), which
covers the implementation specifics (bucket names · key layouts ·
env var toggles · provider matrix). This doc covers the **why**,
the **boundaries**, and the **public claim discipline**.

## 1. Purpose of the Evidence Vault

DefendableOS is not merely generating opinions. Every issued record
points back to the source files, captures, receipts, observations,
validator corrections, manifests and approved exports that make the
opinion inspectable and defensible.

The **Evidence Vault** is the public-doctrine name for the
controlled storage architecture that preserves those artifacts. It
exists so that:

- A buyer of a Defendable Deed can see what evidence supported it
- A validator can re-open the record and check the claim against the
  preserved source trail
- An operator can later supply additional evidence to upgrade a
  record without re-uploading the prior trail
- A partner can ingest evidence under documented rights without the
  platform losing track of what's private vs. derived vs. public-safe

## 2. Why object storage is relevant to DefendableOS

Object storage is the technical foundation underneath the Evidence
Vault. The platform uses an S3-compatible object store (MinIO in
local dev · Tigris on Fly production) because:

- **Durable, addressable storage** for the raw bytes that hashes are
  computed against
- **Per-bucket privacy boundaries** that compose with the
  service-layer guard
- **Provider neutrality** · `boto3` speaks the same protocol to
  MinIO, Tigris, AWS S3 · provider can be swapped without code changes
- **Audit-friendly key layouts** · every key includes the organization,
  asset, evidence-id, manifest version, deed version

The current implementation status:

- 4-bucket vault model · **implemented** (see `app/services/artifacts.py`)
- SHA-256 over arriving bytes · **implemented** (`app/services/hashing.py`)
- Manifest regeneration on every evidence upload · **implemented**
  (`app/services/manifest.py`)
- Upload endpoint with content-type whitelist + 50 MB ceiling ·
  **implemented** (`app/api/v1/evidence.py`)
- 4-bucket privacy enforcement at service boundary · **implemented**
  with test coverage (`tests/test_goods_doctrine.py`)
- Live object-storage mirror · **gated** by `OBJECT_STORAGE_LIVE_ENABLED`
  · defaults `False` so tests and local dev never make surprise
  network PUTs · operator flips per-environment

## 3. The four vault classes

The vault is divided into 4 logically separated classes. Each class
is implemented as both a database `ArtifactPrivacyClass` enum value
AND a distinct bucket. The bucket boundary is defense-in-depth;
the **service-boundary guard is the doctrine**.

| Vault Class | What it contains | Public reachable? |
|---|---|---|
| **Private Evidence Vault** (`PRIVATE_EVIDENCE`) | Client uploads · founder ownership proofs · invoices · serials · raw photos · validator commentary | **Never** |
| **Observation Vault** (`MARKET_OBSERVATIONS`) | Brave grounding snapshots · eBay listing observations · Vast.ai rate snapshots · partner-provided records under research-only rights | Internal only |
| **Derived Intelligence Vault** (`DERIVED_DATASETS`) | Comp sets · opportunity scores · AIOV drafts · Pair Factory candidates · validator receipts · SHA256SUMS manifests | Internal until approved |
| **Public-Safe Export Vault** (`PUBLIC_ASSETS`) | Issued deed manifests · approved summaries · privacy-filtered verify-page payloads · approved MarketReady media | **Only after validation** |

See [`OBJECT_STORAGE_POLICY.md`](./OBJECT_STORAGE_POLICY.md) for the
concrete bucket name conventions and the per-class key layouts.

## 4. Object naming, versioning, and hash receipt conventions

Each write produces three artifacts the platform can later inspect:

1. **The bytes** at a deterministic key (see Object Key Layout
   in `OBJECT_STORAGE_POLICY.md`)
2. **The SHA-256 receipt** stored on the `evidence_items.sha256_hash`
   row alongside the storage key
3. **The manifest** regenerated on every upload · a SHA-256 over the
   sorted-key compact JSON of all current evidence items for the asset

Versioning is per-manifest (`manifest_v1.json` · `manifest_v2.json` ·
etc.) so the chain of evidence states is preserved · NOT overwritten.

Hash properties:

- SHA-256, computed on the raw bytes as received
- Stored on the database row at upload time (single transaction)
- Used downstream to verify that a fetched artifact matches the
  captured receipt
- Embedded by reference in deed JSON (`record_hash`,
  `manifest_sha256`, `validator_receipt`) so a verify page can cite
  the integrity chain without re-fetching the bytes

## 5. Access-control expectations

- **Service-boundary guard first.** Every write goes through
  `artifacts.put_artifact()` which sets the privacy class. Every
  public export goes through `public_export_or_refuse()` which raises
  `PermissionError` on anything not classed `PUBLIC_ASSETS`. The guard
  has **no exception path**.
- **Bucket boundary as defense-in-depth.** Private buckets are never
  fronted by a public URL. Even if the application guard were
  bypassed, the bucket policy prevents public reads.
- **No bucket is public until the privacy-filter audit passes.** This
  is the operating rule in `OBJECT_STORAGE_POLICY.md`.
- **Presigned URLs are short-lived.** `S3_PRESIGNED_URL_TTL_SECONDS`
  defaults to 900 seconds (15 minutes).
- **Operators see their own evidence.** Reads of `PRIVATE_EVIDENCE`
  go through authenticated admin paths that enforce org ownership.

## 6. Public / private disclosure rules

| What | May be public | Conditions |
|---|---|---|
| Raw uploaded bytes | No | Never published by default; only via approved derived export |
| Serial numbers | No | Identity match happens internally; public records show model + form factor only |
| Invoices / receipts | No | Operator can opt to redact-and-include a derived summary |
| Vast.ai listing snapshots | Citable | Source URL + timestamp may appear in public deed text; the raw response stays in Observation Vault |
| Operator rental receipts | Derived only | Aggregate gross/window may appear in approved derived form; raw line items stay private |
| AIOV draft narrative | No | Drafts stay in Derived Intelligence Vault until validator review |
| Validator receipt SHA-256 | Yes | Hash citation only · no validator commentary published |
| Final deed JSON | Yes | After passing `filter_public_payload()` |
| Hashes (record_hash, manifest_sha256) | Yes | Identifies the version that was issued |

## 7. Record lifecycle relationship

The vault state tracks the deed lifecycle 1:1:

| Deed lifecycle state | What's in the vault |
|---|---|
| `DRAFT_REVIEW_RECORD` | Evidence in PRIVATE · observations in OBSERVATION · AIOV draft in DERIVED · NOTHING in PUBLIC |
| `PASSED_FOR_DRAFT_PACKAGING` | Validator receipt added to DERIVED · still nothing PUBLIC |
| `READY_FOR_ISSUANCE` | Deed JSON drafted in DERIVED · privacy-filter pending · still nothing PUBLIC |
| `ISSUED` | Privacy-filtered deed JSON written to PUBLIC vault at `verify/{slug}/deed-public.json` |
| `WITHDRAWN` | PUBLIC artifact removed · all other vault artifacts retained for audit |

The vault retains the full history. The public surface reflects only
the currently-issued state.

## 8. Pair Factory relationship

Pair Factory operates on artifacts already in the vault. It does NOT
re-ingest from external sources during pair generation:

- **Inputs:** `MarketObservation` rows reference `ObservationVault`
  artifacts · `EvidenceItem` rows reference `PrivateEvidenceVault`
  artifacts
- **Outputs:** Generated `TrainingPair` rows reference both the source
  artifact AND the corrected output · the pair JSONL is written to
  `DERIVED_DATASETS` under `pairs/{goods_class}/{batch_id}/candidates.jsonl`
- **Rights flow-through:** A pair inherits the most restrictive rights
  status of any artifact it cites · cannot be more permissive than its
  least-permissive input
- **Approval:** No pair becomes training-eligible without all four
  conditions (`use_class=TRAINING_ELIGIBLE` ·
  `training_eligible=True` · `source_rights_status=TRAINING_ALLOWED` ·
  `validator_status=PASSED`). `approve_batch_for_training()` is
  intentionally `NotImplementedError` today · the seam exists, the
  gate is shut

## 9. Compute examples

### RTX PRO 6000 Blackwell flagship record · DDEED-DOV-COMPUTE-000001-v3

| Artifact | Vault Class | What it supports |
|---|---|---|
| Purchase receipt / ownership proof | PRIVATE | Ownership/acquisition evidence |
| Serial-number photograph | PRIVATE | Identity matching (never public raw) |
| `nvidia-smi` operating snapshot | PRIVATE → DERIVED | Operating state at capture time |
| Brave market grounding snapshot | OBSERVATION | Public market context citation |
| AIOV draft narrative | DERIVED | Draft opinion · validator-gated |
| Validator 12-check receipt | DERIVED | Approval trail |
| Final deed JSON (privacy-filtered) | PUBLIC | `verify/ddeed-dov-compute-000001-v3/deed-public.json` |

### RTX 3090 workhorse utilization record (PROPOSED · DDEED-DOV-COMPUTE-3090-WORKHORSE-001-v1)

| Artifact | Vault Class | Public disclosure |
|---|---|---|
| Purchase receipt | PRIVATE | Never public by default |
| Serial photograph | PRIVATE | Identity match only |
| `nvidia-smi` snapshot | PRIVATE → DERIVED | Redacted summary only if approved |
| Vast.ai public listed-rate snapshot | OBSERVATION | May show as observation, not paid yield |
| Founder rental payout receipt | PRIVATE | Approved derived summary only |
| AIOV hold/rent/sell analysis | DERIVED | Internal until reviewed |
| Validator-approved deed manifest | PUBLIC | Public if issued |

Doctrine: *Listed is not rented. Rented is not guaranteed future
yield. Stored is not automatically proven. Public is only what
survived validation.*

### Jetson edge utility record (EVIDENCE_RICH · sigedge)

| Artifact | Vault Class | Why it matters |
|---|---|---|
| Device identity + reference spec | OBSERVATION | Expected hardware capability |
| Runtime + power-mode snapshot | PRIVATE | Configuration at capture time |
| Captured local workload test JSON | PRIVATE → DERIVED | Demonstrated utility when reviewed |
| Deployment purpose statement | DERIVED | Intended role · not proven performance |
| Validator-approved Edge Utility Record | PUBLIC | Approved demonstrated utility |

Doctrine: *Affordable compute becomes defendable compute when its
actual role and tested utility are preserved as evidence.*

### Complete producing node / fleet record (PROPOSED_PROOF_CASE)

| Artifact | Vault Class |
|---|---|
| Per-component spec + serial | PRIVATE |
| Network + storage configuration | PRIVATE → DERIVED |
| Operational uptime + workload-class evidence | DERIVED |
| Per-tier score breakdown (E5-E7) | DERIVED |
| Complete-node deed + buyer booklet | PUBLIC if issued |

## 10. Rights and training/evaluation restrictions

The vault classification gates downstream rights. The `RightsStatus`
enum on every artifact and observation determines what may happen:

| RightsStatus | What's permitted |
|---|---|
| `TERMS_REVIEW_PENDING` | Hold-only · no analysis · no derivation |
| `INTERNAL_RESEARCH_ONLY` (default) | Internal analysis · no training · no public republish |
| `EVAL_DERIVATIVE_ALLOWED` | Eval pack generation · no training |
| `TRAINING_ALLOWED` | Training pair eligibility (still subject to 4-condition gate) |
| `PUBLIC_DISPLAY_ALLOWED` | Validator-reviewed public surfaces |
| `RESTRICTED_DO_NOT_EXPORT` | Internal reference · refuses derivation |
| `AGREEMENT_REQUIRED` | ITAD / licensed sources · pre-pilot lock |

Where evidence rights and disclosure controls permit, validated
outcomes and corrections can become reusable intelligence for
improving future analysis and record quality. The platform does NOT
ingest data into training material automatically.

## 11. What object storage does NOT prove

Object storage:

- **Does** preserve artifacts at addressable keys
- **Does** support SHA-256 receipts that verify a fetched artifact
  matches what was captured
- **Does** separate private evidence from public-safe records
- **Does** maintain version history of manifests and deeds

Object storage **does not**:

- Make evidence true (validation does)
- Make a claim defensible (the validator + the source class do)
- Certify an asset (no party in the chain issues certifications)
- Guarantee tamper-proofing beyond what the bucket + hash chain offer
- Replace appraisal, inspection, or licensed professional review

> A stored file is not automatically a proven claim. Evidence must
> still be classified, challenged and approved before it supports a
> public record.

## 12. Future connection to Defendable Deeds and verification routes

Today the chain is:

```
upload → SHA-256 → manifest regen → AIOV draft → validator review
       → privacy-filter → deed JSON → PUBLIC vault
       → /api/v1/public/verify/{slug} → /verify/{slug} on defendableos.com
       → ledger.defendableos.com hash lookup
```

Forthcoming (documented · not implemented this turn):

- **Per-deed evidence summary endpoint** · returns the vault-class
  breakdown for a published deed without exposing private contents
- **Operator self-service evidence portal** · upload progress · per-
  artifact rights state · per-artifact public/private flag
- **ENS attestation** · publish `record_hash` to
  `<slug>.defendable.eth` for cross-platform integrity verification

## Related docs

- [`OBJECT_STORAGE_POLICY.md`](./OBJECT_STORAGE_POLICY.md) · technical
  implementation, bucket names, key layouts, env vars
- [`GOODS_INTELLIGENCE_ARCHITECTURE.md`](./GOODS_INTELLIGENCE_ARCHITECTURE.md)
  · the 5-layer architecture this vault sits inside
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) · platform-wide reference
- [`COMPUTE_BEACHHEAD_30_DAY_PLAN.md`](./COMPUTE_BEACHHEAD_30_DAY_PLAN.md)
  · the first revenue lane the vault supports
- [`VAST_AI_UTILIZATION_SIGNAL_RAIL.md`](./VAST_AI_UTILIZATION_SIGNAL_RAIL.md)
  · how Vast.ai signals enter the OBSERVATION vault
- [`EDGE_AI_COMPUTE_LANE.md`](./EDGE_AI_COMPUTE_LANE.md) · how Edge
  Utility Records use the vault
