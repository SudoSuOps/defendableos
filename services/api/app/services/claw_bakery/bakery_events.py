"""Claw Bakery event ledger / outbox.

Events emitted by the bakery pipeline:
  · clawcheck.intake.completed
  · clawcheck.snapshot.computed
  · clawcheck.validator.review_requested
  · clawcheck.pair_candidate.created
  · clawcheck.receipt.generated
  · clawcheck.dataset_candidate.queued

Storage backend is the BakeryStore (filesystem or S3). Each event is
an immutable JSON artifact under claw-bakery/events/. A future iteration
may promote this to a Postgres outbox table for richer querying · the
JSON outbox is sufficient for the current contract (write + replay).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from app.services.claw_bakery.bakery_storage import BakeryStore, get_bakery_store


EventType = Literal[
    "clawcheck.intake.completed",
    "clawcheck.snapshot.computed",
    "clawcheck.validator.review_requested",
    "clawcheck.pair_candidate.created",
    "clawcheck.receipt.generated",
    "clawcheck.dataset_candidate.queued",
    "clawforge.candidate.generated",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_event(
    *,
    event_type: EventType,
    run_id: str,
    payload: dict[str, Any],
    store: BakeryStore | None = None,
) -> dict[str, Any]:
    """Write a single immutable event to the outbox.

    Returns the event envelope (event_id + sha256 + key location). No
    secret-bearing payload is logged · only the envelope. Callers must
    not put credentials or raw operator_attested_context into `payload`
    unless they have explicitly redacted it.
    """
    store = store or get_bakery_store()
    event_id = f"EVT-{uuid.uuid4().hex[:12]}"
    envelope = {
        "event_id": event_id,
        "event_type": event_type,
        "run_id": run_id,
        "created_at": _now(),
        "payload": payload,
    }
    artifact = store.append_event(event_id, envelope)
    return {
        "event_id": event_id,
        "event_type": event_type,
        "run_id": run_id,
        "sha256": artifact.sha256,
        "byte_size": artifact.byte_size,
        "key": artifact.key,
        "created_at": envelope["created_at"],
    }


def list_events(store: BakeryStore | None = None) -> list[str]:
    """List all event keys (admin/replay use only)."""
    store = store or get_bakery_store()
    return store.list_under("events")
