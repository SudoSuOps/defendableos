# Security Model

DefendableOS is an evidence platform. The security model is built around three commitments:

1. **Private by default.** Uploaded evidence is private until an explicit publication action.
2. **Receipts everywhere.** SHA-256 on every uploaded object, deterministic JSON hashing on manifests / deeds / validator receipts.
3. **No silent destruction.** Deed and analysis records use `SUPERSEDED` instead of delete.

## Trust boundaries

| Boundary | Trusts | Distrusts |
|---|---|---|
| Browser | Server JWT-signed token | Nothing else; all keys server-side |
| Portal user (`USER`) | The user's own organization data | Other organizations |
| Edge node (`EDGE_NODE`) | Its enrolled organization, narrow upload paths | Browsing portal data |
| Platform admin | Cross-org review actions | Live ENS issuance without explicit opt-in |
| Public verifier | Nothing more than published `deed-public.json` | Any private evidence |

## Authentication

- Portal sessions: HS256 JWT with `JWT_SECRET`. Token in `Authorization: Bearer …`.
- Edge tokens: HS256 JWT signed by a separate `EDGE_ENROLLMENT_SECRET`, long-lived but revocable by setting node status to `REVOKED`.
- Enrollment tokens: one-time, hashed (SHA-256) in storage, TTL configurable (`EDGE_TOKEN_TTL_MINUTES`).
- Passwords: bcrypt via passlib.

## Tenant isolation

Every privileged route resolves `organization_id` from the current membership. Database queries on private state always filter by `organization_id`. The edge upload route additionally checks `asset.organization_id == edge_node.organization_id`.

## File-upload constraints

- `EvidenceItem` enforces:
  - Content-type allowlist (PDF, JSON, CSV, TXT, PNG, JPEG, WEBP, octet-stream)
  - Maximum bytes (default 50 MiB; configurable)
  - SHA-256 calculated server-side; the client-claimed hash is recorded but verified
- Storage keys are sanitised against path-traversal (`services/storage.py:safe_storage_key`).

## Privacy filter

`services/deed.py:filter_public_payload` strips known sensitive fields when serving the public verification record:
- `asset.serial_number`, `asset.private_serial_number`, `asset.purchase_cost_private`
- `evidence_packet.private_filenames`
- `aiov_analysis.narrative`, `aiov_analysis.private_notes`
- Anything in `evidence_packet` not on the explicit allow-list

`tests/test_deed_privacy.py` is the canary for this filter.

## ENS live-write safety

- `ENS_MODE=mock` (default) never touches a chain or signer key.
- `ENS_LIVE_WRITES_ENABLED=false` (default) blocks even configured adapters from issuing.
- `ENS_SIGNER_PRIVATE_KEY` is never returned in any API response, never logged, never surfaced in the UI.

## Threats and mitigations

| Threat | Mitigation |
|---|---|
| Malicious file upload | Content-type allowlist · size cap · server-side hashing · no public exposure of raw files |
| Cross-tenant data exposure | All private queries filter by `organization_id`; edge-node uploads recheck ownership |
| Unsupported AI conclusions | AIOV `value_opinion.display_status` is `WITHHELD_PENDING_VALIDATOR_REVIEW` by default; validator runs deterministic checks before any range can be published |
| Forged edge evidence | Backend re-hashes the upload; mismatches are rejected (HTTP 400) and audited |
| Mistaken public exposure of private evidence | `filter_public_payload` + dedicated tests · privacy is enforced in code, not by hope |
| Compromised ENS signer key | Mock-by-default · live writes double-gated · signer never returned in any API |
| Public market source misclassification | `evidence_classification` defaults to `UNKNOWN`; validator flags any source left UNKNOWN; listings can never be relabelled as confirmed sales |
| Hallucinated confirmed sale data | Validator rule 6 explicitly checks listing-vs-confirmed presentation |
| Stale public market results | Every public source captures `retrieved_at`; validator rule 4 fails if a source has no timestamp |
| Secret leakage | `.gitignore` excludes `.env*`, `*.pem`, `*.key`, `secrets/`, `~/.defendable-box/` |
