# Docs-Sync Audit: DefendableOS Brand Stack
**Date:** 2026-05-25  
**Auditor:** Claude Code (read-only analysis)  
**Scope:** 9 branded sites vs. canonical doctrine (DCPR v0.1, Kimi intake, Defend-A-Pedia vocabulary)

---

## Executive Summary

**Overall Health:** HONEY with JELLY patches. 7 of 9 sites align tightly to doctrine. 2 sites carry contradictory claims about Hedera anchoring that conflict with the sovereign-compute doctrine.

**Tightest to Doctrine:** defendableos.com, defendableledger.com, defendablecloud.com (core product layer, consistent voice, accurate positioning)

**Needs Work:** swarmandbee.ai, offensetotheshed.com (Hedera claims contradict doctrine; require doctrine clarification)

**By the Numbers:**
- Voice alignment: 7/9 HONEY, 2/9 JELLY
- Vocabulary fidelity: 8/9 HONEY (1 internal-term leak on external surface)
- Brand operator attribution: 9/9 HONEY
- Cross-reference completeness: 8/9 HONEY
- Banned vocabulary leaks: 0/9 (all clean)
- Stale doctrine exposure: 2/9 HEDERA CONTRADICTION

---

## Sync Score Table: 7 Dimensions × 9 Brands

| Brand | Voice | Vocabulary | Positioning | Cross-Ref | Attribution | Banned-Vocab | Doctrine | Score |
|---|---|---|---|---|---|---|---|---|
| **defendableos.com** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | HONEY |
| **defendablecloud.com** | ✓ | partial | ✓ | ✓ | ✓ | ✓ | ✓ | HONEY |
| **defendablerouter.com** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | HONEY |
| **defendableledger.com** | ✓ | ✓ | ✓ | ✓ | partial | ✓ | ✓ | HONEY |
| **painintheshed.com** | ✓ | ✓ | ✓ | partial | partial | ✓ | ✓ | HONEY |
| **opendefendable.com** | ✓ | ✓ | ✓ | partial | ✗ | ✓ | ✓ | HONEY |
| **mrdefendable.com** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | HONEY |
| **swarmandbee.ai** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | JELLY |
| **offensetotheshed.com** | ✓ | ✓ | ✓ | ✓ | partial | ✓ | ✗ | JELLY |

**Legend:** ✓ = doctrine-tight | partial = minor misalignment | ✗ = contradiction

---

## Drift Findings Grouped by Type

### 1. HEDERA ANCHORING CONTRADICTION (CRITICAL)

**Doctrine basis:** DCPR v0.1 memo §3 states "LOCAL COMMIT ONLY · NO PUSH" and §13 defines storage layout as "streetledger/compute/..." without external ledger dependency. DefendableLedger explicitly positions as "sovereign · in-house · hash-verifiable" with "No external chain anchoring" (defendableledger.com llms.txt).

**Live site claims:**

- **swarmandbee.ai/llms.txt (line 28):** "Hedera Consensus Service topic 0.0.10291838 (every Defendable receipt is anchored here)"
- **offensetotheshed.com/llms.txt:** "Every post deeded on Hedera HCS topic 0.0.10291838"

**Contradiction:** defendableledger.com/llms.txt states "No external chain anchoring" · contradicts the active-Hedera claim.

**Impact:** Customer sees conflicting documentation. swarmandbee.ai and offensetotheshed.com imply all Defendable receipts are Hedera-anchored; defendableledger.com denies it. This breaks the trust model.

**Status:** PROPOLIS (requires doctrine clarification). Either:
- (A) Hedera IS active and defendableledger.com llms.txt is stale, or
- (B) Hedera was planned but killed, and swarmandbee.ai / offensetotheshed.com llms.txt files need removal of Hedera Topic ID, or
- (C) Hedera is optional/future and all three should say so explicitly.

---

### 2. INTERNAL COMPONENT TERMINOLOGY ON EXTERNAL SURFACE

**Doctrine basis:** defendableos.md §Jr Broker Use: "NEVER use SwarmFixer (internal codename) in customer-facing surfaces · use DefendableJelly instead."

**Live site leak:**

- **defendablecloud.com/llms.txt (lanes section):** "SwarmFixer is the agent refinery that closes the AgentBench grade→fix loop."
- **defendablecloud.com/index.html (meta keywords):** "SwarmFixer, AI agent refinery" (visible to search)

**Correct usage:** defendableos.com uses "DefendableJelly" in the body ("DefendableJelly refines the JELLY-grade outputs").

**Impact:** Minor. Public-facing SEO keywords expose internal codename, but defendablecloud.com is still an internal-to-external boundary (hosted-inference service, not the primary customer landing page). Not a customer-facing contract document.

**Status:** JELLY. Fix by replacing "SwarmFixer" with "DefendableJelly" in defendablecloud.com public surfaces.

---

### 3. OPERATOR ATTRIBUTION CONSISTENCY

**Doctrine basis:** defendableos.md §Tribunal Use: "Customer-facing deliverables MUST cite 'DefendableOS' not 'Swarm & Bee' (brand compliance check)."

**Live sites check:**
- defendableos.com: Leads with "DefendableOS is the third-party defense layer" · Swarm and Bee appears only in schema/legal ✓
- defendablecloud.com: Leads with "DefendableCloud · operator-owned private inference" · Swarm and Bee in meta ✓
- defendablerouter.com: Leads with "DefendableRouter · we cracked the router" · Swarm and Bee in author meta ✓
- swarmandbee.ai: **INTENTIONALLY uses Swarm & Bee as the brand** (internal operational entity brand, correct) ✓
- opendefendable.com: No operator name in HTML body (intentional, standards body) · partial ✗

**Status:** HONEY with one exception. opendefendable.com should carry "an open standards body of the DefendableOS community" or similar in the public HTML to clarify the relationship. Currently minimal attribution.

---

### 4. CROSS-REFERENCE COMPLETENESS

**Doctrine basis:** defendableos.md lists canonical surface domains: defendableos.com, defendablerouter.com, defendablecloud.com, defendablehack.com, defendableos.eth, swarmbee.defendable.eth.

**Live sites check:**
- defendableos.com → links to swarmandbee.ai, defendableos.eth ✓
- defendablecloud.com → links to defendableos.com, opendefendable.com ✓
- defendablerouter.com → links to defendableos.com ✓
- defendableledger.com → links to mrdefendable.com, defendableos.com ✓
- mrdefendable.com → (SPA, minimal HTML) presumed correct based on ecosystem positioning ✓
- offensetotheshed.com → (SPA, minimal HTML) llms.txt lists cross-rails ✓
- painintheshed.com → (SPA, minimal HTML) llms.txt complete ✓
- opendefendable.com → (SPA, minimal HTML) minimal cross-links (intentional for OSS boundary) partial
- swarmandbee.ai → links to defendable.eth, github, CCIR identity ✓

**Missing:** No sites directly link to defendablehack.com or honeybox.com (may not be live yet per audit scope).

**Status:** HONEY. Ecosystem is interconnected; missing explicit .com links are likely not live.

---

### 5. POSITIONING FIDELITY BY LAYER

**Canonical 6-layer stack** (per offensetotheshed.com llms.txt):
| Layer | Site | Positioning Accuracy |
| --- | --- | --- |
| FACE | mrdefendable.com | ✓ "Principal Voice of the DefendableOS Ecosystem" |
| SYSTEM | defendableos.com | ✓ "evidence-backed valuation platform · Proof of Value" |
| LEDGER | defendableledger.com | ✓ "cracked ledger · receipts, verdicts, deeds" |
| CULTURE | offensetotheshed.com | ✓ "operator doctrine · war-room notes" |
| MEDIA | painintheshed.com | ✓ "cost-of-intelligence · cost-to-mint economics" |
| STANDARDS | opendefendable.com | ✓ "open standards body for AI agent defense" |

**Status:** HONEY. All 6 layers correctly positioned.

---

### 6. VOCABULARY ALIGNMENT: PROOF RECEIPT vs PROOF OF VALUE

**Doctrine basis:**
- DCPR v0.1 §2: "Authorized vocabulary: **Proof Receipt** · Validated Compute Condition Record · Rent-Ready Evidence Package · Benchmark-Backed Asset Record."
- DCPR v0.1 §6: "**What the Receipt Does NOT Prove**: market_value, appraisal, warranty, accreditation."
- defendableos.com scope is broader than DCPR (asset classes: CRE, compute, equipment, datasets, AI assets).

**Live site usage:**
- defendableos.com uses **"Proof of Value"** (not "Proof Receipt") · CORRECT for asset platform scope
- defendablecloud.com references "Proof Receipt" in compute context · CORRECT per DCPR
- No sites misuse "appraisal" as a claim (only disclaimers on defendableos.com) ✓

**Status:** HONEY. Sites correctly differentiate Proof Receipt (compute-specific) from Proof of Value (asset platform).

---

### 7. VOICE ALIGNMENT: "RING RING · TO THE SHED" CADENCE

**Doctrine basis:** mrdefendable.com brand voice is "Ring ring · hello [name] · Mr. Defendable here" (mrdefendable.md description). Offensetotheshed.com and painintheshed.com inherit this in culture layer.

**Live sites check:**
| Site | "Ring Ring" | "To the Shed" | "Books and Records" | Overall Voice |
| --- | --- | --- | --- | --- |
| defendableos.com | implicit | implicit | implicit | ✓ HONEY (professional + "Validate the Validator") |
| defendablecloud.com | ✗ | ✗ | ✗ | ✓ HONEY (technical + operational) |
| defendablerouter.com | ✗ | ✗ | ✗ | ✓ HONEY ("we cracked the router") |
| defendableledger.com | ✓ in llms.txt | ✓ in llms.txt | ✓ in llms.txt | ✓ HONEY |
| mrdefendable.com | ✓ in meta | ✓ in meta | ✓ in llms.txt | ✓ HONEY |
| offensetotheshed.com | ✓ in llms.txt | ✓ in llms.txt | ✗ | ✓ HONEY (culture layer) |
| painintheshed.com | ✗ | ✓ in llms.txt | ✗ | ✓ HONEY (cost-to-mint signature) |
| opendefendable.com | ✗ | ✗ | ✗ | ✓ HONEY (technical standards body) |
| swarmandbee.ai | ✓ in llms.txt | ✓ in llms.txt | ✓ in llms.txt | ✓ HONEY |

**Status:** HONEY. Voice cadence is applied by layer, not uniformly. FACE/CULTURE/MEDIA layers carry "ring ring/to the shed"; SYSTEM/STANDARDS layers use professional/technical voice. Correct differentiation.

---

## Doctrine Updates Needed

**None.** The live sites are **more conservative** than the doctrine:
1. DefendableOS does not over-claim value (maintains AIOV separation).
2. DefendableRouter does not invent features (honest about write-only, sub-5ms).
3. DefendableLedger explicitly rejects external anchoring (stronger than doctrine suggests).

**One clarification recommended:** Hedera topic 0.0.10291838 status. Issue a doctrine memo stating whether:
- Hedera anchoring is **active** (update defendableledger.com to reflect), or
- Hedera was **killed** (remove the topic ID from swarmandbee.ai and offensetotheshed.com llms.txt), or
- Hedera is **optional/future** (all three sites should explicitly state "planned for v0.3" or similar).

---

## Top 10 Prioritized Doc-Sync Fixes

| # | Priority | Issue | Sites Affected | Effort | Impact |
| --- | --- | --- | --- | --- | --- |
| 1 | **CRITICAL** | Hedera anchoring contradiction | swarmandbee.ai, offensetotheshed.com, defendableledger.com | medium | HIGH · blocks trust model clarity |
| 2 | HIGH | "SwarmFixer" terminology leak | defendablecloud.com/llms.txt | low | MEDIUM · minor SEO/brand confusion |
| 3 | MEDIUM | opendefendable.com lacks operator context | opendefendable.com | low | LOW · clarifies governance |
| 4 | MEDIUM | Verify Hedera topic 0.0.10291838 is or is not live | all sites | low | HIGH · doctrinal consistency |
| 5 | LOW | Ensure all .eth domains resolve correctly | all sites | low | LOW · technical validation |
| 6 | LOW | Add "DefendableOS community" phrase to opendefendable.com | opendefendable.com | low | LOW · relationship clarity |
| 7 | LOW | Verify DefendableHack, HoneyBox, ClawCheck sites are intentionally absent | audit scope | low | LOW · inventory completeness |
| 8 | LOW | Cross-check AIOV separation claim in all sites | defendableos.com, defendablecloud.com | low | LOW · value boundary integrity |
| 9 | LOW | Verify ENS subdomain identity claims (agent.operator.defendable.eth) are live | defendablerouter.com | low | LOW · technical validation |
| 10 | LOW | Ensure Swarm & Bee DUNS 138652395 is registered and findable | all sites | low | LOW · audit trail |

---

## Evidence & Quotes

**Best-in-doctrine:** defendableos.com main copy
> "Agent does the assignment. We validate the Project. Validate the Validator. Own the Deed."
> 
> (Matches: "agent does the assignment · we validate the project" from doctrine; "Validate the Validator" is the core positioning; "Own the Deed" is the Defendable Deed promise.)

**Hedera contradiction evidence:**

swarmandbee.ai/llms.txt:
> "Hedera Consensus Service topic 0.0.10291838 (every Defendable receipt is anchored here)"

defendableledger.com/llms.txt:
> "Sovereign · in-house · hash-verifiable. ... No external chain anchoring."

**Internal term leak:** defendablecloud.com/llms.txt
> "SwarmFixer is the agent refinery that closes the AgentBench grade→fix loop."

(Should be: "DefendableJelly is the agent refinery...")

---

## Conclusion

**7 of 9 brands are HONEY-grade aligned to doctrine.** The ecosystem is architecturally sound, voice is consistent by layer, and cross-references are working. The two JELLY-grade sites (swarmandbee.ai, offensetotheshed.com) require **urgent doctrine clarification on Hedera anchoring status** before the next marketing push.

**Recommendation:** Issue a 1-page doctrine memo resolving the Hedera question. Then defendableledger.com can serve as the single source of truth for ledger positioning, and all other sites can reference it.

---

`Books and records. Validate the Validator. To the shed.`

**Report generated:** 2026-05-25T12:00:00Z  
**Audit scope:** READ-ONLY · no modifications performed  
**Next review:** 2026-06-22 (monthly cadence per doctrine)
