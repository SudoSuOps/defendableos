"""MarketScout · eBay Browse → observed asking-price evidence for compute.

Wraps the existing eBay Browse client (services/api/app/integrations/ebay/
browse_api.py) but ALWAYS labels its output as OBSERVED_ASKING_PRICE_EVIDENCE
with transaction_verified=False. NEVER calls Marketplace Insights (that's
the separate sold-comp rail).

Per-observation pipeline:
  1. Browse search_item_summaries(q=<query>)
  2. For each result · normalizer.classify_title() decides INCLUDED/EXCLUDED
  3. Build observation record + normalization record
  4. Write both immutably to bakery vault (paths separated)
  5. SHA-256 receipt per record · per-batch manifest receipt

Kill switch: COMPUTECLAW_MARKET_OBSERVATION_ENABLED env var. Defaults
False · the service refuses to run unless explicitly enabled. This is
intentional · live eBay calls cost rate-limit budget and produce
storage growth · operator must opt in per-environment.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.claw_bakery.bakery_storage import (
    BakeryStore,
    bakery_key,
    get_bakery_store,
    safe_key_part,
)
from app.services.claw_bakery.bakery_events import append_event
from app.services.claw_bakery.receipts import generate_receipt
from app.services.compute_claw.normalizer import (
    build_normalization_record,
    classify_title,
)


_log = logging.getLogger("compute_claw.marketscout")


# Default disabled · operator must flip the env var to enable live calls.
def is_enabled() -> bool:
    return os.environ.get("COMPUTECLAW_MARKET_OBSERVATION_ENABLED", "false").lower() == "true"


class MarketScoutDisabled(RuntimeError):
    """Raised when MarketScout is asked to run but the env kill-switch is off."""


@dataclass
class ObservationBatchResult:
    observation_batch_id: str
    query_used: str
    marketplace_id: str
    captured_at: str
    market_source: str
    environment: str
    total_observed: int
    included_candidates: int
    excluded_records: int
    raw_batch_artifact_key: str
    batch_receipt_id: str
    per_observation: list[dict[str, Any]] = field(default_factory=list)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_batch_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"EBAY-BATCH-{ts}-{uuid.uuid4().hex[:6]}"


def _new_observation_id() -> str:
    return f"EBAY-OBS-{uuid.uuid4().hex[:14].upper()}"


def _build_observation_record(
    *,
    observation_id: str,
    observation_batch_id: str,
    market_source: str,
    marketplace_id: str,
    environment: str,
    query_used: str,
    normalized_asset_name: str,
    asset_category: str | None,
    item: dict[str, Any],
    include: bool,
    exclusion_reason: str | None,
    raw_response_artifact_path: str,
    normalized_record_artifact_path: str,
    sha256_receipt_path: str,
) -> dict[str, Any]:
    price = item.get("price") or {}
    return {
        "observation_id": observation_id,
        "observation_batch_id": observation_batch_id,
        "observed_at": _now_iso(),
        "market_source": market_source,
        "marketplace_id": marketplace_id,
        "environment": environment,
        "evidence_type": "OBSERVED_ASKING_PRICE_EVIDENCE",
        "transaction_verified": False,
        "condition_verified_by_defendable": False,
        "asset_category": asset_category,
        "normalized_asset_name": normalized_asset_name,
        "query_used": query_used,
        "marketplace_item_id": item.get("itemId"),
        "seller_title": item.get("title"),
        "seller_condition_text": item.get("condition"),
        "price": {
            "value": price.get("value"),
            "currency": price.get("currency"),
        },
        "shipping_price": item.get("shippingOptions"),  # may be None or list
        "buying_options": item.get("buyingOptions") or [],
        "item_url": item.get("itemWebUrl"),
        "seller_claims_unverified": True,
        "machine_assisted_normalization": True,
        "include_as_comparable_candidate": include,
        "exclusion_reason": exclusion_reason,
        "raw_response_artifact_path": raw_response_artifact_path,
        "normalized_record_artifact_path": normalized_record_artifact_path,
        "sha256_receipt_path": sha256_receipt_path,
        "disclaimer": (
            "Observed active listing evidence only. Asking prices are not "
            "verified paid transaction comps. Seller-stated condition is "
            "not Defendable-verified condition."
        ),
    }


def collect_observations(
    *,
    query: str,
    asset_category: str | None = None,
    normalized_asset_name: str | None = None,
    limit: int = 10,
    asset_intake_id: str | None = None,
    store: BakeryStore | None = None,
) -> ObservationBatchResult:
    """Run a single eBay Browse query · normalize · persist · receipt.

    NEVER calls eBay unless COMPUTECLAW_MARKET_OBSERVATION_ENABLED=true.
    """
    if not is_enabled():
        raise MarketScoutDisabled(
            "MarketScout is disabled. Set "
            "COMPUTECLAW_MARKET_OBSERVATION_ENABLED=true to enable live "
            "eBay Browse observations."
        )

    # Lazy import keeps this module importable when ebay deps absent in tests
    from app.integrations.ebay.browse_api import (
        EbayBrowseAPIError,
        search_item_summaries,
    )
    from app.integrations.ebay.oauth import (
        EbayOAuthConfigMissing,
        EbayOAuthError,
    )

    store = store or get_bakery_store()
    batch_id = _new_batch_id()
    captured_at = _now_iso()

    try:
        browse_result = search_item_summaries(q=query, limit=limit)
    except (EbayOAuthConfigMissing, EbayOAuthError, EbayBrowseAPIError):
        raise

    environment = browse_result.environment
    marketplace_id = os.environ.get("EBAY_MARKETPLACE_ID", "EBAY_US")

    # Write raw batch immutably (eBay's full response body, kept verbatim)
    raw_payload = {
        "observation_batch_id": batch_id,
        "query_used": query,
        "limit": limit,
        "marketplace_id": marketplace_id,
        "environment": environment,
        "captured_at": captured_at,
        "asset_intake_id": asset_intake_id,
        "browse_total_reported": browse_result.total,
        "item_summaries": browse_result.item_summaries,
    }
    raw_bytes = json.dumps(raw_payload, sort_keys=True, indent=2).encode("utf-8")
    raw_key = bakery_key(
        "compute-claw", "market-observations", "ebay", "raw-batches",
        f"{safe_key_part(batch_id)}.json",
    )
    raw_artifact = store.driver.write_immutable(raw_key, raw_bytes, "application/json")

    per_observation: list[dict[str, Any]] = []
    included = 0
    excluded = 0
    receipts_generated: list[str] = []
    normalized_name = normalized_asset_name or query

    for item in browse_result.item_summaries:
        observation_id = _new_observation_id()
        title = item.get("title") or ""
        decision = classify_title(title)
        include = (decision.decision == "INCLUDED")
        exclusion_reason = decision.reason_text if not include else None

        # Write normalization record (separate artifact · derived)
        norm_record = build_normalization_record(
            observation_id=observation_id,
            normalized_asset_name=normalized_name,
            decision=decision,
        )
        norm_bytes = json.dumps(norm_record, sort_keys=True, indent=2).encode("utf-8")
        norm_subdir = "excluded" if not include else "normalized"
        norm_key = bakery_key(
            "compute-claw", "market-observations", "ebay", norm_subdir,
            f"{safe_key_part(observation_id)}.json",
        )
        store.driver.write_immutable(norm_key, norm_bytes, "application/json")

        # If included · also write to included-candidates for clean enumeration
        included_key = None
        if include:
            included += 1
            included_key = bakery_key(
                "compute-claw", "market-observations", "ebay",
                "included-candidates",
                f"{safe_key_part(observation_id)}.json",
            )
            store.driver.write_immutable(included_key, norm_bytes, "application/json")
        else:
            excluded += 1

        # Receipt per observation
        observation_record = _build_observation_record(
            observation_id=observation_id,
            observation_batch_id=batch_id,
            market_source="EBAY_BROWSE_API",
            marketplace_id=marketplace_id,
            environment=environment,
            query_used=query,
            normalized_asset_name=normalized_name,
            asset_category=asset_category,
            item=item,
            include=include,
            exclusion_reason=exclusion_reason,
            raw_response_artifact_path=raw_artifact.key,
            normalized_record_artifact_path=norm_key,
            sha256_receipt_path="",  # filled after receipt
        )

        receipt = generate_receipt(
            artifact_type="pair_candidate",
            artifact_key=norm_key,
            artifact_bytes=norm_bytes,
            source_run_id=batch_id,
            tribunal_label="INCLUDED" if include else "EXCLUDED_PENDING_REVIEW",
            redaction_status="NOT_APPLICABLE",
            consent_status={"public_listing_metadata": True},
            extra_metadata={
                "rail": "compute_claw.market_observation",
                "observation_id": observation_id,
                "batch_id": batch_id,
                "asset_category": asset_category,
                "normalized_asset_name": normalized_name,
            },
            store=store,
        )
        observation_record["sha256_receipt_path"] = (
            f"receipts/sha256/{receipt['receipt_id']}.json"
        )
        per_observation.append(observation_record)
        receipts_generated.append(receipt["receipt_id"])

    # Batch-level manifest receipt (over the raw batch bytes)
    batch_receipt = generate_receipt(
        artifact_type="benchmark_pack",
        artifact_key=raw_artifact.key,
        artifact_bytes=raw_bytes,
        source_run_id=batch_id,
        tribunal_label="OBSERVATION_BATCH",
        redaction_status="NOT_APPLICABLE",
        consent_status={"public_listing_metadata": True},
        extra_metadata={
            "rail": "compute_claw.market_observation.batch",
            "batch_id": batch_id,
            "query_used": query,
            "total_observed": len(browse_result.item_summaries),
            "included": included,
            "excluded": excluded,
            "asset_intake_id": asset_intake_id,
        },
        store=store,
    )

    # Emit lifecycle events
    append_event(
        event_type="clawcheck.receipt.generated",
        run_id=batch_id,
        payload={
            "rail": "computeclaw.market_observation.batch_stored",
            "batch_id": batch_id,
            "query_used": query,
            "asset_intake_id": asset_intake_id,
            "batch_receipt_id": batch_receipt["receipt_id"],
        },
        store=store,
    )

    _log.info(
        "MarketScout batch · batch_id=%s query=%r total=%d included=%d excluded=%d",
        batch_id, query, len(browse_result.item_summaries), included, excluded,
    )

    return ObservationBatchResult(
        observation_batch_id=batch_id,
        query_used=query,
        marketplace_id=marketplace_id,
        captured_at=captured_at,
        market_source="EBAY_BROWSE_API",
        environment=environment,
        total_observed=len(browse_result.item_summaries),
        included_candidates=included,
        excluded_records=excluded,
        raw_batch_artifact_key=raw_artifact.key,
        batch_receipt_id=batch_receipt["receipt_id"],
        per_observation=per_observation,
    )


def safe_summarize_batch(batch: ObservationBatchResult, max_items: int = 5) -> dict[str, Any]:
    """Operator/admin-safe summary · no raw seller account details."""
    sample = []
    for obs in batch.per_observation[:max_items]:
        sample.append({
            "observation_id": obs["observation_id"],
            "marketplace_item_id": obs["marketplace_item_id"],
            "normalized_asset_name": obs["normalized_asset_name"],
            "seller_title": (obs["seller_title"] or "")[:160],
            "price": obs["price"],
            "include_as_comparable_candidate": obs["include_as_comparable_candidate"],
            "exclusion_reason": obs["exclusion_reason"],
            "evidence_type": obs["evidence_type"],
            "transaction_verified": obs["transaction_verified"],
        })
    return {
        "observation_batch_id": batch.observation_batch_id,
        "environment": batch.environment,
        "query_used": batch.query_used,
        "marketplace_id": batch.marketplace_id,
        "captured_at": batch.captured_at,
        "total_observed": batch.total_observed,
        "included_candidates": batch.included_candidates,
        "excluded_records": batch.excluded_records,
        "batch_receipt_id": batch.batch_receipt_id,
        "sample": sample,
        "doctrine_note": (
            "Observed active listing evidence only. Asking prices are not "
            "verified paid transaction comps. Seller-stated condition is "
            "not Defendable-verified condition."
        ),
    }
