"""ComputeClaw · first revenue-facing DefendableOS claw.

Workflow:
  intake → MarketScout (eBay Browse observed asking-price evidence)
         → Normalizer (noise/accessory/parts exclusion · review-preserving)
         → BenchInspector (benchmark receipt attachment)
         → UtilitySignal (rental/income evidence attachment)
         → ValueComposer (draft AIOV Proof Pack · NEVER final · NEVER deed)
         → Validator review (out-of-band · required before deed eligibility)

Doctrine guarantees:
  · Active eBay listings are OBSERVED_ASKING_PRICE_EVIDENCE · NEVER sold comps
  · Final value opinion + deed issuance NEVER automated by this claw
  · Raw intake + raw eBay batches immutable · derived normalizations stored
    separately · exclusions preserved with reason codes
  · No client secrets or OAuth tokens ever written to artifacts
  · Operator-supplied utility claims marked unverified without receipt
"""
