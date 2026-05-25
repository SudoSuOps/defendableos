# Command Examples · v0.1

> The smash RTX 5090 post-rental cycle expressed as the CLI invocations
> that v0.2 will execute. v0.1 ships these as a script-by-hand reference.

## Full rental_readiness flow (smash example)

```bash
# 1. Intake — name the run, name the baseline
defendable-compute intake \
  --use-case rental_readiness \
  --asset-id smash-rtx5090-host-001 \
  --operator-name claude-code-swarm-research-intake \
  --operator-role audit_agent \
  --platform vast_ai \
  --power-cap-w 550 \
  --thermal-warning-c 80 \
  --thermal-shutdown-c 90 \
  --privacy redacted

# Output: receipts/DCPR-20260525-{ULID}/intake.json + receipt.json stub

# 2. Observe — read-only sweep of identity + service state
defendable-compute observe --receipt-id DCPR-20260525-{ULID}

# Output: receipts/DCPR-20260525-{ULID}/evidence/*.txt|csv
#         receipt.json populated with asset_identity + precheck_state + findings
# Expected finding for smash: GPU_MEMORY_HELD_BY_LOCAL_PROCESS

# 3. Generate remediation plan (no execution)
defendable-compute remediate-plan --receipt-id DCPR-20260525-{ULID}

# Output: receipts/DCPR-20260525-{ULID}/remediation_plan.md
# Plan lists: SIGTERM vllm PID, SIGTERM llama.cpp PID, SIGTERM router PID

# 4. Execute remediation (per-finding, operator-confirmed)
defendable-compute remediate \
  --receipt-id DCPR-20260525-{ULID} \
  --finding GPU_MEMORY_HELD_BY_LOCAL_PROCESS \
  --confirm

# 5. Re-observe — fills post_remediation_state
defendable-compute observe \
  --receipt-id DCPR-20260525-{ULID} \
  --phase post_remediation

# 6. Trigger platform-remote validation
defendable-compute validate \
  --receipt-id DCPR-20260525-{ULID} \
  --platform vast_ai

# Output: receipts/DCPR-20260525-{ULID}/evidence/{ts}_platform_remote_validation.txt
#         benchmark_validation_results[] populated

# 7. Finalize the receipt (Tribunal gate + linter + hashes)
defendable-compute receipt \
  --receipt-id DCPR-20260525-{ULID} \
  --format both

# Output: receipts/DCPR-20260525-{ULID}/receipt.json
#         receipts/DCPR-20260525-{ULID}/receipt.md
#         receipts/DCPR-20260525-{ULID}/manifest.json
#         receipts/DCPR-20260525-{ULID}/SHA256SUMS.txt
```

## Resale flow

```bash
defendable-compute intake \
  --use-case resale_readiness \
  --asset-id seller-fleet-rig-04 \
  --operator-name seller-fleet-ops \
  --operator-role broker \
  --platform none \
  --power-cap-w 600 \
  --thermal-warning-c 78 \
  --thermal-shutdown-c 88

defendable-compute observe --receipt-id DCPR-...
defendable-compute remediate-plan --receipt-id DCPR-...
# operator reviews plan, runs remediate with --confirm per finding

# For resale: minimum required tests include thermal_response ≥ 5 min
# v0.1 platform_remote (vast.ai validator) does not cover this;
# requires a third_party adapter (out of v0.1 scope)
defendable-compute validate --receipt-id DCPR-... --platform none \
  --include-test thermal_response --duration 300
defendable-compute receipt --receipt-id DCPR-... --format both
```

## Disposition / ITAD intake flow

```bash
defendable-compute intake \
  --use-case disposition_intake \
  --asset-id itad-batch-2026-Q2-rig-018 \
  --operator-name itad-intake-agent \
  --operator-role itad_intake \
  --platform none

defendable-compute observe --receipt-id DCPR-...
# Minimum tests: runtime_visibility + ecc_health
# Stress tests optional
defendable-compute validate --receipt-id DCPR-... \
  --tests identity_check,runtime_visibility,ecc_health
defendable-compute receipt --receipt-id DCPR-... --format both
```

## Fleet audit flow (identity-only)

```bash
defendable-compute intake \
  --use-case fleet_audit \
  --asset-id fleet-host-007 \
  --operator-name fleet-audit-bot \
  --operator-role fleet_owner

defendable-compute observe --receipt-id DCPR-...
# No validate phase required for fleet_audit
defendable-compute receipt --receipt-id DCPR-... --format json
```

## Verifying a published receipt

```bash
# Pull a receipt + its evidence from the published ledger URL
mkdir -p /tmp/verify-DCPR-... && cd /tmp/verify-DCPR-...
wget -r {ledger_url}/receipt.json
# Then:
defendable-compute verify-hashes --receipt-id DCPR-...
echo "exit code: $?"  # 0 == valid, 4 == hash mismatch
```

## What the CLI will REFUSE to do (v0.1 contract)

```bash
# Refused — banned vocabulary in receipt
defendable-compute receipt --receipt-id DCPR-... \
  --inject 'tribunal_verdict.rationale="certified appraisal complete"'
# → exits 3 (banned vocabulary)

# Refused — touching rental platform service
defendable-compute remediate --receipt-id DCPR-... \
  --finding RENTAL_PLATFORM_SERVICE_DOWN --confirm
# → exits 1 (v0.1 does not auto-restart rental platform services)

# Refused — docker daemon restart in v0.1
defendable-compute remediate --receipt-id DCPR-... \
  --allow-docker-restart
# → exits 1 (flag not supported in v0.1)
```
