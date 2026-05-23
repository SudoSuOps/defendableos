"""Claw Bakery · DefendableOS evidence + benchmark + pair refinery.

Public surface:
  · bakery_storage.BakeryStore     · raw-evidence immutable artifact writer
  · bakery_events.append_event     · outbox for downstream Tribunal review
  · pair_factory.create_pair_candidate · agent-domain pair-candidate model
  · clawforge.generate_synthetic_candidate · disabled-by-default synthetic forge

NONE of these may auto-train a production model, auto-issue a deed, or
auto-label a record as Honey. All training admission requires
Tribunal-approved label + consent + redaction · per doctrine.
"""
