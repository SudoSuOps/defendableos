# Defendable Goods Intelligence · Architecture

The Goods Vault is DefendableOS's market memory. It turns three
different kinds of raw signal into a structured, scrutinable,
rights-controlled archive that AIOV and MarketReady can read from
without ever inheriting an unsupported claim.

## The thesis

> Most systems gather prices. Defendable grades whether the price
> deserves to matter.

Every price point that exists in the wild — a listing, a sale
record, a trend mention — has a different epistemic weight. The
Goods Vault encodes those differences as first-class types so the
platform never confuses them.

## The five layers

```
LAYER 1 · TREND DISCOVERY      → what is worth observing?      Brave LLM Context
LAYER 2 · RAW MARKET VAULT     → what was actually retrieved?  Tigris / MinIO
LAYER 3 · NORMALIZED GOODS DB  → what is the canonical thing?  CanonicalGood + GoodsIdentifier
LAYER 4 · COMP FOUNDRY         → which signals support value?  CompSet + CompSetMember
LAYER 5 · PAIR FACTORY         → what can we learn from this?  PairBatch + TrainingPair (rights-gated)
```

Two cross-cutting registries:

```
SOURCE RIGHTS LEDGER  →  permissions per artifact (training, public display, retention)
ARTIFACT REGISTRY     →  where every object lives in the 4-bucket vault
```

## The 4-bucket vault

| Bucket logical name | Purpose | Example contents |
|---|---|---|
| `defendable-private-evidence-prod` | Client / founder-owned evidence | Invoices, photos, receipts, deed JSON |
| `defendable-market-observations-prod` | Provider raw + normalized intel | Brave responses, eBay Browse responses |
| `defendable-derived-datasets-prod` | Pairs, eval packs, manifests | JSONL pair candidates, SHA256SUMS |
| `defendable-public-assets-prod` | Privacy-filtered approved exports ONLY | `/verify/{slug}/deed-public.json`, MarketReady media |

The `public_export_or_refuse()` function in `app/services/artifacts.py`
is a doctrine-enforced gate. It raises `PermissionError` if anything
other than a `PUBLIC_ASSETS`-classed artifact is requested through a
public path. **There is no exception path.**

## The 7 connectors

| Provider | Today | Future state |
|---|---|---|
| `BRAVE_LLM_CONTEXT` | Trend discovery context · grade E always | Stays at internal research |
| `EBAY_BROWSE` | Public active listing observations · grade ceiling C | Stays at internal research |
| `EBAY_INVENTORY` | `FUTURE_DISABLED` | Outbound MarketReady listings (after approval) |
| `SHOPIFY_FUTURE` | `FUTURE_DISABLED` | Outbound MarketReady listings |
| `CLIENT_UPLOAD` | Private evidence intake | Stays private |
| `FIRST_PARTY_TRANSACTION` | Confirmed sale evidence | Reviewable comp grade A/B |
| `LICENSED_TRANSACTION_DATA_FUTURE` | `FUTURE_DISABLED` | Reviewed sold-data ingestion |

The status reported by `/api/v1/admin/goods/connectors` is derived
from CONFIG + KILL SWITCHES · never from a stored value. The truth
is: keys present + live calls enabled + terms reviewed = READY.
Anything else returns the precise reason.

## The compute pilot

Initial commercial lane is `COMPUTE_HARDWARE`. The watchlist seeded
on day one:

```
GOOD-COMPUTE-NVIDIA-RTXPRO6000-BW-000001   linked to DOV-COMPUTE-000001
GOOD-COMPUTE-NVIDIA-RTX5090                watchlist only
GOOD-COMPUTE-NVIDIA-RTX4500-BW             watchlist only
GOOD-COMPUTE-NVIDIA-V100-32GB              watchlist only
GOOD-COMPUTE-AI-WORKSTATION-SYSTEM         watchlist only
GOOD-COMPUTE-DEFENDABLE-BOX                watchlist only
```

A draft comp set `COMPSET-DOV-COMPUTE-000001-v1` exists with status
`NOT_READY_FOR_VALUE_SUPPORT` and the canonical disclosure:

> *This comp set contains asking-market and/or discovery context
> only. No confirmed transaction support has been established.*

It will stay in that state until either:

1. A confirmed `FIRST_PARTY_TRANSACTION` is uploaded with a verified
   evidence manifest, or
2. A licensed transaction data feed is reviewed, terms-approved, and
   enabled (FUTURE_DISABLED today).

## Future expansion

The schema is class-agnostic. Adding a new goods class (luxury,
collectibles, CRE) requires:

1. Adding the enum value to `GoodsClass` and the matching enum in
   the next Alembic migration.
2. Adding canonical-goods seed entries.
3. Adding category-specific connectors (e.g., RealReal API for
   luxury, MLS feed for CRE).

The core invariants — trend ≠ comp, listing ≠ sale, rights gate
before training, public export only via `PUBLIC_ASSETS` artifacts —
do not change.

## File map

```
services/api/app/models/goods.py                  15 models · 24 enums
services/api/alembic/versions/0002_*.py           clean additive migration
services/api/app/services/artifacts.py            ArtifactRegistry + 4-bucket vault
services/api/app/services/comp_foundry.py         grading + RULE 1..6
services/api/app/services/pair_factory.py         pair candidates + rights gate
services/api/app/services/connector_registry.py   status + terms + live-call gate
services/api/app/services/seed_goods.py           idempotent watchlist seed
services/api/app/tests/test_goods_doctrine.py     20 boundary tests
docs/GOODS_INTELLIGENCE_ARCHITECTURE.md           this file
docs/OBJECT_STORAGE_POLICY.md                     bucket boundaries
docs/COMP_QUALITY_DOCTRINE.md                     A-E grading
docs/CONNECTOR_CONFIGURATION.md                   env vars + statuses
```
