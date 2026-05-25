# Federal Corpus v0.3 · Required Updates Post-Registration

> Once Caballerz Network LLC SAM registration moves from **submitted** → **active**, the federal corpus needs a v0.3 update to reflect the new federal-contracting capability.

> ⚠️ **Claim boundary (forward-looking planning doc).** Every "VERIFIED", "eligible", "bid-eligible", and federal-lane statement below describes a **target state contingent on SAM activation and per-solicitation eligibility confirmation** — not a current capability. As of 2026-05-25 the registration is **submitted, activation pending**; CAGE is not assigned; no contract is awarded; and no prime/sub or DoD eligibility is established. Do not cite this document as evidence of present eligibility.

## Files that need to flip from NOT VERIFIED → VERIFIED

### `SMALL_CONTRACT_OPPORTUNITIES.md` · Required Registrations table

Current state (v0.2):

| Registration | Purpose | Status |
| --- | --- | --- |
| UEI | Required for all federal contracts | **NOT VERIFIED** |
| CAGE Code | Required for defense contracts | **NOT VERIFIED** |
| SAM.gov Registration | Required for all bidding | **NOT VERIFIED** |
| NAICS 541715 | R&D / SBIR eligibility | **NOT REGISTERED** |
| NAICS 541519 | Computer Services | **NOT REGISTERED** |
| NAICS 541512 | Computer Systems Design | **NOT REGISTERED** |
| Small Business Size Standard | Must meet SBA size standard per NAICS | **NOT VERIFIED** |
| SBIR Eligibility | US-owned, for-profit, ≤500 employees | **NOT VERIFIED** |
| 8(a) Certification | For 8(a) sole source primes | NOT APPLICABLE |
| SDVOSB Certification | For VA SDVOSB set-asides | NOT APPLICABLE |

v0.3 target state (post-registration):

| Registration | Purpose | Status |
| --- | --- | --- |
| UEI | Required for all federal contracts | **VERIFIED** (Caballerz Network LLC) |
| CAGE Code | Required for defense contracts | **PENDING SAM ACTIVATION** |
| SAM.gov Registration | Required for all bidding | **SUBMITTED 2026-05-25 · pending SAM activation** |
| NAICS 541511 | Custom Computer Programming Services (PRIMARY) | **VERIFIED** |
| NAICS 541715 | R&D / SBIR eligibility | NEEDS SECONDARY ADD (for SBIR opportunities) |
| NAICS 541519 | Computer Services | NEEDS SECONDARY ADD (for cyber/data opportunities) |
| NAICS 541512 | Computer Systems Design | NEEDS SECONDARY ADD (for systems work) |
| Small Business Size Standard | Per 541511 | **VERIFIED · yes (small business under 541511)** |
| SBIR Eligibility | US-owned, for-profit, ≤500 employees | **REQUIRES SEPARATE SBA SBIR ELIGIBILITY CHECK** |
| 8(a) Certification | For 8(a) sole source primes | NOT APPLICABLE (no application filed) |
| SDVOSB Certification | For VA SDVOSB set-asides | NOT APPLICABLE (no veteran-owned status claimed) |

### `12_DEFENDABLE_FEDERAL_LEDGER_MANIFEST.json` · add registration block

Add this top-level field to the manifest:

```jsonc
"federal_entity_registration": {
  "legal_entity": "CABALLERZ NETWORK LLC",
  "operating_brand": "Swarm & Bee",
  "primary_naics": "541511",
  "registration_purpose": "All Awards",
  "federal_lane": "TBD per solicitation after activation (no prime/sub or DoD eligibility asserted)",
  "small_business_under_primary_naics": true,
  "registration_submitted_at": "2026-05-25",
  "registration_status": "submitted_pending_activation",
  "uei_assigned": true,
  "cage_code_assigned": false,
  "confirmation_routed_to": "build@swarmandbee.ai",
  "evidence_path": "federal/sam_registration/2026-05-25/evidence/",
  "tribunal_verdict": "HONEY",
  "tribunal_verdict_date": "2026-05-25",
  "doctrine": "No proof, no honey. The federal identity is submitted; activation is the next gate."
}
```

### `00_EXECUTIVE_VERDICT.md` · add registration milestone section

Insert a new section between §8 (Key Limitations) and §9 (Tribunal Verdict):

```markdown
## 8.5 · Federal Entity Registration Milestone

Submitted 2026-05-25:
- Legal entity: CABALLERZ NETWORK LLC (Florida)
- Operating brand: Swarm & Bee
- Primary NAICS: 541511 — Custom Computer Programming Services
- Registration purpose: All Awards
- Federal lane: TBD per solicitation after activation (no prime/sub or DoD eligibility asserted)
- Confirmation routed to: build@swarmandbee.ai
- Tribunal verdict on the milestone: HONEY
- Status: submitted · pending SAM activation
- Evidence trail: `federal/sam_registration/2026-05-25/`

This flips the corpus from "no federal-contracting entity registered" to "federal-contracting entity submitted in SAM.gov." All v0.2 registration-table NOT VERIFIED rows become VERIFIED at v0.3 once SAM confirms activation.
```

### `11_PARTNER_AND_PRIME_MAP.md` · add CABALLERZ as a prime row

Add a new row to the prime contractor map:

```markdown
| Caballerz Network LLC | NEW · this firm | Florida LLC | 541511 | Software · federal lane TBD per solicitation | Submitted 2026-05-25 · pending SAM activation |
```

### `14_NEXT_30_DAY_FEDERAL_ATTACK_PLAN.md` · revise priorities

Now that registration is submitted, the 30-day plan should shift:

| priority before (v0.2) | priority after (v0.3) |
| --- | --- |
| Get UEI / SAM registration submitted | ✅ DONE 2026-05-25 |
| Identify small-business set-aside targets | ✅ DONE (3 candidate targets · DOT SBIR · NRC · Army 8(a) subcontract path) |
| Wait for SBIR Phase I bid eligibility | DOT SBIR FY2026 Edge AI-V2X · May 29 · candidate — pursuable only after activation + SBIR-specific eligibility check |
| Wait for prime-eligible SB set-asides | NRC Cybersecurity Novel Tech AI/ML · May 26 · candidate — eligibility to be confirmed per solicitation |
| Subcontract path for 8(a) | Army RMF · May 29 · partner with 8(a) prime (unchanged) |

## Recommended sequencing

1. **Week 1 post-activation** (when SAM moves to active):
   - Issue federal corpus v0.3 commit on `remediation/federal-corpus-v0.3-registration-active`
   - Update SMALL_CONTRACT_OPPORTUNITIES.md registration table
   - Anchor the registration record on DefendableLedger
2. **Week 2:**
   - Add secondary NAICS codes (541715 for SBIR · 541519 for cyber · 541512 for systems)
   - Issue capability statement v1.0 under Caballerz Network LLC
3. **Week 3-4:**
   - Submit first RFI responses
   - File SBIR Phase I bid if eligibility confirmed
4. **Q3 2026:**
   - CMMC Level 1 self-attestation (if DoD opportunities require)
   - Consider 8(a) application path if relevant
5. **2027:**
   - Evaluate SBIR Phase II / III progression
   - CMMC Level 2 third-party certification if DoD prime work warrants

## Anchor strategy

Once SAM activation confirms, generate a `REG-SAM-ACTIVE-CABALLERZ-{YYYY-MM-DD}` ledger record on DefendableLedger that supersedes the `REG-SAM-CABALLERZ-2026-05-25` submission record. Same `supersedes` pattern used in DCPR Tribunal verdict promotions.

---

`Books and records · Caballerz now in the federal stack · v0.3 ready to ship when SAM activates. To the shed.` 🐝🇺🇸
