# Kimi Compute Wedge — Evidence Audit Report

**Audit ID:** DEFENDABLEOS-KIMI-COMPUTE-PACKAGE-AUDIT-001 · **Date:** 2026-05-25
**Operator:** Claude Code — Swarm Evidence Audit · **Doctrine:** Tribunal begins before training. No proof, no honey.

---

## 1. Executive Verdict
Kimi got the **big call right and the proof discipline wrong**. The recommended first product — the **Defendable Compute Proof Receipt** — is sound and is backed by **directly observed Swarm operational evidence** (the smash RTX 5090 post-rental cycle) plus a passed Vast validation suite. **Product promotion is APPROVED.** But Kimi's external market claims were self-labeled HONEY without independent source promotion. On audit of the 25 most material claims: **4 DIRECT_EVIDENCE, 4 HONEY, 14 JELLY, 3 PROPOLIS.** The dollar figures ($20B lending, $11.7B ITAD, $4M gap, 15–25% premium), the "Munich Re" backing, the "no competitor" absolute, and three target companies (Slyd/STS/Maxicom) do **not** survive and must not appear externally.

## 2. Audit Scope and Method
Independent verification of material claims in the Kimi package (`defendableos.agent.final.md` + 11 dimensions + 19 sections inside the mission zip). Method: locate the cited source, read it, and check whether it supports the *exact* claim. Local evidence: 15 fetched competitor/target HTML pages + domain-resolution probes (captured 2026-05-25), the Kimi report read read-only from the zip, and the product workspace v0.1. **Limitation:** this audit did not reach SEC EDGAR credit-agreement exhibits or OCC GPU-specific guidance; those claims remain JELLY in the verification queue. No claim was promoted merely because Kimi labeled it HONEY.

## 3. Source Package Inventory
- `/home/swarm/Kimi_Agent_DefendableOS Compute Wedge Mission.zip` — 916,056 B, sha256 `da0ae8df…` (32 members: report docx/md, outline, 19 sections, 11 dims, cross-verification, insight, landscape).
- `/home/swarm/defendableos.agent.final.md` — 260,560 B, sha256 `8977e76f…`.
- `/home/swarm/DefendableOS_Compute_Wedge_Report.docx` — 1,115,976 B, sha256 `44785fa8…`.
- Originals hash-verified and **not modified** (see `01_raw_reference/`).

## 4. Relationship to Prior Kimi Intake
The prior intake (`research/kimi_intake/2026-05-25/`, commit `65e7a00`) catalogued the broader Kimi drop (262 HONEY / 634 JELLY / 8 PROPOLIS in Kimi's own grading). This audit is narrower and stricter: it independently re-grades the *material* compute-wedge claims and does not inherit Kimi's HONEY labels. A prior partial pass (untracked) extracted 590 raw report chunks as placeholder JELLY; that file is preserved as `material_claim_registry.extraction_raw.jsonl` and superseded by the 25-claim adjudicated registry.

## 5. Relationship to Defendable Compute Proof Receipt v0.1
The product workspace (`products/defendable_compute_proof_receipt/v0.1/`, commit `9aad5d0`) already encodes the right discipline: schemas, CLI spec, a claim-boundary doctrine that **bans** "appraisal/valuation/certified/insurance-backed/lender-accepted," and the smash example. This audit **reinforces** that doctrine and feeds a `market_validation/` crosswalk into it (not overwriting it).

## 6. Direct Operational Evidence from smash (the strongest tier)
- Renter exited; Docker cleaned to zero containers/images/volumes/cache; runtimes + CDI verified.
- GPU baseline restored: 550 W cap, persistence enabled.
- **High-VRAM finding:** 28,114 MiB used at 0% util, 0 containers → traced to **first-party** SwarmCurator vLLM (~28,104 MiB), plus SwarmJelly llama.cpp and DefendableRouter. Not tenant residue.
- Local model services stopped; **Vast services untouched.**
- Clean idle confirmed: 2 MiB / 32,607 MiB, 0% util, ~51 °C, ~21.55 W, 550 W cap, persistence on.
- Vast remote validation: system requirements, ResNet18, ECC, NCCL (1 GPU), simultaneous stress-ng + gpu-burn 60 s — all pass; instance destroyed; machine test DONE.
- This is the proof the product mechanic works on real hardware, and that the receipt can distinguish first-party residue from tenant contamination.

## 7. Kimi Strategic Thesis Reviewed
Thesis: build the Proof Receipt; ITAD remarketing = fastest paid volume; neoclouds = fastest validation; lenders/ABL = scale; ITAD→neocloud→lender record triangle. **Assessment:** product call correct; validation/paid/scale lanes correct *as a sequence* but mislabeled (Kimi called lenders the "first paid wedge"). The triangle is a plausible network-effect hypothesis, not a verified fact.

## 8. Claim Audit Summary
25 material claims adjudicated: **DIRECT_EVIDENCE 4 · HONEY 4 · JELLY 14 · PROPOLIS 3.** Full registry: `02_claim_audit/material_claim_registry.jsonl`; trace matrix: `claim_source_trace_matrix.{csv,md}`.

## 9. Material Claims Promoted to HONEY (and DIRECT_EVIDENCE)
- DIRECT_EVIDENCE: product thesis on smash basis; smash clean idle; first-party VRAM trace; Vast validation pass.
- HONEY: Vast.ai real GPU marketplace w/ host verification; Barkr real (AI insurance-backed valuation for lenders; partner-candidate); Blancco/Spherity/EquipmentWatch real adjacent platforms; 6 datacenter ITADs real.

## 10. Material Claims Retained as JELLY
GPU-specific ITAD capability (adjacent only); $20B lending; $4M gap; OCC requirements; ITAD $11.7B + CAGRs; decommission $12.95B→$19.94B; 15–25% premium + price points; rental +40%/sold-out; $50–150 host WTP; EU DPP 2027; HIPAA serialized destruction; export-eligibility; commercialization sequence; $176B depreciation→audit demand. (14 total.)

## 11. PROPOLIS Findings and Rejected Claims
- **Munich Re backing of Barkr** — not on Barkr's own site; no primary source.
- **"No competitor combines all five layers (49 scanned)"** — unfalsifiable absolute; rewrite mandated.
- **Slyd / STS Electronic Recycling / Maxicom** — domains do not resolve; identity unverifiable; removed from outreach.

## 12. Lender / ABL Lane Audit
Highest long-term value, least verified. All dollar/covenant claims JELLY; Munich Re PROPOLIS. CoreWeave is a verified real AI cloud but debt figures are not traced to primary filings here. **No lender/appraisal/insurer/OCC claim may be used externally.** (Detail: `03_market_audit/lender_lane_audit.md`.)

## 13. ITAD / Remarketing Lane Audit
6 of 10 targets verified real datacenter ITADs; Iron Mountain existence-only (bot-walled); Slyd/STS/Maxicom unverifiable. **No ITAD homepage advertises GPU/NVIDIA** — GPU relevance is adjacent/inferred. R2v3 funds data destruction/compliance, **not** a market-value verification budget. (Detail: `itad_target_audit.md`.)

## 14. Neocloud / GPU Host Lane Audit
Fastest validation lane and the only one with DIRECT_EVIDENCE. Vast.ai verified; smash run is a working instance. Pricing/sold-out/WTP claims JELLY. (Detail: `neocloud_host_lane_audit.md`.)

## 15. Market Comps Source Audit
All comps are secondary (HashrateIndex, SemiAnalysis, oplexa, BigDataSupply, eBay/Reddit; EquipmentWatch is heavy-equipment). No primary transaction feed located. Build the comps registry with source-quality flags; never emit a value conclusion or call it an "index." (Detail: `compute_comps_source_audit.md`.)

## 16. Target Organization Audit
Verified (HONEY, outreach-prep eligible as datacenter ITADs, GPU adjacent): Sims Lifecycle, SK tes, Apto, Procurri, Re-Teck, GreenTek Solutions. Existence-only (JELLY): Iron Mountain. Unverifiable (PROPOLIS): Slyd, STS, Maxicom. Registry: `verified_target_registry.jsonl`. **No contact data is asserted** — outreach must source contacts from official pages at send time.

## 17. Competitor Claim Audit
"No competitor" absolute → PROPOLIS; approved rewrite: *"The audited sample did not reveal a single platform publicly describing all identified layers in one offering."* Each verified competitor occupies one adjacent layer; differentiation thesis is usable internally, not as an absolute externally.

## 18. Regulatory and Compliance Claim Audit
EU DPP (ESPR) is real law but per-product delegated acts are phased — ICT/compute applicability + 2027 timeline unconfirmed → JELLY/PROPOSED. HIPAA Security Rule changes are PROPOSED (NPRM) → JELLY. Export controls (ECCN 3A090/4A090) are real categories but a receipt can **record** identity, not **determine** eligibility. **Never claim a receipt makes a company compliant.**

## 19. Barkr/Barker and Other Entity-Name Conflict Resolution
Canonical entity is **Barkr** (barkr.ai); "Barker" is an empty redirect shell. Munich Re unconfirmed. GreenTek Solutions (greenteksolutionsllc.com) ≠ greentek.com (turf company). Re-Teck = re-teck.com (not reteck.com). Slyd/STS/Maxicom unresolved. No fabricated contacts. (Detail: `02_claim_audit/name_entity_conflicts.jsonl`.)

## 20. Commercialization Sequence Verdict
**Validate on neoclouds (Stage 1) → first paid revenue on ITAD (Stage 2) → scale into lenders (Stage 3).** Lenders are the destination, not the entry. (Detail: `05_tribunal/contradiction_resolution.md`.)

## 21. Product Promotion Decision
**APPROVED.** Components A/B/C/E supported by DIRECT_EVIDENCE + schema; D (market signal) is a flagged-provenance hypothesis; value/appraisal output remains prohibited. (Detail: `04_product_promotion/proof_receipt_product_support.md`.)

## 22. Sales-Safe Claims
See `04_product_promotion/sales_safe_claims.md` (what the receipt records, timestamp-scoped, condition not value) and `claims_not_safe_for_sales.md` (third-party-acceptance and dollar/compliance claims prohibited).

## 23. Federal-Facing Claim Boundaries
CABALLERZ NETWORK LLC SAM registration is **submitted, not active**. Only DIRECT_EVIDENCE/HONEY (with review) may enter capability statements; no Kimi market/lender/compliance figure. Allowed vocabulary listed in `federal_facing_claim_boundaries.md` and the federal memo.

## 24. Ranked Build Queue
Build now (DIRECT_EVIDENCE/HONEY): #1 schema+CLI lint, #2 smash example, #3 collector spec, #4 verified target registry. Next wave (gated on Stage-1 evidence): comps registry, federal capability statement, pilot questionnaire, claim-verification ledger. Do not build toward the lender lane yet. (Detail: `product_integration_recommendations.md`.)

## 25. Verification Work Remaining
- CoreWeave/Lambda/xAI debt → SEC EDGAR / credit-agreement exhibits.
- OCC/interagency appraisal guidance applicability to GPU collateral.
- Barkr–reinsurer relationship → primary source.
- EU DPP delegated-act timeline for ICT; HIPAA final rule status.
- Per-target GPU-handling confirmation for the 6 verified ITADs.
- Iron Mountain readable service page; resolving domains for Slyd/STS/Maxicom.
- Secondary market-size/pricing figures → primary corroboration before any external use.

## 26. Receipt and Hash Appendix
See `06_receipts/audit_manifest.json` and `06_receipts/SHA256SUMS.txt` for the full artifact hash set and the safety attestation (no GPU/model/Docker/Vast/NVIDIA/network/apt changes; originals unmodified; no push; no outreach).

---

### Answers to the required questions
- **Did Kimi identify the first build correctly?** Yes — Defendable Compute Proof Receipt.
- **Fastest to validate?** Neocloud / GPU host (DIRECT_EVIDENCE already exists).
- **Fastest to first paid revenue?** ITAD remarketing pilot (6 verified targets).
- **Highest long-term value?** GPU lenders / ABL (unverified today; do not lead).
- **Which Kimi dollar claims survived?** None as verified fact — all remain JELLY pending primary sources.
- **Which targets are ready for outreach prep?** Sims, SK tes, Apto, Procurri, Re-Teck, GreenTek Solutions (as datacenter ITADs; GPU fit to confirm).
- **Which claims must not be used externally?** All JELLY/PROPOLIS: dollar figures, Munich Re, "no competitor," compliance/lender/appraisal language, Slyd/STS/Maxicom.
- **Does this justify product promotion?** Yes — into `market_validation/`, on DIRECT_EVIDENCE.
- **What should Swarm build next?** Build queue #1–#4 now; gate the rest on Stage-1 pilots.

`Books and records. Promote only what survives source examination. To the shed.`
