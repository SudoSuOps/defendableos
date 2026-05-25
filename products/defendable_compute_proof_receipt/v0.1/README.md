# Defendable Compute Proof Receipt · v0.1

> A benchmark-backed, hash-receipted record establishing that a compute asset is
> identified, visible to the runtime, clear of unintended workloads, configured to
> an operating baseline, and passes functional/stress validation — ready for
> rental, resale, disposition, or later AIOV value analysis.

## What this is

A **Proof Receipt**. Not an appraisal. Not a value opinion. Not a certification
issued by an accredited body.

This v0.1 product takes a single observed lifecycle on a real GPU host — the
post-renter verification of the smash RTX 5090 on 2026-05-25 — and turns it
into a repeatable, schema-anchored, hash-receipted artifact that compounds
into the books-and-records substrate DefendableOS publishes on
DefendableLedger.

## What this is NOT (claim boundaries)

This artifact does not establish, imply, or assert:

- Certified appraisal of compute value
- Guaranteed market value
- Insurance acceptance
- Lender acceptance
- Legal ownership proof
- Formal accreditation of any kind
- Manufacturer warranty status
- Compliance with any specific regulatory framework

Those are separate determinations that require separate evidence chains. The
Proof Receipt is the *operational condition* record that any of those later
determinations may be built on.

## Authorized vocabulary

The artifacts produced by this product use only the following terms:

- **Proof Receipt**
- **Validated Compute Condition Record**
- **Rent-Ready Evidence Package**
- **Benchmark-Backed Asset Record**

The terms "appraisal", "valuation", "certified", "guaranteed", or "warranted"
must not appear in any field of any artifact produced by this product without
a separate external attestation.

## Workspace layout

| dir | purpose |
| --- | --- |
| `doctrine/` | product thesis, terminology + claim boundaries, Tribunal gate |
| `schemas/` | 5 JSON Schema files defining the data model |
| `examples/` | smash RTX 5090 example proof receipt (JSON + markdown) |
| `protocol/` | post-rental, benchmark, evidence-capture, failure-taxonomy protocols |
| `cli_spec/` | future CLI specification (no execution implemented in v0.1) |
| `integrations/` | Vast.ai readiness lane, AIOV future, object-storage layout |
| `receipts/` | sha256 manifest + build manifest |
| `reports/` | founder-grade product memo |

## Doctrine

`Tribunal begins before training. No proof, no honey.`

This product is a Tribunal artifact. Each receipt carries an explicit tribunal
verdict (`HONEY` / `JELLY` / `PROPOLIS`) and an explicit `claim_boundaries`
block stating exactly what the receipt does and does not establish.

## Cross-references

- Kimi intake findings supporting this product: `../../../research/kimi_intake/2026-05-25/`
- Existing benchmark spec (extends): `../../../docs/DEFENDABLE_COMPUTE_BENCH.md`
- Existing work-unit schema (compatible): `../../../docs/DEFENDABLE_WORK_UNIT_SCHEMA.md`
- AIOV future integration target: see `integrations/aiov_future_integration.md`

## Status

- **Schema version:** v0.1
- **Build status:** local · not pushed to GitHub
- **Operational example:** 1 real host (smash RTX 5090, 2026-05-25 post-rental cycle)
- **CLI implementation:** specification only · no hardware execution
