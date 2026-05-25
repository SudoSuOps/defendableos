# Public Claims Patch Log · defendable-compute-wedge

Repo: `github.com/SudoSuOps/defendable-compute-wedge`
Pre-pass HEAD: `78db387` · Corrective commit: `78bd10b` (pushed to `main`)

## Principle applied

The required independent **source-promotion audit** (promoting research-sweep sources to
verified primary references) was not completed before publication. External market claims are
therefore downgraded. Tiering used:

- **DIRECT_EVIDENCE** — DefendableOS smash-rig operational results only (benchmark/identity runs
  executed in-house). *Not applied to any external market figure.*
- **RESEARCH-SUPPORTED / VERIFICATION PENDING** — market-structure findings from the sweep,
  awaiting primary-source promotion.
- **JELLY** — pricing, market-size, willingness-to-pay, funding/valuation, competitor-gap claims.

The product recommendation (**Defendable Compute Proof Receipt is the recommended first build**)
is preserved and explicitly marked unaffected by audit status. Underlying research is preserved.

## Statements found and corrected

| location | before (problematic) | after (corrected) |
| --- | --- | --- |
| `README.md` subtitle | "Verified Comps · Benchmark Receipts · First Paid Customer Path" | "Research Corpus · Source-Promotion Audit Pending" |
| `README.md` top | "🍯 Tribunal verdict: HONEY · 9 high-confidence cross-verified findings" | Status banner: research corpus, audit pending, with the 3-tier labeling and preserved product recommendation |
| `README.md` thesis sentence | "$20B+ market … $15K-20K H100 secondary value, 15-25% refurbished premium … 300+ new entrants" stated as fact | figures softened + explicit "(all market sizes, premiums, entrant counts … VERIFICATION PENDING)" |
| `README.md` | "**No competitor** (49 scanned across 14 categories) combines all five layers." | "The reviewed research sample (49 alternatives scanned …) **did not identify a publicly described offering combining all five proposed layers; further competitive verification is required.**" |
| `README.md` pillars header | "Headline evidence pillars (HONEY)" | "Headline research findings (RESEARCH-SUPPORTED · VERIFICATION PENDING)" + audit note |
| `README.md` competitor row | "49 competitors · no integrated stack \| None combines …" | "49 alternatives scanned · no integrated stack found in sample \| reviewed sample did not surface … further verification required" |
| `README.md` doctrine | "9 HONEY findings = cross-verified by 2+ independent dimensions from authoritative sources" | internal cross-pass is not a substitute for primary-source promotion; market findings are JELLY/VERIFICATION PENDING until audit completes |
| `audit/TRIBUNAL_VERDICT.md` | "## 🍯 HONEY" + "HONEY \| 9 \| ready for build/outreach/action" | "## Status: RESEARCH CORPUS · SOURCE-PROMOTION AUDIT PENDING" + RESEARCH-SUPPORTED row with VERIFICATION PENDING |
| `audit/TRIBUNAL_VERDICT.md` | "Quantified evidence pillars (HONEY)" with hard $ figures | "Quantified research findings (RESEARCH-SUPPORTED · VERIFICATION PENDING)" + per-line "figures pending audit" |
| `audit/TRIBUNAL_VERDICT.md` | "no competitor offers all three" / "none combines all 5 layers" | bounded "reviewed sample did not surface … further verification required" |
| `audit/mission_manifest.json` | `"tribunal_verdict": "HONEY"`, `"HONEY": 9` | `"tribunal_verdict": "RESEARCH_CORPUS_SOURCE_PROMOTION_AUDIT_PENDING"`, `"RESEARCH_SUPPORTED": 9`, + `claim_status` block |

## Specific Kimi-derived claims now labeled VERIFICATION PENDING / JELLY

- $20B+ GPU-collateralized lending market
- $11.7B ITAD market
- $12.95B → $19.94B AI GPU decommissioning market (2032)
- 15–25% refurbished-condition premium
- Barkr funding / valuation / Munich Re backing
- neocloud share (~1/3) and 300+ entrant counts
- H100 rental tightness / sold-through capacity
- "No competitor combines all five layers" (rewritten to bounded language)

## Preserved (not deleted)

- All `sections/`, `research_dims/`, `deliverables/*.md`, and `extractions/` research artifacts
- The three-phase go-to-market recommendation
- The Defendable Compute Proof Receipt product recommendation
