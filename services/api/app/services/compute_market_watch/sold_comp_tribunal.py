"""Rule-based sold-comp tribunal · DETERMINISTIC · no LLM.

Classifies an eBay Marketplace Insights item-sale record into one of:

  · HONEY        · clean confirmed-sale evidence · usable as comp
  · JELLY        · downgraded · review/repair queue
  · PROPOLIS     · invalid · preserved as adversarial evidence (NEVER comp)
  · QUARANTINED  · category mismatch · model uncertainty

Rules are pure code · documented inline. The fixture-driven SKU expectations
let an operator add a new compute SKU (e.g., a future RTX 5090) without
touching this module · just add the SKU + sanity-band to compute_skus.py.

Honest framing in every output:
  · `tribunal_label` (the verdict)
  · `tribunal_rules_fired` (the list of named rules that contributed)
  · `failed_checks` (per-rule failures · empty list for HONEY)
  · `reason` (single-sentence summary)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.services.compute_market_watch.compute_skus import (
    ComputeSkuSpec,
    match_compute_sku,
)


# Tribunal labels (string literals · match the bakery convention)
LABEL_HONEY = "HONEY"
LABEL_JELLY = "JELLY"
LABEL_PROPOLIS = "PROPOLIS"
LABEL_QUARANTINED = "QUARANTINED"


_SANE_MAX_PRICE_USD = 200_000  # No single GPU/accelerator sells above this
_RECENT_SOLD_DAYS = 90         # eBay Insights covers last 90 days · be strict


@dataclass
class TribunalVerdict:
    label: str
    rules_fired: list[str]
    failed_checks: list[str]
    reason: str
    matched_sku: ComputeSkuSpec | None
    normalized_price_usd: float | None


def classify(sale: dict[str, Any], *, queried_sku_hint: str | None = None) -> TribunalVerdict:
    """Classify a single Marketplace Insights item-sale record.

    `queried_sku_hint` is the SKU string we queried with (e.g. "RTX 3090") ·
    helps category-match when eBay's category data is sparse.
    """
    failed: list[str] = []
    rules_fired: list[str] = []

    # ── Critical-field presence (PROPOLIS triggers) ──────────────────
    item_id = sale.get("itemId")
    title = (sale.get("title") or "").strip()
    sold_price_obj = sale.get("lastSoldPrice") or {}
    price_raw = sold_price_obj.get("value")
    currency = sold_price_obj.get("currency") or ""
    sold_date = sale.get("lastSoldDate") or ""

    rules_fired.append("critical_field_presence")
    if not item_id:
        failed.append("missing_itemId")
    if not title or len(title) < 10:
        failed.append("missing_or_short_title")
    if price_raw is None:
        failed.append("missing_lastSoldPrice_value")
    if not currency:
        failed.append("missing_lastSoldPrice_currency")
    if not sold_date:
        failed.append("missing_lastSoldDate")

    # Parse price
    rules_fired.append("price_numeric_check")
    price_usd: float | None = None
    if price_raw is not None:
        try:
            price_usd = float(price_raw)
        except (TypeError, ValueError):
            failed.append("price_value_not_numeric")
        else:
            if price_usd <= 0:
                failed.append("price_zero_or_negative")
            if price_usd > _SANE_MAX_PRICE_USD:
                failed.append(f"price_above_sanity_ceiling_${_SANE_MAX_PRICE_USD:,.0f}")

    if currency and currency != "USD":
        # Non-USD is JELLY (we keep it but can't directly compare without FX)
        failed.append(f"non_usd_currency_{currency}")

    # Date parse + recency
    rules_fired.append("date_parse_recency")
    sold_dt: datetime | None = None
    if sold_date:
        try:
            sold_dt = datetime.fromisoformat(sold_date.replace("Z", "+00:00"))
        except ValueError:
            failed.append("sold_date_unparseable")
    if sold_dt is not None:
        age_days = (datetime.now(timezone.utc) - sold_dt).days
        if age_days < -1:  # future date · clearly invalid
            failed.append(f"sold_date_in_future_{age_days}d")
        elif age_days > _RECENT_SOLD_DAYS + 30:
            # Insights only returns 90-day window · anything beyond + 30
            # grace means parsing or supply chain issue
            failed.append(f"sold_date_too_old_{age_days}d")

    # ── Title-text anti-patterns (sandbox tests · obvious scams) ────
    # These are PROPOLIS-class regardless of SKU match · "test" / "promotion
    # test" in a title means the record is unfit as comp evidence even if
    # it does NOT match a known compute SKU.
    rules_fired.append("title_text_filter")
    title_lower = title.lower()
    sandbox_test = bool(
        re.search(r"\btest\b", title_lower)
        or re.search(r"\bpromotion test\b", title_lower)
        or re.search(r"\bdemo\b", title_lower)
        or re.search(r"for promotion test \d+", title_lower)
    )
    if sandbox_test:
        failed.append("sandbox_or_promotion_test_marker_in_title")

    # ── SKU match (drives quarantine vs honey/jelly) ────────────────
    rules_fired.append("compute_sku_match")
    matched_sku = match_compute_sku(title, queried_hint=queried_sku_hint)
    if matched_sku is None and not sandbox_test:
        # Title doesn't match a known compute SKU AND no sandbox marker ·
        # could be a valid sale of something else returned by a loose query ·
        # quarantine for review. (Sandbox-test titles fall through to the
        # PROPOLIS aggregation below regardless of SKU match.)
        return TribunalVerdict(
            label=LABEL_QUARANTINED,
            rules_fired=rules_fired,
            failed_checks=failed + ["title_does_not_match_any_compute_sku"],
            reason=(
                "Sold-comp title did not match any known compute SKU · "
                "quarantined for category-review before use as comp evidence."
            ),
            matched_sku=None,
            normalized_price_usd=price_usd,
        )

    # ── SKU price-band sanity (per-SKU rule · only when SKU matched) ─
    if matched_sku is not None:
        rules_fired.append(f"sku_price_band:{matched_sku.canonical}")
        if price_usd is not None and matched_sku.price_band_usd is not None:
            lo, hi = matched_sku.price_band_usd
            if not (lo <= price_usd <= hi):
                failed.append(
                    f"price_${price_usd:.0f}_outside_sku_band_${lo:.0f}-${hi:.0f}"
                )

    # ── Verdict aggregation ──────────────────────────────────────────
    # Critical PROPOLIS triggers (any of these → PROPOLIS)
    critical_propolis = {
        "missing_itemId",
        "missing_lastSoldPrice_value",
        "missing_lastSoldDate",
        "price_value_not_numeric",
        "price_zero_or_negative",
        "sold_date_in_future_",  # prefix · matched via startswith
        "sandbox_or_promotion_test_marker_in_title",
    }
    propolis_hit = any(
        any(fc.startswith(p) for fc in failed) for p in critical_propolis
    )
    # Sanity-ceiling and SKU-band hits are also PROPOLIS-class (clear-bad-data)
    if any(fc.startswith("price_above_sanity_ceiling") for fc in failed):
        propolis_hit = True

    if propolis_hit:
        return TribunalVerdict(
            label=LABEL_PROPOLIS,
            rules_fired=rules_fired,
            failed_checks=failed,
            reason=(
                "Sold-comp record failed a critical rule (missing key field · "
                "zero/invalid price · sandbox-test marker · or sanity-ceiling "
                "breach) · preserved as adversarial evidence · NEVER used as "
                "positive comp."
            ),
            matched_sku=matched_sku,
            normalized_price_usd=price_usd,
        )

    if failed:
        # Non-critical failures · JELLY (still preserved · operator review path)
        return TribunalVerdict(
            label=LABEL_JELLY,
            rules_fired=rules_fired,
            failed_checks=failed,
            reason=(
                "Sold-comp record has non-critical issues "
                f"({len(failed)} downgrade(s)) · preserved as JELLY · "
                f"review/repair before use as production comp evidence."
            ),
            matched_sku=matched_sku,
            normalized_price_usd=price_usd,
        )

    # All checks passed
    return TribunalVerdict(
        label=LABEL_HONEY,
        rules_fired=rules_fired,
        failed_checks=[],
        reason=(
            f"Sold-comp record passed every rule · matched SKU "
            f"{matched_sku.canonical} · "
            f"${price_usd:.0f} {currency} · usable as confirmed-sale evidence."
        ),
        matched_sku=matched_sku,
        normalized_price_usd=price_usd,
    )
