# Compute Utility Score · Standard

A "useful AI compute" framework cannot score every asset on the
same axes. A Jetson Orin Nano and an RTX PRO 6000 Blackwell are
not the same kind of work. The Compute Utility Score (CUS) is
the doctrine that prevents the platform from comparing them on
incompatible axes.

## Doctrinal premise

> Different tiers of compute do different kinds of useful work.
> The score for an edge device is not the score for a workstation
> is not the score for a rack node. Each tier has its own scoring
> framework and own evidence requirements.

The score is **never** a single number that ranks all compute
together. The score is a **per-tier card** with workload-aware
components.

## Three score families · one standard

| Family | Applies to | Anchor question |
|---|---|---|
| **Edge / Local Utility Score** | E0-E2 (edge devices) | Does this device run real workloads in real environments at honest power? |
| **Workhorse Utility Score** | E3-E5 (consumer + workstation GPU rigs · CPU servers) | Does this asset earn revenue, run important local AI, or hold redeployable value? |
| **Institutional Utility Score** | E6-E7 (premium workstation + rack tier) | Is this asset a defendable production deployment with operating history? |

## Scoring components per family

### Edge / Local Utility Score (E0-E2)

| Component | Weight | Evidence basis |
|---|---|---|
| Workload test receipt present | 0.30 | first-party benchmark JSON · timestamp · SHA-256 |
| Power-envelope observation | 0.15 | nominal TDP + measured wattage when captured |
| Deployment-context attestation | 0.15 | operator-attested "running in [described context] for N days" |
| Privacy / offline benefit documented | 0.10 | air-gap suitability noted · local-only inference path described |
| AI acceleration spec confirmed | 0.10 | manufacturer published TOPS verified against firmware/runtime |
| Operating cost honesty | 0.10 | $/month at observed power × local kWh |
| Maintenance / runtime stability | 0.10 | uptime over a tracked window |

Total: 1.00 · `CUS_EDGE_v1`

### Workhorse Utility Score (E3-E5)

| Component | Weight | Evidence basis |
|---|---|---|
| Rental signal evidence | 0.20 | `VAST_PUBLIC_LISTING_RATE` snapshots or first-party rental receipts |
| Local AI capability evidence | 0.20 | largest model run · tokens/sec captured · quantization documented |
| First-party operating receipts present | 0.15 | rental receipts · occupancy history · workload uptime |
| Marketplace liquidity context | 0.10 | observed comps · days-on-market context · NEVER ranked above receipts |
| Power + thermal envelope captured | 0.10 | TDP + measured wattage + cooling notes |
| Configuration completeness | 0.10 | CPU + RAM + storage + network present alongside the GPU |
| Operator-attested deployment history | 0.10 | "deployed for N months in role X" |
| Redeployment optionality | 0.05 | path to E1-E2 redeployment documented · sister-lane fit |

Total: 1.00 · `CUS_WORKHORSE_v1`

### Institutional Utility Score (E6-E7)

| Component | Weight | Evidence basis |
|---|---|---|
| Defendable Deed issued + published | 0.25 | DDEED record with verify URL · ENS path noted |
| Operating-history receipts | 0.20 | uptime · workload class · training/inference receipts |
| Premium configuration validated | 0.15 | WRX90 · ThreadRipper PRO · ECC memory · validated power · inspection notes |
| Workload-class evidence | 0.15 | training-capable · multi-GPU coordination · NVLink/PCIe topology |
| Operating-cost honesty | 0.10 | $/month at observed power · cooling/colo cost when applicable |
| Configuration completeness | 0.10 | CPU + RAM + storage + network + chassis + PSU + cooling |
| Redeployment / resale optionality | 0.05 | path to secondary buyer or redeployment documented |

Total: 1.00 · `CUS_INSTITUTIONAL_v1`

## The score is a card · not a number

Each score outputs a card that shows the components, not just the
total. The card is the value · the number is shorthand.

```
Compute Utility Score · WORKHORSE (CUS_WORKHORSE_v1)
Subject: RTX 3090 Founders Edition · 24 GB · Operator workstation rig

  Rental signal evidence ........... 0.14 / 0.20
    Captured: 8 VAST_PUBLIC_LISTING_RATE snapshots
    Missing: first-party rental receipts

  Local AI capability evidence ..... 0.18 / 0.20
    Captured: Llama-3-13B Q5 at 8K ctx · 24 t/s

  First-party operating receipts ... 0.00 / 0.15
    Captured: none yet · EVIDENCE_INCOMPLETE

  Marketplace liquidity context .... 0.07 / 0.10
    Captured: 12 active listings observed in last 7 days

  Power + thermal envelope ......... 0.08 / 0.10
    Captured: 350W TDP · measured peak 340W under load

  Configuration completeness ....... 0.09 / 0.10
    Captured: 13900K · 128GB DDR5 · 2TB NVMe · 10GbE

  Operator-attested deployment ..... 0.05 / 0.10
    Captured: "18 months in workstation role"

  Redeployment optionality ......... 0.04 / 0.05
    Captured: fits E2 local AI inference role · documented

Total: 0.65 / 1.00 · EVIDENCE_INCOMPLETE on rental receipts
Recommendation: capture VAST_FOUNDER_RENTAL_RECEIPT before upgrading
                to HOLD_AND_RENT recommendation
```

## What the score is NOT

- The score is **not** a price.
- The score is **not** a rental yield projection.
- The score is **not** a rank against other asset classes.
- The score is **not** transferable to a buyer's expected ROI.
- The score is **not** static · evidence ages out and scores degrade.

## What the score IS

- A defendable, evidence-backed snapshot of the asset's documented
  usefulness in its class.
- A diagnostic that tells the operator exactly what evidence is
  missing to upgrade the recommendation.
- A versioned record · `CUS_<FAMILY>_v<n>` · so historic scores
  remain valid as the doctrine evolves.

## Evidence-aging rule

Captured evidence carries a freshness clock:

| Evidence type | Freshness window |
|---|---|
| Workload benchmark receipt | 180 days |
| Rental rate snapshot | 30 days |
| Rental receipt | 365 days |
| Occupancy history | 90 days rolling |
| Operating cost observation | 90 days |
| Marketplace liquidity snapshot | 30 days |
| Configuration inventory | 365 days |

When evidence ages out · the corresponding score component decays
to `EVIDENCE_STALE` and the operator gets a refresh request.

## Service-boundary enforcement

Forthcoming · `services/api/app/services/compute_utility_score.py`:

```python
class ComputeUtilityScoreError(Exception):
    """Raised when scoring would violate doctrine."""

def score_edge(...) -> EdgeScoreCard:
    if not workload_test_receipt_present:
        return EdgeScoreCard(
            total=0.0,
            status="EVIDENCE_INCOMPLETE",
            missing=["workload_test_receipt"]
        )
    # ...

def score_workhorse(...) -> WorkhorseScoreCard: ...
def score_institutional(...) -> InstitutionalScoreCard: ...
```

Doctrine guards refuse to mix families · refuse to publish scores
above 0.50 without a first-party evidence receipt · refuse to
inherit a score across asset replacements.

## Related docs

- `COMPUTE_ASSET_TAXONOMY.md` · the E0-E7 ladder the score families map to
- `COMPUTE_UTILIZATION_INDEX_SPEC.md` · how scores aggregate into the index
- `EDGE_AI_COMPUTE_LANE.md` · the Edge score family's primary lane
- `CPU_AND_SMALL_GPU_UTILITY_LANE.md` · spans Edge and Workhorse families
- `SECOND_LIFE_COMPUTE_STRATEGY.md` · scoring older hardware honestly
- `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` · primary source for the Rental
  Signal Evidence component
