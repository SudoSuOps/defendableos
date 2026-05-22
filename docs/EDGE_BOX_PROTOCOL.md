# Edge Box Protocol

The Defendable Box is the local capture appliance for DefendableOS. It hashes evidence locally, uploads it to the platform with the precomputed SHA-256, and the platform re-hashes on receipt. Hash mismatches are rejected and audited.

> *"Defendable Box · Local capture. Verified receipts. Sovereign evidence flow."*

## Trust boundary

An edge node is **not** a portal user. It cannot browse other organizations' data, cannot list assets, cannot run AIOV. Its identity is narrow:

| Edge node may | Edge node may not |
|---|---|
| Heartbeat | Browse the portal |
| Upload evidence to assets in its organization | List assets it has not been assigned |
| Upload benchmark JSON | Approve deeds or publish |
| Read its own ENS reservation | Read other organizations |

## Enrollment

1. ORG_ADMIN clicks **+ Enroll device** in `/portal/edge/enroll`
2. Backend creates an `EdgeEnrollmentToken`
   - Plaintext shown once
   - Stored as SHA-256
   - TTL default 30 minutes (`EDGE_TOKEN_TTL_MINUTES`)
3. Operator runs on the device:
   ```bash
   defendable-box enroll \
     --server https://platform.defendableos.com \
     --token <token> \
     --node-name box-01
   ```
4. Backend swaps the token for an `EdgeNode` row + long-lived `edge_token` JWT
5. Token row is marked `consumed_at` + linked to `consumed_by_node_id`
6. Credentials saved to `~/.defendable-box/credentials.json` with mode `0600`

## Heartbeat

```bash
defendable-box heartbeat
```

Sends `software_version` + optional hardware summary. Backend sets `last_heartbeat_at = now()`. A node that has not heartbeat'd in N minutes (cron job, future) flips to `STALE`.

## Evidence upload

```bash
defendable-box upload-evidence \
  --asset-id <uuid> \
  --type BENCHMARK_OUTPUT \
  --file ./benchmark.json
```

Agent behaviour:
1. SHA-256 the file locally (streamed)
2. POST multipart to `/api/v1/edge/assets/{asset_id}/evidence`:
   - `file=<bytes>`
   - `evidence_type=BENCHMARK_OUTPUT`
   - `claimed_sha256=<hex>`
3. Backend re-hashes the received bytes
4. If `claimed_sha256 != server_sha256` → reject with HTTP 400, audit a `EVIDENCE_UPLOAD_HASH_MISMATCH` event
5. If match (or no claim) → persist evidence with `provenance="EDGE_CAPTURED"`, regenerate manifest, audit success

## Hash mismatch handling

- The backend's hash is authoritative
- `EdgeUploadEvent.hash_match` is recorded (true / false / null)
- Mismatches **never** populate an EvidenceItem · they are rejected at the boundary
- The mismatch event itself is preserved for forensic review

## Revocation

ORG_ADMIN can mark a node `REVOKED`. The `get_current_edge_node` dependency checks status and returns HTTP 403 on revoked tokens.

## Local credential security

- File path: `~/.defendable-box/credentials.json`
- File mode: `0o600`
- Contains: `server`, `node_id`, `node_name`, `edge_token`
- Excluded from git via `.gitignore`

## Future: local inference

The Defendable Box is sized for local LLM-class inference (Jetson Orin Nano Super / Bee Box). Future versions may:
- Run a local `EDGE_EVIDENCE_CLASSIFICATION` model to pre-classify uploads
- Produce a benchmark receipt with model + driver fingerprint
- Operate in offline mode with deferred sync (signed evidence queue)

These are deliberately out of the MVP scope. Evidence capture + verified hashing is the core trust contract.
