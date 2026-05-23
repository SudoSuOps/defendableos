"""Orchestrator · Marketplace Insights → Tribunal → bakery vault.

Public entry: run_compute_sold_comp_ingest()

For each SKU in the requested list:
  1. Call Marketplace Insights search_item_sales(q=sku_alias)
  2. For each returned sale:
     a. Classify via sold_comp_tribunal.classify()
     b. Build the sold-comp record envelope
     c. Write immutably to bakery vault under
        compute-market-watch/sold-comps/<label>/<comp_id>.json
     d. Generate SHA-256 receipt
     e. Append to per-run ingest log
  3. Write the per-run aggregate ingest manifest under
     compute-market-watch/ingest-runs/<run_id>.json

Returns a SAFE summary the admin endpoint can return (counts only · no
seller usernames, no raw payload bodies · those live in the vault).
"""
from __future__ import annotations

import hashlib
import json
import logging
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
from app.services.claw_bakery.receipts import generate_receipt
from app.services.compute_market_watch.compute_skus import (
    DEFAULT_INGEST_SKUS,
    find_sku_by_alias,
)
from app.services.compute_market_watch.sold_comp_tribunal import (
    LABEL_HONEY,
    LABEL_JELLY,
    LABEL_PROPOLIS,
    LABEL_QUARANTINED,
    TribunalVerdict,
    classify,
)


_log = logging.getLogger("compute_market_watch.ingest")


@dataclass
class SkuIngestStats:
    sku_alias: str
    total_from_ebay: int = 0
    by_label: dict[str, int] = field(default_factory=lambda: {
        LABEL_HONEY: 0,
        LABEL_JELLY: 0,
        LABEL_PROPOLIS: 0,
        LABEL_QUARANTINED: 0,
    })
    errors: list[str] = field(default_factory=list)


@dataclass
class IngestRunResult:
    run_id: str
    environment: str
    started_at: str
    completed_at: str
    skus_requested: list[str]
    per_sku_stats: list[SkuIngestStats]
    total_processed: int
    total_by_label: dict[str, int]
    manifest_artifact_key: str
    bundle_sha256: str
    dry_run: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"cmw-{ts}-{uuid.uuid4().hex[:6]}"


def _bucket_for_label(label: str) -> str:
    return {
        LABEL_HONEY: "honey",
        LABEL_JELLY: "jelly",
        LABEL_PROPOLIS: "propolis",
        LABEL_QUARANTINED: "quarantined",
    }.get(label, "quarantined")


def _build_comp_envelope(
    *,
    run_id: str,
    sku_alias: str,
    sale: dict[str, Any],
    verdict: TribunalVerdict,
    environment: str,
) -> tuple[str, dict[str, Any]]:
    """Build the on-disk sold-comp record · returns (comp_id, envelope)."""
    item_id = sale.get("itemId") or f"missing-{uuid.uuid4().hex[:8]}"
    comp_id = f"CMW-COMP-{safe_key_part(item_id)}"
    sold_price_obj = sale.get("lastSoldPrice") or {}
    envelope = {
        "comp_id": comp_id,
        "run_id": run_id,
        "source": "EBAY_MARKETPLACE_INSIGHTS",
        "environment": environment,
        "queried_sku_alias": sku_alias,
        "matched_sku_canonical": verdict.matched_sku.canonical if verdict.matched_sku else None,
        "tribunal_label": verdict.label,
        "tribunal_rules_fired": verdict.rules_fired,
        "tribunal_failed_checks": verdict.failed_checks,
        "tribunal_reason": verdict.reason,
        "evidence": {
            "itemId": sale.get("itemId"),
            "title": sale.get("title"),
            "lastSoldDate": sale.get("lastSoldDate"),
            "lastSoldPrice": {
                "value": sold_price_obj.get("value"),
                "currency": sold_price_obj.get("currency"),
            },
            "condition": sale.get("condition"),
            "conditionId": sale.get("conditionId"),
            "categories": sale.get("categories"),
            "itemWebUrl": sale.get("itemWebUrl"),
        },
        "normalized_price_usd": verdict.normalized_price_usd,
        "captured_at": _now_iso(),
        "doctrine": {
            "data_class": "PERMISSIONED_CONNECTED_SALE" if verdict.label == LABEL_HONEY else None,
            "training_eligible_as_positive": verdict.label == LABEL_HONEY,
            "use_class": "COMP_EVIDENCE" if verdict.label == LABEL_HONEY else "REVIEW_QUEUE",
            "note": (
                "HONEY sold-comps are usable as confirmed-sale evidence in "
                "MarketReady receipts. JELLY/QUARANTINED require operator "
                "review. PROPOLIS is preserved as adversarial evidence and "
                "NEVER used as positive comp."
            ),
        },
    }
    return comp_id, envelope


def _write_sold_comp(
    *,
    store: BakeryStore,
    comp_id: str,
    label: str,
    envelope: dict[str, Any],
) -> tuple[str, str]:
    """Write the sold-comp envelope immutably · return (storage_key, sha256)."""
    bucket = _bucket_for_label(label)
    body = json.dumps(envelope, sort_keys=True, indent=2).encode("utf-8")
    key = bakery_key(
        "compute-market-watch", "sold-comps", bucket, f"{safe_key_part(comp_id)}.json"
    )
    artifact = store.driver.write_immutable(key, body, "application/json")
    return artifact.key, artifact.sha256


def run_compute_sold_comp_ingest(
    *,
    sku_aliases: list[str] | None = None,
    limit_per_sku: int = 10,
    dry_run: bool = False,
    store: BakeryStore | None = None,
) -> IngestRunResult:
    """Run a sold-comp ingest pass over the requested compute SKUs.

    Calls eBay Marketplace Insights for each SKU · classifies each
    returned sale through the deterministic tribunal · persists each
    result as an immutable bakery artifact · emits an aggregate manifest.

    `dry_run=True` runs the full pipeline EXCEPT the per-comp write +
    receipt · returns counts only · useful for cost-control rehearsals
    before authorizing a full ingest.
    """
    # Lazy import to keep this module testable without exercising httpx
    from app.integrations.ebay.marketplace_insights import (
        EbayMarketplaceInsightsError,
        EbayMarketplaceInsightsScopeDenied,
        search_item_sales,
    )

    store = store or get_bakery_store()
    run_id = _new_run_id()
    started_at = _now_iso()
    skus = list(sku_aliases) if sku_aliases else list(DEFAULT_INGEST_SKUS)

    per_sku: list[SkuIngestStats] = []
    receipts: list[dict[str, Any]] = []
    total_by_label: dict[str, int] = {
        LABEL_HONEY: 0, LABEL_JELLY: 0,
        LABEL_PROPOLIS: 0, LABEL_QUARANTINED: 0,
    }
    environment = "unknown"

    for sku_alias in skus:
        stats = SkuIngestStats(sku_alias=sku_alias)
        # Validate SKU alias is registered (defensive · prevents typos
        # from silently producing zero-result calls)
        if find_sku_by_alias(sku_alias) is None:
            stats.errors.append(f"unknown_sku_alias:{sku_alias}")
            per_sku.append(stats)
            continue

        try:
            result = search_item_sales(q=sku_alias, limit=limit_per_sku)
        except EbayMarketplaceInsightsScopeDenied as exc:
            stats.errors.append(f"scope_denied:{exc}")
            per_sku.append(stats)
            continue
        except EbayMarketplaceInsightsError as exc:
            stats.errors.append(f"insights_error:{type(exc).__name__}:{exc}")
            per_sku.append(stats)
            continue

        environment = result.environment
        stats.total_from_ebay = len(result.item_sales)

        for sale in result.item_sales:
            verdict = classify(sale, queried_sku_hint=sku_alias)
            stats.by_label[verdict.label] = stats.by_label.get(verdict.label, 0) + 1
            total_by_label[verdict.label] = total_by_label.get(verdict.label, 0) + 1

            if dry_run:
                continue

            comp_id, envelope = _build_comp_envelope(
                run_id=run_id,
                sku_alias=sku_alias,
                sale=sale,
                verdict=verdict,
                environment=environment,
            )
            try:
                key, sha = _write_sold_comp(
                    store=store, comp_id=comp_id, label=verdict.label, envelope=envelope,
                )
            except Exception as exc:  # noqa: BLE001
                stats.errors.append(f"write_failed:{comp_id}:{type(exc).__name__}")
                continue

            # SHA-256 receipt over the raw bytes
            try:
                generate_receipt(
                    artifact_type="pair_candidate",  # closest matching artifact_type literal
                    artifact_key=key,
                    artifact_bytes=json.dumps(envelope, sort_keys=True, indent=2).encode("utf-8"),
                    source_run_id=run_id,
                    tribunal_label=verdict.label,
                    redaction_status="NOT_APPLICABLE",
                    consent_status={"public_listing_metadata": True},
                    extra_metadata={
                        "comp_id": comp_id,
                        "sku_alias": sku_alias,
                        "matched_sku": verdict.matched_sku.canonical if verdict.matched_sku else None,
                        "rail": "compute_market_watch",
                    },
                    store=store,
                )
                receipts.append({"comp_id": comp_id, "sha256": sha, "label": verdict.label})
            except Exception as exc:  # noqa: BLE001
                stats.errors.append(f"receipt_failed:{comp_id}:{type(exc).__name__}")

        per_sku.append(stats)

    # ── Run manifest ────────────────────────────────────────────────
    completed_at = _now_iso()
    manifest = {
        "run_id": run_id,
        "rail": "compute_market_watch.sold_comp_ingest",
        "source": "EBAY_MARKETPLACE_INSIGHTS",
        "environment": environment,
        "dry_run": dry_run,
        "started_at": started_at,
        "completed_at": completed_at,
        "skus_requested": skus,
        "limit_per_sku": limit_per_sku,
        "total_processed": sum(s.total_from_ebay for s in per_sku),
        "total_by_label": total_by_label,
        "per_sku": [
            {
                "sku_alias": s.sku_alias,
                "total_from_ebay": s.total_from_ebay,
                "by_label": s.by_label,
                "errors": s.errors,
            } for s in per_sku
        ],
        "receipts": receipts,
        "doctrine_note": (
            "HONEY counts are usable as confirmed-sale comp evidence. "
            "JELLY/QUARANTINED require operator review before use. "
            "PROPOLIS preserved as adversarial evidence · NEVER used "
            "as positive comp. Per-comp artifacts and receipts live "
            "under compute-market-watch/sold-comps/<label>/."
        ),
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")
    manifest_key = bakery_key("compute-market-watch", "ingest-runs", f"{run_id}.json")
    bundle_sha = hashlib.sha256(manifest_bytes).hexdigest()
    if not dry_run:
        store.driver.write_immutable(manifest_key, manifest_bytes, "application/json")

    return IngestRunResult(
        run_id=run_id,
        environment=environment,
        started_at=started_at,
        completed_at=completed_at,
        skus_requested=skus,
        per_sku_stats=per_sku,
        total_processed=sum(s.total_from_ebay for s in per_sku),
        total_by_label=total_by_label,
        manifest_artifact_key=manifest_key,
        bundle_sha256=bundle_sha,
        dry_run=dry_run,
    )
