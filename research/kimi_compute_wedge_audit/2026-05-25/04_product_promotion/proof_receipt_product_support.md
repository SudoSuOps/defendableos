# Defendable Compute Proof Receipt v0.1 — Product Promotion Support

## Promotion verdict: **PROMOTE** (the product thesis survives audit)

The product is supported by **direct operational evidence** (smash) plus **verified external workflow evidence** (Vast). Revenue/market sizing around it stays JELLY but does not block promotion — the *product* stands on DIRECT_EVIDENCE; the *market claims* are separated out.

## Component-by-component evidence grade

### A. Asset Identity — SUPPORTED (DIRECT_EVIDENCE + product schema)
- smash run identified GPU to runtime (RTX 5090), host, runtime/CDI visibility, chain-of-observation.
- Schema already supports `serial_or_uuid` with `full`/`salted_hash`/`redacted` privacy treatments.
- **Hypothesis remaining:** export-control status field (ECCN) — can *record* identity, must not *determine* eligibility (JELLY, KCW-CLAIM-0021).

### B. Functional Condition — SUPPORTED (DIRECT_EVIDENCE)
- Active-workload detection proven: 28,114 MiB VRAM at 0% util with 0 containers → traced to first-party SwarmCurator vLLM, not tenant residue. This is the single strongest demonstration of product value.
- Baseline (550 W, persistence), thermals (~51 C), power (~21.55 W idle), service state, runtime/CDI exposure all captured.

### C. Benchmark Evidence — SUPPORTED (DIRECT_EVIDENCE)
- Vast remote suite passed: system-requirements, ResNet18, ECC, NCCL (1 GPU), simultaneous stress-ng + gpu-burn 60 s, instance destroyed.
- Pass/fail limits and evidence preservation defined in product protocol.
- **Limitation:** one GPU, one run — corpus of 1. Needs more receipts (Stage 1).

### D. Market Signal Attachment — HYPOTHESIS (build with source-quality flags)
- Comp sources are all secondary (see compute_comps_source_audit). Build the comps registry with provenance flags. **No automatic valuation conclusion** — product doctrine bans "valuation"/"appraisal".

### E. Hash Receipt — SUPPORTED (product schema)
- Artifact hashes, manifest, tamper-evident record, verification chain already specified.
- **Must not** claim legal title or regulatory compliance (doctrine + this audit).

## Summary table
| component | grade | basis |
| --- | --- | --- |
| A Asset Identity | SUPPORTED | smash DIRECT_EVIDENCE + schema |
| B Functional Condition | SUPPORTED | smash DIRECT_EVIDENCE |
| C Benchmark Evidence | SUPPORTED | smash + Vast DIRECT_EVIDENCE |
| D Market Signal Attachment | HYPOTHESIS | secondary comps only (JELLY) |
| E Hash Receipt | SUPPORTED | product schema |
| export-control field | HYPOTHESIS | ECCN real, eligibility not determinable (JELLY) |
| value/appraisal output | PROHIBITED | banned in v0.1 |
