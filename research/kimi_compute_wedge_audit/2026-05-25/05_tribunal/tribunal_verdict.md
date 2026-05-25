# Tribunal Verdict — DEFENDABLEOS-KIMI-COMPUTE-PACKAGE-AUDIT-001

**Date:** 2026-05-25 · **Doctrine:** Tribunal begins before training. No proof, no honey.

## Headline verdict
The Kimi package **correctly identified the first product** (Defendable Compute Proof Receipt) and a **plausible go-to-market sequence**, but **over-graded its external market claims**. Kimi labeled ~262 findings HONEY in its own pass; on independent audit of the *material* claims, the great majority are **JELLY** (secondary-sourced) and three clusters are **PROPOLIS**. The product promotion is **APPROVED** because it rests on DIRECT_EVIDENCE, not on the market claims.

## Adjudicated material-claim tally (this audit, 25 priority claims)
| class | count | meaning |
| --- | ---: | --- |
| DIRECT_EVIDENCE | 4 | smash operational proof + product mechanic |
| HONEY | 4 | external, source located, exact claim confirmed (entity existence / Vast / Barkr / ITAD reality) |
| JELLY | 14 | plausible but secondary/single-source/proposed/WTP/inference |
| PROPOLIS | 3 | Munich Re backing · "no competitor" absolute · Slyd/STS/Maxicom unverifiable |

(The raw extraction layer — 590 ungraded chunks, all placeholder JELLY — is preserved separately in `material_claim_registry.extraction_raw.jsonl` and is **not** a grading.)

## What survived
- Product thesis + smash evidence + Vast validation (DIRECT_EVIDENCE).
- Existence of Barkr, Vast.ai, and 6 datacenter ITADs (HONEY).
- The staged commercialization sequence as a working hypothesis (JELLY, internal).

## What failed or was softened
- $20B lending / $4M gap / OCC requirements → JELLY (no primary trace).
- ITAD $11.7B, decommission $12.95B→$19.94B, 15–25% premium, rental +40%/sold-out → JELLY (secondary).
- EU DPP / HIPAA / export-eligibility "compliance" framing → JELLY (proposed/not-determinable).
- "Munich Re backing" → PROPOLIS (not on Barkr's site).
- "No competitor combines all five layers" → PROPOLIS as worded; softened rewrite mandated.
- Slyd / STS / Maxicom → PROPOLIS (domains dead; identity unverifiable).
- "ITADs have GPU-specific capability" → JELLY (no ITAD homepage mentions GPU).

## Gate
Product promotion: **APPROVED**. External/federal use of any JELLY or PROPOLIS claim: **BLOCKED**. See `04_product_promotion/` for the safe/unsafe split and `contradiction_resolution.md` for the sequence.
