# Product Thesis · Defendable Compute Proof Receipt v0.1

## The pain it addresses

Compute assets — GPUs, servers, edge appliances — change hands constantly via
rental platforms, resale marketplaces, IT asset disposition (ITAD) pipelines,
and direct enterprise transfers. At every handoff, the parties on both sides
need to know:

- Is this thing identified and authentic?
- Is it free of the prior tenant's workloads, residual data, and unintended
  background processes?
- Is it configured to a known operating baseline?
- Does it functionally work under load right now?
- Is there a tamper-resistant record of all of the above?

Today, that record either does not exist or is produced ad-hoc per platform
(Vast.ai test verdict, eBay seller claim, ITAD provider PDF). None of those
are durable, comparable, or independently verifiable.

## The thesis

A single, schema-anchored, hash-receipted artifact — the **Proof Receipt** —
captures the post-handoff verification of a compute asset and publishes its
evidence chain to a public ledger. The same receipt format serves every
handoff lane:

- **rental_readiness** (Vast.ai, RunPod, Coreweave-equivalents)
- **resale_readiness** (eBay, broker, direct sale)
- **disposition_intake** (ITAD providers, donation, scrapping)
- **fleet_audit** (in-place enterprise GPU inventory)

The receipt establishes the operational condition record. Any downstream
valuation, insurance, or certification process is a separate step layered on
top — but each of those layers benefits from having one canonical condition
record at the bottom.

## Why this is the first DefendableOS product

1. **Proven operational lifecycle.** The smash RTX 5090 post-renter cycle
   already executed end-to-end on 2026-05-25 with full evidence in hand. The
   product just captures what already happened.

2. **Schema-anchored.** Every field has a JSON Schema definition. Every
   artifact gets a sha256. Every receipt carries an explicit Tribunal verdict.
   This matches the existing DefendableOS books-and-records doctrine.

3. **Verifiable claim boundaries.** v0.1 deliberately does not claim
   valuation. It claims condition. That's the smallest publishable unit and
   the one with the least exposure.

4. **Direct lane to AIOV.** Once condition records exist at scale, AIOV
   compute valuation can layer on top with proven evidence chains —
   sequenced via `integrations/aiov_future_integration.md`.

5. **Existing infrastructure compatibility.** The receipt slots into the
   existing Tigris object storage layout (`streetledger/compute/...`),
   publishes to DefendableLedger, and follows the same hash-chain doctrine
   as the swarm-research and federal corpora.

## The non-thesis

The receipt **does not** establish, replace, or substitute for:

- A USPAP-compliant appraisal
- A manufacturer authentication
- A warranty determination
- A regulatory compliance attestation
- An insurance underwriting decision
- A legal title verification

It is the **operational condition record** that any of those processes can
inherit.

## Smallest publishable unit

The smallest publishable unit of value from this product is:

> "This asset, identified as X, was observed in condition Y, validated by
> tests Z, and any anomalies are recorded in W — captured at timestamp T,
> hashed at H, and signed by operator O."

That sentence is the receipt. Everything else is provenance.

## What v0.1 delivers

- Schemas (5 JSON Schema files) defining the data model
- Protocol documents codifying the smash lifecycle as a reusable script
- One real example (smash RTX 5090) demonstrating the receipt at field level
- CLI specification (no implementation) for the v0.2 build
- Integration lanes for Vast.ai today and AIOV next
- Object storage record layout for ledger publication

## What v0.2+ will deliver

- CLI implementation (read-only observation first, remediation with operator
  confirmation second)
- DefendableLedger publisher integration (using the existing GitHub Contents
  API publisher pattern from PR #7 on defendableos)
- Vast.ai readiness-lane integration (capture pricing observations alongside
  condition records)
- AIOV future-integration: bundle condition record + benchmark scores +
  market comparables into a separately-issued valuation opinion
