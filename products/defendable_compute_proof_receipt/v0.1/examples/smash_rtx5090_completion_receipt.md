# Completion Receipt · smash RTX 5090 post-rental cycle · 2026-05-25

> Plain-text record of what was actually performed on the smash host during
> the post-renter verification sequence. This document is a witness, not a
> claim — it accompanies the structured `smash_rtx5090_proof_receipt.example.json`.

## Sequence performed

1. **Renter exited.** Vast.ai tenancy concluded.
2. **Docker rental artifacts cleaned.** No containers, images, networks, or
   volumes attributable to the prior tenant remained.
3. **Docker storage/runtime/CDI verified.** `runc` and `nvidia` runtimes
   configured. CDI devices present.
4. **GPU baseline restored.** Persistence enabled, 550 W rental cap set.
5. **High VRAM condition discovered.** `nvidia-smi` reported 28,114 MiB used
   while `docker ps` showed zero containers.
6. **Investigation identified the cause as first-party.** Local SwarmCurator
   vLLM process (PID 75037) was holding 28,104 MiB. Additional first-party
   sessions identified: SwarmJelly llama.cpp server (port 8089) and
   DefendableRouter (port 8080).
7. **Local model services shut down.** SIGTERM sequence to vLLM, llama.cpp,
   and DefendableRouter. Vast services (`vastai`, `vast_metrics`) were
   explicitly NOT touched.
8. **Post-shutdown state confirmed.**
   - VRAM used: 2 MiB
   - GPU utilization: 0 %
   - GPU temperature: ~51 °C
   - GPU power draw: ~21.55 W idle
   - Power cap: 550 W
   - Persistence: enabled
9. **Vast.ai services remained active.** `vastai` and `vast_metrics` were
   running before, during, and after the local-side cleanup.
10. **No Docker containers remained.** `docker ps` returned empty.
11. **Vast remote validation executed and passed:**
    - system requirements test → pass
    - ResNet18 GPU test → pass
    - ECC test → pass
    - NCCL distributed test with 1 GPU → pass
    - simultaneous stress-ng + gpu-burn test for 60 seconds → pass
    - test instance destroyed successfully
    - machine test result: **DONE**

## What this completion receipt does NOT establish

- No market value for the asset
- No formal appraisal
- No warranty status determination
- No insurance attestation
- No certification by a third-party body
- No statement of long-term reliability or fitness for any specific workload

It establishes only the **operational condition** of the asset at the
timestamp the sequence completed.

## Where to find the structured artifact

Structured receipt: `examples/smash_rtx5090_proof_receipt.example.json`

Verdict: 🍯 **HONEY** — asset returned to verified idle state and passed
platform-remote functional/stress validation for rental readiness.

## Operator notes

- The high-VRAM precheck finding was first-party, not renter contamination —
  this is a critical distinction. The Proof Receipt records both the finding
  and the remediation transparently.
- A different finding (e.g., `GPU_MEMORY_HELD_BY_UNKNOWN_PROCESS`) would have
  blocked the HONEY verdict per the Tribunal gate.
- All Vast platform services were left untouched. Future automated runs of
  this protocol must preserve this invariant.

---

`Books and records. No proof, no honey. To the shed.`
