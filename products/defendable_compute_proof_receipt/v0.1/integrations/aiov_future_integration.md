# AIOV Future Integration · v0.1 Forward Pointer

> The Defendable Compute Proof Receipt v0.1 is a **condition record**, not a
> valuation. AIOV (sovereign opinions of value) is a separate downstream
> product that will consume Proof Receipts as inputs. This document defines
> the contract between them so v0.1 receipts are AIOV-ready when the
> valuation layer ships.

## v0.1 does not produce value opinions

The receipt schema deliberately omits any value-asserting field. There is
no `estimated_value_usd`, `market_value`, `appraisal_opinion`, or
`valuation_basis` block in the v0.1 receipt.

This is enforced by:
- Banned vocabulary list in `doctrine/terminology_and_claim_boundaries.md`
- Receipt linter (`defendable-compute receipt --lint`)
- Tribunal gate refusing HONEY if `CLAIM_EXCEEDS_EVIDENCE` is detected

## How AIOV will consume Proof Receipts (future)

The AIOV product, when built, will:

1. **Index Proof Receipts by asset_id.** Multiple receipts per asset_id
   build a longitudinal condition history.
2. **Extract structured features** from the receipt:
   - `asset_identity.model`
   - `asset_identity.vram_total_mib`
   - benchmark results per `test_scope`
   - service-state pass/fail history
   - findings frequency and severity over time
   - operating baseline deviations
3. **Layer comparable evidence** (Vast.ai pricing snapshots, eBay sales,
   ITAD broker quotes, manufacturer MSRP, secondary-market listings)
4. **Issue a separate AIOV value opinion** referencing one or more
   Proof Receipts as inputs.

The AIOV value opinion is its OWN artifact with its OWN schema, its OWN
operator, and its OWN claim boundaries. It is not a field on the Proof
Receipt.

## Receipt → AIOV linkage fields

These fields in the v0.1 schema are already AIOV-ready:

| field | how AIOV uses it |
| --- | --- |
| `asset_identity.asset_id` | primary index key |
| `asset_identity.model` | dictionary lookup for OEM benchmark / MSRP |
| `asset_identity.vram_total_mib` | model fit / size tier |
| `benchmark_validation_results[].test_origin = OEM/platform_remote/third_party` | weight in confidence model |
| `benchmark_validation_results[].observed_output` | numeric features (TFLOPS, latency, etc.) |
| `tribunal_verdict.verdict` | HONEY-only receipts qualify for HIGH-confidence AIOV |
| `created_at` + `observed_at` | recency adjustment |
| `ledger_publication.record_sha256` | verifiability anchor |

## AIOV will issue its own claim boundaries

When the AIOV product ships, its artifacts will carry their own
`claim_boundaries`:

```json
{
  "claim_boundaries": {
    "scope": "value_opinion_at_market_snapshot",
    "establishes": [
      "estimated_market_value_range_under_named_methodology",
      "comparable_set_referenced",
      "valuation_methodology_disclosed"
    ],
    "does_not_establish": [
      "guaranteed_resale_price",
      "appraisal_under_uspap_unless_separately_endorsed",
      "insurance_acceptance",
      "lender_acceptance",
      "compliance_with_any_specific_accounting_standard"
    ]
  }
}
```

Note the explicit `unless_separately_endorsed` carve-out for USPAP. AIOV by
default is a sovereign opinion of value, not an accredited appraisal.

## Sequencing

| version | ships | scope |
| --- | --- | --- |
| **v0.1 (this)** | now | condition-only Proof Receipt; no value claim |
| v0.2 | next | CLI implementation; DefendableLedger publication |
| v0.3 | next next | Vast.ai pricing capture (still condition-only, but pricing context added) |
| AIOV v0.1 | separate ship | first AIOV value opinion artifact, consuming Proof Receipts |

## Hard rule

**No version of the Defendable Compute Proof Receipt ever asserts value.**
The product family's split is permanent: condition records and value
opinions are two separate artifacts, two separate operators, two separate
claim boundaries.

This split protects both products: a buyer who disputes the value opinion
can still rely on the condition record. A renter who renews the listing
gets a fresh condition record without needing a fresh valuation.

## What this means for the Kimi-intake AIOV opportunities

The Kimi intake `04_strategy/aiov_compute_market_opportunities.md` lists
five product candidates derived from `dim05_asset_compute`. Of those:

| Kimi candidate | belongs in |
| --- | --- |
| Compute appraisal deed intake schema | **AIOV v0.1** (separate product) |
| GPU benchmark-to-value receipt | **AIOV v0.1** (consumes a Proof Receipt + adds value layer) |
| ITAD secondary-market signal registry | **AIOV v0.1** (price-side context, not condition) |
| Vast.ai demand capture module | **DCPR v0.3** (price-side observation, condition-context only) |
| Object-storage appraisal record structure | **shared infrastructure** (see `object_storage_record_layout.md`) |
| Defendable Box edge intake workflow | **DCPR v0.2** (extension of `use_case=fleet_audit`) |
| Verified comps booklet generator | **AIOV v0.1** (composes Proof Receipt + market context) |
| Proof of Compute scoring receipt | **DCPR v0.2** (sustained-load extension) |
| Federal demand intelligence registry expansion | separate product family |

This split lets DCPR v0.1 ship now without entangling itself in valuation
disputes.
