# Vast.ai Readiness Lane · Integration · v0.1

> How Defendable Compute Proof Receipt v0.1 integrates with the existing
> Vast.ai rental workflow, anchored on the smash RTX 5090 post-rental cycle
> observed on 2026-05-25.

## What Vast.ai already provides

The platform supplies a remote validator that exercises:

- system requirements
- ResNet18 GPU functional check
- ECC memory check
- NCCL distributed test (scaled to host's GPU count)
- combined stress-ng + gpu-burn (default 60s)
- automatic test instance teardown

Result is a binary `DONE` (or failure detail) reported on the host's machine
status. The platform's validation output is a **`platform_remote`-class
evidence artifact** under our schema.

## What Defendable Compute Proof Receipt adds

| concern | Vast.ai today | DCPR v0.1 |
| --- | --- | --- |
| Host identity record | implicit (Vast host ID) | explicit `compute_asset_identity` JSON object with sha256-anchored evidence |
| Pre-validation contamination check | none documented | full `precheck_state` + `findings[]` |
| Remediation log | none | per-finding `remediation_actions[]` with operator confirmation receipts |
| Post-remediation baseline | implicit | explicit `post_remediation_state` |
| Stress test result archive | Vast-side log | sha256-hashed local + ledger-published copy |
| Receipt verifiability | platform-only | hash-chain anchored to DefendableLedger; any party can verify |
| Claim boundaries | none stated | explicit `claim_boundaries` block stating what receipt does + does NOT establish |

## How the receipt slots into the rental flow

```
Vast renter exits
     │
     ▼
defendable-compute intake --use-case rental_readiness
     │
     ▼
defendable-compute observe  ← Phase 1+2: identity + precheck
     │
     ▼
findings non-empty? ──── yes ──► remediate-plan → operator confirm → remediate → observe (post)
     │ no
     ▼
defendable-compute validate --platform vast_ai  ← Phase 6: invokes Vast remote validator
     │
     ▼
defendable-compute receipt  ← Tribunal gate + linter + hashes
     │
     ▼
optional: publish to DefendableLedger
     │
     ▼
Vast listing reactivated · listing now carries a verifiable Proof Receipt URL
```

## Invariants the integration MUST honor

1. **Never restart Vast services.** `vastai` and `vast_metrics` are not
   subject to remediation by the CLI in v0.1.
2. **Capture Vast validator output verbatim.** The platform's own validation
   trace IS the `evidence_locator` for the corresponding `benchmark_observation`.
3. **Preserve Vast machine status.** The CLI does not modify the listing
   itself; the operator manually relists once the receipt is in hand.
4. **No pricing capture in v0.1.** Pricing-side integration belongs in the
   `aiov_future_integration.md` track; the v0.1 receipt is condition-only.

## Recommended Vast listing description footer

After issuance, the operator can add to their Vast listing description:

```
Defendable Compute Proof Receipt: {ledger_url}
Receipt ID: DCPR-...
Verdict: HONEY (rental_readiness, issued {YYYY-MM-DD})
This is a condition record only; not an appraisal or warranty.
```

This is purely opt-in. The listing functions without the receipt; with it,
the renter can independently verify the host's stated condition.

## Adapter scope

The v0.2 Vast adapter (`adapters/vast_ai.py`, not yet implemented) will:

- Invoke the existing Vast validator command (operator-configured path)
- Parse stdout for the named test results
- Map each to a `benchmark_observation` per
  `protocol/benchmark_validation_protocol.md` test_scope mapping
- Preserve the raw stdout file as evidence

The adapter does **not** auto-detect Vast configuration; the operator
provides the platform path explicitly.

## Open questions for v0.2

- Does Vast.ai expose a stable URL for a host's validation history? If yes,
  the `evidence_locator` should point at the platform URL (more verifiable)
  rather than a captured local copy.
- Can the Vast validator be triggered programmatically without operator
  intervention? If yes, the v0.2 CLI can fully automate Phase 6.
- Is there a hook for receipt URL inclusion in the listing description?
