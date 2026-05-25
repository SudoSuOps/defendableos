# Terminology and Claim Boundaries · v0.1

## Authorized vocabulary

The artifacts produced by this product use only the following terms when
describing what the receipt establishes:

| term | meaning |
| --- | --- |
| **Proof Receipt** | The artifact produced by this product. A hash-receipted, schema-anchored record of an asset's operational condition at a specific timestamp. |
| **Validated Compute Condition Record** | Synonym for Proof Receipt; emphasizes the condition (not value) scope. |
| **Rent-Ready Evidence Package** | A bundle of receipt + supporting evidence formatted for a rental platform consumer (e.g., Vast.ai). |
| **Benchmark-Backed Asset Record** | A receipt where the validation step includes one or more functional/stress benchmarks. |

## Banned vocabulary in v0.1 artifacts

The following terms must NOT appear in any field of any artifact produced by
this product without a separate, external attestation:

| term | reason banned in v0.1 |
| --- | --- |
| appraisal | Implies USPAP or equivalent standards; requires accredited appraiser. |
| valuation | Implies a value opinion; v0.1 captures condition only. |
| certified | Implies third-party accreditation; v0.1 is first-party. |
| guaranteed | Implies a warranty/insurance backing. |
| warranted | Implies a manufacturer warranty determination. |
| insurance-backed | Implies an underwriting determination. |
| lender-accepted | Implies a financing-side acceptance. |
| legally proves | Implies a legal title or ownership determination. |
| accredited | Implies third-party accreditation body sign-off. |

The CLI must lint generated artifacts for these banned terms and refuse to
emit a receipt that contains them in any value field. Comments referencing
the bans (like this document) are allowed.

## Claim boundary block

Every Proof Receipt carries an explicit `claim_boundaries` block stating, in
positive terms, exactly what the receipt establishes:

```json
{
  "claim_boundaries": {
    "scope": "operational_condition_at_timestamp_only",
    "establishes": [
      "asset_identified_to_runtime",
      "no_unintended_workloads_at_timestamp",
      "configured_to_documented_operating_baseline",
      "passed_named_functional_and_stress_tests_at_timestamp"
    ],
    "does_not_establish": [
      "market_value",
      "appraisal_under_uspap_or_equivalent",
      "manufacturer_warranty_status",
      "insurance_underwriting_acceptance",
      "lender_acceptance",
      "legal_title_or_ownership",
      "accreditation_by_third_party_body",
      "fitness_for_any_specific_purpose_beyond_the_named_tests"
    ],
    "validity_window": "snapshot_at_observed_at_timestamp_only",
    "successor_records_supersede": true
  }
}
```

## Validity window

A Proof Receipt is valid **only at the timestamp it was generated**. It is a
snapshot. Any subsequent state change (new renter, driver update, hardware
swap, OS reinstall) invalidates the prior receipt as a current-state claim.
The prior receipt remains historically valid as a *past observation*.

The successor-records-supersede rule means: if a later receipt for the same
`asset_id` exists, downstream consumers (Vast.ai listing, ITAD intake, AIOV
appraiser) should prefer the latest receipt when evaluating current
condition.

## Identity privacy treatment

Hardware identifiers (GPU UUID, board serial, BMC serial, host MAC) are
sensitive in two ways:

1. Operationally — they can be used to track specific machines across
   rental platforms.
2. Commercially — they may be tied to ownership chains the operator does
   not wish to publish.

The schemas define a `serial_or_uuid` field with three privacy treatments:

| treatment | publication policy |
| --- | --- |
| `full` | The full identifier is published in the receipt. |
| `salted_hash` | A salted SHA-256 of the identifier is published; the salt is stored locally only. |
| `redacted` | The field is recorded as `"[redacted]"`; the original is held in operator-only evidence. |

Default for first-party operator receipts: `salted_hash`.
Default for renter / customer-facing receipts: `redacted`.

## Operator identity

Each receipt names the operator that generated it. Operator may be a human,
an agent, or a CI worker. The operator is the **first-party signer** — they
are claiming what is in the receipt. Liability for misstatement attaches to
the operator.

## Verification chain

Any party may independently verify a Proof Receipt by:

1. Fetching the receipt JSON from its published URL.
2. Fetching the named evidence artifacts via their `evidence_locator` URLs.
3. Recomputing the sha256 of each artifact and comparing to
   `artifact_hashes`.
4. Cross-checking the named benchmark outputs against any independently
   captured copies.

If any hash mismatches, the receipt is **invalid** and the consumer should
treat the asset as unverified.
