# DefendableOS Integration Memo · Kimi Drop · 2026-05-25T11:37:32Z

> What the Kimi drops uncovered that Swarm & Bee has not yet operationalized,
> and the executable path to fold them into the product rails.

## 1 · What did Kimi uncover that we have not already operationalized?

The published swarm-research v0.1+v0.2 and federal v0.1+v0.2 corpora cover the
**top layer** (executive memos, deliverable headers, manifest). The drops also
contain the **layer below** — uningested in any of the GitHub repos:

| asset | location in drop | currently in any GitHub repo? |
| --- | --- | --- |
| `defendable_dim01_consumer_financial.md` (55KB) | `research/` | **NO** |
| `defendable_dim02_fraud_digital.md` (49KB) | `research/` | **NO** |
| `defendable_dim03_cyber_ai_risk.md` (45KB) | `research/` | **NO** |
| `defendable_dim04_property_contractor.md` (37KB) | `research/` | **NO** |
| `defendable_dim05_asset_compute.md` (40KB) | `research/` | **NO** — direct AIOV feedstock |
| `defendable_dim06_ai_agent_trust.md` (44KB) | `research/` | **NO** |
| `pod04_ai_tevv_results.md` (27KB) | `federal/` | YES (federal corpus) |
| `pod05_cyber_results.md` (33KB) | `federal/` | YES (federal corpus) |
| `pod06_data_governance_results.md` (26KB) | `federal/` | YES (federal corpus) |
| `pod07_08_fraud_compute_results.md` (27KB) | `federal/` | YES (federal corpus) |
| `pod09_award_history_results.md` (49KB) | `federal/` | YES (federal corpus) |
| `pod10_11_smallbusiness_naics_results.md` (32KB) | `federal/` | YES (federal corpus) |
| `12_RESEARCH_GAPS_AND_NEXT_RUN.md` (38KB) | `deliverables/` | YES (swarm-research) |
| `11_PRODUCT_AND_AGENT_OPPORTUNITY_MAP.md` (65KB) | `deliverables/` | YES (swarm-research) |
| `14_NEXT_30_DAY_FEDERAL_ATTACK_PLAN.md` (72KB) | `federal/` | YES (federal corpus) |

**Critical finding:** the 6 dimension research files (`dim01-06`) are NOT in any published repo. They are the deepest research artifacts in the drops and carry the densest citations.

## 2 · What can be folded into DefendableOS immediately?

### Defendable Cyber Proof Ledger (dim03 inputs)
- IBM Cost of Data Breach 2025 metrics ($4.44M global, $10.22M US — HONEY)
- OWASP LLM Top 10 (2025) — prompt injection ranked #1 (HONEY)
- NIST AI RMF + AI 600-1 + CSF mappings already cited
- → Direct integration: ingest these as `02_SOURCE_REGISTRY.csv` rows in a v0.3 swarm-research push

### DefendableOS Federal Demand Intelligence (pods)
- Pods already on GitHub but the dim05 (asset_compute) file is NOT
- 14_NEXT_30_DAY_FEDERAL_ATTACK_PLAN.md is on GitHub but its associated dim research is not

### Defend-A-Pedia vocabulary (entity registry)
- 41 government agencies + 29 companies + 8 datasets + 3 hardware platforms cataloged in `02_extractions/entity_registry.jsonl`
- → Direct integration: bulk-promote to `defend-A-pedia--vocabulary` repo as DDEED-VOCAB entries

## 3 · What belongs in AIOV compute valuation?

The dim05 file is **the strongest AIOV feedstock in the entire drop set**. It carries:

- GPU secondary market data (with the inflated $40B→$140B framing marked PROPOLIS)
- Vast.ai pricing observations
- ITAD secondary-market dynamics
- Counterfeit chip risk (PR-AC-006 receipt)

**Build target:** `aiov_compute_evidence_pack_v0.1` — a JSONL of cited dollar receipts per GPU SKU / per service tier, sourced 100% from dim05.

## 4 · What belongs in Proof of Compute / benchmark receipts?

- The dim06 file (ai_agent_trust) describes TEVV expectations from federal procurement
- Pod04 (ai_tevv_results) documents the DIA AI TEVV RFI (DefendableOS 10/10 fit, already noted in federal corpus)
- **Build target:** A `proof_of_compute_receipt_schema` modeled on `04_CORPUS_SCHEMA.json` from swarm-research, extended with TEVV fields

## 5 · What belongs in a dataset product?

- The 262 HONEY signals → published as a free `defendable_demand_signals_v0.1` dataset on Hugging Face under SudoSuOps
- The 41 agency + 29 company entity registry → published as a CC0 `defendable_buyer_atlas_v0.1` reference dataset
- The 222 source URLs → published as a `defendable_corpus_lineage_v0.1` provenance dataset

These three datasets, together, are the **first-party AI-trust dataset product Swarm & Bee can sell or freely license to compound the moat**.

## 6 · What belongs in sales, federal demand, ITAD, marketplace, or partnership outreach?

### Federal (already operationalized via federal corpus v0.2)
- DOT SBIR FY2026 Edge AI-V2X (May 29) — ~$250K SBIR Phase I
- NRC Cybersecurity AI/ML (May 26) — SB Set-Aside
- Army RMF 8(a) Sole Source (May 29) — subcontract path only

### ITAD / secondary market (dim05)
- Vast.ai as data source for GPU pricing reality
- Coreweave / Crusoe / Lambda Labs as competitive landscape
- **Build target:** ITAD signal registry that ingests Vast.ai pricing API + secondary-market listings into Defendable Deeds

### Partnership outreach (entity_registry)
- Tier 1 prime targets: Palantir, Booz Allen, Lockheed Martin, Raytheon (mentioned across pods)
- Tier 2 small-business primes for 8(a) subcontract: Caelum Research, Bridgephase, Aquia (from federal pods)

## 7 · What should NOT be used until separately verified?

- All 8 PROPOLIS signals (see `03_tribunal/propolis_findings.jsonl`)
- The $40B→$140B secondary-server-market projection — cited but framing is inflated
- The "FTC estimates true fraud losses at $195.9B" claim — flagged PROPOLIS
- The "$103B/$100B counterfeit national-security supply chain" cluster — cited but PROPOLIS-flagged for "massive" language without primary source

## 8 · Next 5 executable builds

| rank | build | source | effort | gate |
| ---: | --- | --- | --- | --- |
| 1 | Promote `dim01-06` files to `defendableos-swarm-research` v0.3 in a `research/dimensions/` subfolder | drops | small | HONEY signals + audit |
| 2 | Build `defendable_demand_signals_v0.1` dataset (262 HONEY rows) | this intake | small | Tribunal pass — already done here |
| 3 | Build `defendable_buyer_atlas_v0.1` dataset (41 agencies + 29 companies) | this intake | small | entity verification round |
| 4 | Bulk-promote entity_registry to `defend-A-pedia--vocabulary` repo (DDEED-VOCAB entries) | this intake | medium | per-term review |
| 5 | Build `aiov_compute_evidence_pack_v0.1` from dim05 | drops | medium | propolis-filter pass |

---

`Trust layers compound. Hype cycles rotate.`
