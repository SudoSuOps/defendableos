# Comp Quality Doctrine · the truth controls behind every value claim

DefendableOS treats price evidence as TYPED. Every artifact knows
what it is, what it can support, and what it can never claim. This
file is the canonical statement of those rules · the code in
`app/services/comp_foundry.py` enforces them at the service
boundary, and `app/tests/test_goods_doctrine.py` is the canary.

## The three signal kinds

```
TREND SIGNAL          discovery context only           grade E always
PUBLIC ACTIVE LISTING asking-market context only       grade ceiling C
CONFIRMED TRANSACTION supports value claim after review grade A or B
```

A LISTING IS NEVER A SALE. A TREND IS NEVER A COMP.

## Grade definitions

| Grade | Meaning | Allowed support |
|---|---|---|
| **A** | Confirmed transaction with full evidence manifest AND high attribute match | Final value, after validator review |
| **B** | Authorized transaction with review limitations | Draft value, with limitations |
| **C** | Active listing with high identity match | Asking-market context only |
| **D** | Weak listing match | Discovery only |
| **E** | Trend signal | NEVER comp evidence |

## The 6 rules

**RULE 1** · A `TrendSignal` can NEVER enter a comp set as value
support. Always grade E. Always inclusion_reason
`DISCOVERY_ONLY`. Enforced in `comp_foundry.add_trend_signal()`.

**RULE 2** · A `PUBLIC_ACTIVE_LISTING` must carry:
- `transaction_confirmed = False`
- `price_type = ASKING_PRICE`
- `quality_grade` ceiling = C
- `limitations` includes `ASKING_PRICE_NOT_CONFIRMED_TRANSACTION`
- `limitations` includes `REQUIRES_VALIDATOR_REVIEW`

The service raises `CompFoundryError` if any field violates. Tests
`test_comp_foundry_refuses_a_on_listing` and friends are the canary.

**RULE 3** · A confirmed transaction requires:
- `source_type ∈ {CLIENT_PROVIDED_SALE_RECEIPT, FOUNDER_OWNED_VERIFIED_SALE, AUTHORIZED_MERCHANT_TRANSACTION, LICENSED_TRANSACTION_DATA, FIRST_PARTY_TRANSACTION}`
- `transaction_status = CONFIRMED_WITH_EVIDENCE`
- `evidence_manifest_id is not None`

`comp_foundry.add_transaction_evidence()` refuses anything else.

**RULE 4** · A comp set with zero confirmed transactions OR only
Grade C/D/E entries MUST resolve to `NOT_READY_FOR_VALUE_SUPPORT`
with the canonical disclosure:

> *This comp set contains asking-market and/or discovery context
> only. No confirmed transaction support has been established.*

This text is in `comp_foundry._NOT_READY_DISCLOSURE`. Do not edit
it without updating downstream UI and doctrine docs.

**RULE 5** · A comp set never becomes AIOV-final-value-ready
automatically. The upgrade requires explicit human approval.
`comp_foundry.approve_for_limited_use()` is `NotImplementedError`
by design until that workflow ships. The seam exists so callers
can grep for it.

**RULE 6** · Source rights must exist before any pair or
derivative export. `SourceRightsRecord.training_eligible` defaults
to `False`. `TrainingPair.use_class` defaults to
`CANDIDATE_ONLY`. `pair_factory.assert_training_eligible()` is
the gate every exporter must call.

## What "not ready" looks like to a buyer

The public verify page for a draft asset shows:

- Record status: `DRAFT_REVIEW_RECORD`
- Validator status: `PASSED_FOR_DRAFT_PACKAGING`
- Value status: `WITHHELD_PENDING_VALIDATOR_REVIEW` or
  `OPERATOR_ASK_PRICE` (operator claim only)
- ENS status: `RESERVED_NOT_ISSUED`

A comp set is BEHIND that doctrine band. Its job is to feed AIOV
draft inputs and MarketReady positioning context — never to
authorize a public value claim by itself.

## Future grades and states

- **A+** (proposed) · confirmed transaction + audited rent roll +
  appraiser review. For STNL deals at scale.
- **REVIEWED_AND_DISCLOSED** value display state · when validator
  passes a confirmed-sale-backed range. Unlocked by eBay Marketplace
  Insights or licensed data approval.

These do not exist yet. Today's defaults stay conservative.
