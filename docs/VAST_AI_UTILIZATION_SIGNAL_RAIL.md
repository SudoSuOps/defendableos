# Vast.ai · Compute Utilization Signal Rail

Vast.ai becomes a core Compute utilization intelligence rail.
Carefully · honestly · with strict claim discipline. Listing
rates are NOT resale value. Availability is NOT occupancy. Public
visibility is NOT booked revenue. First-party rental receipts ARE
operating evidence the platform can issue claims from.

## A · Strategic role

Vast.ai gives Defendable Compute an observable signal for:

- Which GPUs are being offered for rent
- At what rates the public market is asking
- Which apparent market supply exists for which categories
- Where founder account evidence exists · which owned assets are
  actually producing revenue

This is critical because a useful compute asset may have:

- Resale value (what a buyer would pay)
- Rental value (what the asset earns while held)
- Redeployment value (utility from moving the asset to another role)
- Edge / local deployment value (utility from offline / private use)
- Part-out value (sum of components > whole asset)

DefendableOS compares these paths rather than assuming sale is
always the correct exit. Vast.ai is the rail that makes the rental
column real.

## B · Signal classes

Every Vast.ai-derived observation MUST carry one of these classes
explicitly. The platform refuses to roll non-confirmed classes into
confirmed-sale claims · same doctrine that protects the rest of the
SignalClass system.

| Signal Class | Example | What it proves | What it does NOT prove |
|---|---|---|---|
| `VAST_PUBLIC_LISTING_RATE` | observed market hourly asking/rental rate | current public market observation | actual paid rental or occupancy |
| `VAST_PUBLIC_SUPPLY_OBSERVATION` | number/category of visible offerings if observable | apparent marketplace supply | demand or booked utilization |
| `VAST_FOUNDER_MACHINE_LISTING` | founder's listed machine and advertised rate | owned asset listed for rental | paid revenue |
| `VAST_FOUNDER_RENTAL_RECEIPT` | completed rental or payout record | actual paid utility evidence | resale market value |
| `VAST_FOUNDER_OCCUPANCY_HISTORY` | rental duration / booked time | actual utilization history | future guaranteed utilization |
| `VAST_WORKLOAD_TEST_RECEIPT` | self-test, benchmark or validation receipt | operational / rental readiness | market demand |
| `VAST_DERIVED_YIELD_ANALYSIS` | modeled gross/net annualized yield from captured receipts | analysis based on disclosed inputs | guaranteed future earnings |

**Doctrine layer note:** Of these 7 classes, only
`VAST_FOUNDER_RENTAL_RECEIPT` and `VAST_FOUNDER_OCCUPANCY_HISTORY`
count as **first-party operating evidence**. They are eligible to
contribute to a `FIRST_PARTY_DEFENDABLE_SALE`-class signal on the
asset's deed if the operator confirms the receipt represents actual
paid utility. All other classes are signal-only.

Proposed `SignalClass` enum additions (next session · schema work):

```
VAST_PUBLIC_LISTING_RATE       NOT_CONFIRMED_SALE
VAST_PUBLIC_SUPPLY_OBSERVATION NOT_CONFIRMED_SALE
VAST_FOUNDER_MACHINE_LISTING   NOT_CONFIRMED_SALE
VAST_FOUNDER_RENTAL_RECEIPT    CONFIRMED_FIRST_PARTY_UTILITY (new sub-class)
VAST_FOUNDER_OCCUPANCY_HISTORY CONFIRMED_FIRST_PARTY_UTILITY
VAST_WORKLOAD_TEST_RECEIPT     OPERATIONAL_READINESS_RECEIPT
VAST_DERIVED_YIELD_ANALYSIS    DERIVED_ANALYSIS_WITH_RECEIPTS
```

Until those land · this doc IS the contract.

## C · Workhorse GPU watchlist

Vast.ai intelligence covers more than flagship GPUs. The watchlist:

| Card | VRAM | Why it matters |
|---|---|---|
| RTX 3090 / 3090 Ti | 24 GB | the workhorse rental thesis · 24 GB still runs serious local models · proven secondary-market rental demand · see Section D below |
| RTX 4090 | 24 GB | the previous flagship · still in heavy rental rotation · large supply |
| RTX 5090 | 32 GB | the current consumer flagship · GDDR7 · Blackwell architecture |
| RTX A5000 / A6000 | 24 / 48 GB | workstation cards · steady inference + render workloads · longer service life expectation |
| RTX 4500 Blackwell | 32 GB | workstation Blackwell · where observed |
| RTX PRO 6000 Blackwell | 96 GB | premium workstation accelerator · institutional tier |
| A100 | 40 / 80 GB | enterprise training · still extremely active in rental · multi-year residual |
| H100 / H200 | 80 / 141 GB | current enterprise standard · highest rental rates · gated supply |
| T4 | 16 GB | low-power inference workhorse · longstanding rental presence |
| V100 | 16 / 32 GB | second-life enterprise · still useful for many inference workloads |

Other cards are added only when marketplace visibility and utility
justify them.

### Required observable fields (when lawfully visible on public listings)

- memory size
- public rate observation (asking $/hr)
- timestamp (UTC ISO-8601)
- supply / availability indicator if shown
- host requirements (verified host badge · regions · uptime claim)
- reliability / verification indicators where observable
- machine configuration context (CPU class · RAM · NVMe · network speed)
- suitability for local inference / fine-tuning / rendering / enterprise
  workload **where evidence supports it**

## D · RTX 3090 workhorse thesis

> The RTX 3090-class card is a critical Second-Life Compute workhorse
> because its 24 GB VRAM can remain useful for local AI and rental
> workloads even after newer consumer generations ship.

**However · do NOT state rental rate, occupancy or expected earnings
as permanent truth.**

Instead the platform:

1. **Captures current Vast.ai public rate snapshots** with timestamp
   + source URL · stored as `VAST_PUBLIC_LISTING_RATE` observations
2. **Collects founder-owned rental receipts** when available · stored
   as `VAST_FOUNDER_RENTAL_RECEIPT`
3. **Compares purchase/resale basis against actual paid yield** when
   both inputs exist · produces `VAST_DERIVED_YIELD_ANALYSIS`
4. **Uses the record to determine** whether `HOLD/RENT`, `SELL`,
   `REDEPLOY`, or `REVIEW` is the most defensible next action

The RTX 3090 becomes the flagship example of a **prior-generation
asset retaining productive value through utilization evidence**.

A `Defendable RTX 3090 Workhorse Utilization Record` is the first
proof case · using founder-owned hardware where operating data is
already accessible.

## E · Rental yield analysis standard

Required fields for any `VAST_DERIVED_YIELD_ANALYSIS`:

| Field | Source class | Required? |
|---|---|---|
| asset model | private spec | yes |
| VRAM | private spec | yes |
| host system configuration | private spec | yes |
| purchase cost | private operator input (may be redacted) | optional |
| listed rental rate | `VAST_FOUNDER_MACHINE_LISTING` | yes (when listed) |
| actual paid rate | `VAST_FOUNDER_RENTAL_RECEIPT` | yes (for yield claim) |
| utilization period | `VAST_FOUNDER_OCCUPANCY_HISTORY` | yes |
| gross earnings | sum of `VAST_FOUNDER_RENTAL_RECEIPT` values | yes |
| platform fees (if available) | receipt detail | preferred |
| electricity assumption | operator input with source · or measured | yes |
| power cap / measured wattage | operator input or device telemetry | yes |
| cooling / operating cost notes | operator input | preferred |
| downtime / maintenance notes | operator input | preferred |
| derived monthly gross yield | computed from above | yes |
| derived net yield | computed when ALL required inputs exist | conditional |
| sale-value comparison | only when comp evidence exists | conditional |
| recommendation status | `HOLD/RENT` / `SELL` / `REDEPLOY` / `REVIEW` / `EVIDENCE_INCOMPLETE` | yes |

**Hard rule:** No ROI or yield claim may be issued without source-tagged inputs.

Example deficient analysis:

```json
{
  "asset_model": "RTX 3090 Founders Edition",
  "vram_gb": 24,
  "evidence_inputs": {
    "vast_public_listing_rate": "$0.21/hr (2026-05-22T18:00Z, vast.ai)",
    "vast_founder_machine_listing": null,
    "vast_founder_rental_receipt": null,
    "vast_founder_occupancy_history": null
  },
  "recommendation_status": "EVIDENCE_INCOMPLETE",
  "explanation": "Public listing-rate observation only. No founder operating receipts captured. Cannot model yield. Next step: ingest founder Vast.ai rental receipts via private upload."
}
```

The platform produces this output honestly · the operator sees
exactly what's missing.

## F · Connector status proposal

`VAST_AI` as a new `ProviderName` (next-session schema work). Connector
definition:

```python
{
    "provider_name": ProviderName.VAST_AI,
    "connector_purpose": (
        "Vast.ai · GPU rental marketplace utilization signal · public "
        "listing rates + supply observations + founder operating "
        "receipts when uploaded · NEVER a resale-value source"
    ),
    "default_terms": TermsReviewStatus.REVIEWED_INTERNAL_RESEARCH_ONLY,
    "status_fn": lambda: ProviderStatus.READY,  # manual analyst + founder upload workflow
}
```

Until the enum entry lands, Vast.ai data is captured via manual
analyst workflow into existing tables · `StoreIntelligenceObservation`
for public-listing observations (provider="VAST_AI"), and
`ConnectedStoreOutcome` for founder rental receipts (provider="VAST_AI"
in a new sub-classification).

## G · Claim discipline · what the platform says publicly

| Allowed | Forbidden |
|---|---|
| "Vast.ai rate snapshot · $0.21/hr · 2026-05-22T18:00Z · source: vast.ai" | "RTX 3090 earns $X/hr" without receipts |
| "Founder operating receipt · 412 hours rented in last 30 days · $86.52 gross" | "Always rented" without occupancy history |
| "Derived yield from captured inputs · $X/month gross · before electricity" | "$X profit per month" without electricity + fees inputs |
| "Public market context shows N units offered in [region]" | "High demand for this card" without comparative receipts |

## H · How this feeds the Compute Beachhead

Vast.ai signal flows into 3 of the 6 product tiers:

- **Workhorse Utilization Record** (RTX 3090 lane) · the primary use
- **Premium Compute Proof of Value** (5090 · 4500 Blackwell · PRO 6000)
  · auxiliary rental-value context
- **Compute Node / MarketReady Package** · operating-rental annual
  earnings as a buyer talking point

For the RTX 3090 specifically · the first paid customer for this
product tier could be a founder operating a small rental fleet who
needs evidence to support a `HOLD vs SELL` decision · the platform
delivers the analysis for $199 with founder-captured receipts.

## Related docs

- `COMPUTE_BEACHHEAD_30_DAY_PLAN.md` · the Workhorse Utilization Record product
- `SECOND_LIFE_COMPUTE_STRATEGY.md` · why 3090 matters
- `COMPUTE_ASSET_TAXONOMY.md` · the E0 → E7 ladder including E4 workhorse
- `COMPUTE_UTILIZATION_INDEX_SPEC.md` · future internal index this feeds
