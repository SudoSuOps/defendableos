# Neocloud / GPU Host / Rental Lane Audit

## Verdict
This is the **fastest validation lane** and the only lane with **DIRECT_EVIDENCE** behind it. Vast.ai is verified; the smash RTX 5090 run *is* a working instance of a host-readiness validation flow. Market-size/pricing/willingness-to-pay claims around it remain JELLY.

## What is DIRECT_EVIDENCE (from smash)
- A real post-rental readiness cycle was executed: Docker cleaned to zero, GPU baseline restored (550 W, persistence), a first-party high-VRAM condition found and resolved, clean idle confirmed (2 MiB, 0%, ~21.55 W), and a Vast remote validation suite passed (sysreq, ResNet18, ECC, NCCL-1GPU, stress-ng+gpu-burn 60s, instance destroyed). Vast platform services were left untouched.
- This proves the **product mechanic** works end-to-end on real hardware on a real rental platform.

## What is HONEY
- Vast.ai is a real GPU rental marketplace (vast.ai, "Rent GPUs") that runs host verification/randomized testing. RunPod and TensorDock resolve and operate tiered host qualification (per Kimi Dim 8; domains resolve). Existence + general verification programs = HONEY.

## What stays JELLY
- "Hosts will pay $50–$150 per certificate" — willingness-to-pay inference, no customer evidence.
- "Capacity sold out through Sep 2026 / H100 rental +40%" — single secondary source (SemiAnalysis), time-sensitive.
- Host/GPU counts — not independently verified.

## Why this is the validation lane
Technical founders, quick decisions, an existing verification habit, and a live integration surface (the smash flow already runs the tests). The receipt makes existing validation **permanent, transferable, and finance-grade** — that is a believable wedge to *test*, and we already have one real data point.

## Action
- Stage 1: run the receipt format against additional Swarm-owned / Vast-hosted GPUs to build a small corpus of real receipts.
- Pricing is an experiment, not a claim. Do not publish the $50–$150 figure.
