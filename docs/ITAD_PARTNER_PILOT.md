# Defendable Compute Partner Feed Pilot · ITAD Outreach Plan

The **ITAD lane** is the highest-quality comp source we have access to.
An ITAD partner moving H100s / A100s / DGX systems can supply data
that public marketplaces never expose: configuration, test status,
condition class, chain of custody, sanitization records, transaction
amount, transaction date, sale channel · all attached to a
**completed transaction**, not a listing.

This is also a **two-sided product opportunity**. The same firms that
have the data we want also have a pain we can solve: proving
hardware identity, packaging premium remarketing inventory, producing
buyer-facing recovery-value reports. Defendable Compute MarketReady
is the offer to them.

## The 8 verified targets

### Track A · specialist · faster pilot

| Partner | Status | Coverage |
|---|---|---|
| **Jawa** | OUTREACH_READY | GPU-native marketplace · references anonymized GPU sales data |
| **SellGPU** | OUTREACH_READY | GPUs / CPUs / RAM / SSDs / PCs / server components · bulk ITAD |
| **GreenTek Solutions** | OUTREACH_READY | DGX H100 / A100 / L40 / V100 / T4 / deep-learning servers / GPU rigs |

### Track B · enterprise · slower cycle but higher value

| Partner | Status | Coverage |
|---|---|---|
| **Alta Technologies** | OUTREACH_READY | H100/H200/A100-class GPUs · AI servers · full racks · R2v3 certified |
| **exIT Technologies** | OUTREACH_READY | DGX/HGX · H100/H200/A100/A800/L40S/L40/V100 · NVLink/NVSwitch · requests configs+photos |
| **Re-Teck** | OUTREACH_READY | Cloud / AI data-center ITAD · GPU-dense servers |
| **Iron Mountain** | OUTREACH_READY | Global ITAD · secure disposition · remarketing · enterprise institutional path |
| **ServerMonkey** | OUTREACH_READY | Used servers / networking · refurbished GPU servers for AI/ML/HPC |

All 8 are seeded in `itad_partners` table with:
- `partnership_status = OUTREACH_READY`
- `agreement_status = NONE`
- `rights_scope = AGREEMENT_REQUIRED`
- `contact_status = NOT_CONTACTED`

## The ask

Each partner gets a small anonymized pilot export of **50–250 completed
transactions** covering AI compute hardware categories:

- NVIDIA H100 / H200
- NVIDIA A100
- NVIDIA L40 / L40S
- NVIDIA RTX 6000 Ada / RTX A6000 / RTX PRO 6000 Blackwell
- NVIDIA V100
- DGX / HGX systems
- GPU servers + complete AI workstations
- NVLink / NVSwitch / baseboard hardware (sold with compute packages)

## The requested per-record schema

```json
{
  "partner_transaction_reference": "pseudonymous string",
  "transaction_date": "YYYY-MM or YYYY-MM-DD if permitted",
  "asset_type": "GPU | GPU_SERVER | DGX_HGX | WORKSTATION | COMPONENT",
  "manufacturer": "NVIDIA",
  "model": "string",
  "form_factor": "PCIE | SXM | SYSTEM | UNKNOWN",
  "memory_configuration": "string or null",
  "quantity": 1,
  "condition_class": "TESTED | REFURBISHED | AS_IS | PULL | UNKNOWN",
  "test_status": "string or null",
  "system_configuration_summary": "string or null",
  "transaction_type": "DIRECT_BUYBACK | REMARKETING_SALE | AUCTION_SALE | UNKNOWN",
  "transaction_amount_usd": "number or band if required",
  "amount_disclosure_type": "EXACT | RANGE | INDEXED | REDACTED",
  "geography": "broad region only",
  "rights_permission": {
    "internal_comp_analysis": true,
    "customer_report_derivative_use": false,
    "public_aggregate_use": false,
    "eval_pair_derivative_use": false,
    "training_use": false
  }
}
```

**Start restrictive. Earn wider use through signed agreement.**

## The doctrine guards that ride with every ITAD record

Even after we receive the data, the comp foundry enforces:

1. `partnership_status` must be `IN_CONVERSATION` or better before
   any observation can join a comp set
2. `rights_status` must not be `AGREEMENT_REQUIRED` (some agreement
   must exist)
3. `amount_disclosure_type` must be documented
4. `condition_class` must be set
5. Grade ceiling is **B** before validator review · only the validator
   may elevate to A after attribute-match + rights review
6. `training_eligible` and `public_display_eligible` default to false
   on every record · don't auto-flip even if the rights permission
   allows it

Tests in `app/tests/test_itad_doctrine.py` (15 of them) defend these.

## The outreach email

Reusable for Jawa, SellGPU, GreenTek, Alta, exIT, Re-Teck, Iron Mountain
with minor customization per the company-specific compute coverage line.

```
Subject: ITAD / GPU Partner Pilot · DefendableOS

Hello [Company Name] Team,

I'm building DefendableOS, a Proof of Value platform for high-value
assets, beginning with AI compute hardware: GPUs, AI workstations,
DGX/HGX systems, GPU servers and related infrastructure.

We are developing Defendable Compute to help asset owners and
remarketing partners organize hardware identity, configuration details,
testing and condition evidence, comparable-market support, validator
receipts and premium go-to-market packages before a resale or transfer.

Your work with used AI hardware and IT asset disposition stood out
because enterprise GPU and server transactions are exactly where
ordinary marketplace listings are least sufficient. For this asset
class, a meaningful comparable depends on model, form factor, memory,
configuration, test status, condition and documented transaction
context.

We would like to explore a small partnership pilot built around
permissioned, anonymized completed-transaction records or a controlled
CSV/feed export for AI hardware categories such as NVIDIA
H100/H200, A100, L40/L40S, RTX workstation GPUs, V100, DGX/HGX
systems and GPU servers.

DefendableOS would use any agreed data only within documented rights
controls. We would not republish raw partner transaction data or
assume model-training rights. Potential initial use cases include
internal comparable grading, privacy-safe derived Proof of Value
support and enhanced remarketing packages for high-value compute
assets.

In return, Defendable may be able to support your remarketing
workflows with evidence-backed asset pages, buyer-ready specification
and condition packages, validator-controlled records and premium
presentation for AI hardware inventory.

Would your team be open to a short conversation about an initial
50–250 record anonymized pilot or a co-developed remarketing proof
workflow?

Best,
Donovan Mackey
Founder, Swarm and Bee LLC
DefendableOS — Proof of Value
```

## Per-company customization hints

| Partner | Tweak the second paragraph to mention |
|---|---|
| **Jawa** | "GPU-native marketplace context and your anonymized sales data work" |
| **SellGPU** | "your bulk ITAD workflow and component-level transaction depth" |
| **GreenTek** | "DGX H100/A100 buyback specialization and deep-learning-server lane" |
| **Alta Technologies** | "R2v3-certified tested AI server inventory and full-rack disposition" |
| **exIT Technologies** | "DGX/HGX intake schema and NVLink/NVSwitch-aware configuration capture" |
| **Re-Teck** | "cloud and AI data-center remarketing posture" |
| **Iron Mountain** | "enterprise IT asset lifecycle management and value-recovery workflow" |
| **ServerMonkey** | "AI/ML/HPC GPU-server resale and configuration depth" |

## What we will NOT claim

- **NOT** "we have a partnership with [company]"
- **NOT** "we have an API connector to [company]"
- **NOT** sold-comp data is publicly available from [company]
- **NOT** training rights on raw partner data
- **NOT** that public buyback quotes are completed transactions
- **NOT** R2v3 / disposition certification language as a comp signal
  (matters for diligence · not for comp grade)

## Track outreach in the platform

Each partner's `contact_status` advances through:
`NOT_CONTACTED → EMAIL_SENT → RESPONSE_RECEIVED → IN_CONVERSATION
→ (NO_RESPONSE)`

And `partnership_status` advances:
`OUTREACH_READY → IN_CONVERSATION → PILOT_AGREEMENT
→ PRODUCTION_PARTNER → (DECLINED)`

Update them via the admin API (`POST /api/v1/admin/goods/itad-partners/{slug}/contact-status`)
when an outreach event happens.

## The bigger product

Once two or three partners say yes, the platform offer to ITAD firms
crystallizes into:

> **Defendable Compute for ITAD**
> Evidence-backed remarketing records for AI hardware disposition.
>
> ITAD Partner provides:
>   · permissioned anonymized transaction / feed data
>   · configuration and condition fields
>   · pilot inventory examples
>
> Defendable provides:
>   · proof-backed marketing pages
>   · buyer booklets
>   · validator-controlled asset records
>   · portfolio recovery dashboards
>   · optional branded remarketing packages

That's the moat: the public marketplaces help us see asking markets,
our own sellers give us first-party comps, and ITAD partners give us
**enterprise-grade AI hardware transaction intelligence**.
