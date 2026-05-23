"""Compute SKU registry · canonical names + alias patterns + price bands.

Each SKU has:
  · canonical: the official Defendable name we emit in receipts + reports
  · query_aliases: strings we send to eBay Insights `q=` for this SKU
  · title_patterns: regex patterns we match against eBay item titles to
    identify which SKU a sold-comp is for
  · price_band_usd: (low, high) inclusive · sanity bracket for tribunal

The price bands are deliberately wide · they catch obvious errors (a
$5 RTX 4090, a $50,000 used 3090) without rejecting genuine market
fluctuation. They are NOT a price oracle · they're a Tribunal guardrail.

Easy to extend: add a new ComputeSkuSpec to the SKUS list. No other
file change needed · tribunal + ingest pick it up automatically.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ComputeSkuSpec:
    canonical: str                  # "NVIDIA RTX 3090"
    query_aliases: list[str]        # ["RTX 3090", "GeForce RTX 3090"]
    title_patterns: list[re.Pattern]  # regex matchers against eBay titles
    price_band_usd: tuple[float, float] | None  # (lo, hi) sanity bracket


def _p(s: str) -> re.Pattern:
    return re.compile(s, re.IGNORECASE)


# ─── Compute SKU catalogue ────────────────────────────────────────────


SKUS: list[ComputeSkuSpec] = [
    # ── Consumer RTX (Ampere · 30-series) ───────────────────────────
    ComputeSkuSpec(
        canonical="NVIDIA RTX 3090",
        query_aliases=["RTX 3090", "GeForce RTX 3090"],
        title_patterns=[
            _p(r"\brtx\s*3090(?!\s*ti)\b"),  # 3090 but NOT 3090 Ti (different SKU)
            _p(r"geforce\s+rtx\s*3090\b"),
        ],
        price_band_usd=(400, 2500),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA RTX 3090 Ti",
        query_aliases=["RTX 3090 Ti"],
        title_patterns=[_p(r"\brtx\s*3090\s*ti\b")],
        price_band_usd=(600, 3000),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA RTX 3080",
        query_aliases=["RTX 3080"],
        title_patterns=[_p(r"\brtx\s*3080(?!\s*ti)\b")],
        price_band_usd=(250, 1500),
    ),

    # ── Consumer RTX (Ada · 40-series) ───────────────────────────────
    ComputeSkuSpec(
        canonical="NVIDIA RTX 4090",
        query_aliases=["RTX 4090", "GeForce RTX 4090"],
        title_patterns=[_p(r"\brtx\s*4090\b")],
        price_band_usd=(1200, 4500),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA RTX 4080",
        query_aliases=["RTX 4080"],
        title_patterns=[
            _p(r"\brtx\s*4080(?!\s*super)\b"),
            _p(r"\brtx\s*4080\s*super\b"),  # treat Super as same SKU for now
        ],
        price_band_usd=(700, 2200),
    ),

    # ── Consumer RTX (Blackwell · 50-series) ─────────────────────────
    ComputeSkuSpec(
        canonical="NVIDIA RTX 5090",
        query_aliases=["RTX 5090", "GeForce RTX 5090"],
        title_patterns=[_p(r"\brtx\s*5090\b")],
        price_band_usd=(1500, 6000),
    ),

    # ── Workstation RTX A-series (Ampere) + Ada Pro ──────────────────
    ComputeSkuSpec(
        canonical="NVIDIA RTX A4000",
        query_aliases=["RTX A4000"],
        title_patterns=[_p(r"\brtx\s*a4000\b")],
        price_band_usd=(400, 1800),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA RTX A5000",
        query_aliases=["RTX A5000"],
        title_patterns=[_p(r"\brtx\s*a5000\b")],
        price_band_usd=(800, 3000),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA RTX A6000",
        query_aliases=["RTX A6000"],
        title_patterns=[_p(r"\brtx\s*a6000\b")],
        price_band_usd=(2500, 7500),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA RTX 4500 Ada",
        query_aliases=["RTX 4500 Ada", "RTX 4500"],
        title_patterns=[_p(r"\brtx\s*4500(?:\s*ada)?\b")],
        price_band_usd=(2000, 6000),
    ),

    # ── RTX PRO Blackwell Workstation (flagship · what's in the rig) ─
    ComputeSkuSpec(
        canonical="NVIDIA RTX PRO 6000 Blackwell",
        query_aliases=[
            "RTX PRO 6000 Blackwell",
            "RTX 6000 Blackwell",
            "NVIDIA RTX 6000 Blackwell",
        ],
        title_patterns=[
            _p(r"\brtx\s*(?:pro\s*)?6000\s+blackwell\b"),
            _p(r"\bblackwell\s+workstation\b"),
        ],
        price_band_usd=(5000, 15000),
    ),

    # ── Datacenter (Hopper / Ampere · less common on eBay but worth tracking) ─
    ComputeSkuSpec(
        canonical="NVIDIA H100",
        query_aliases=["NVIDIA H100", "H100 80GB"],
        title_patterns=[_p(r"\bh100\b")],
        price_band_usd=(15000, 60000),
    ),
    ComputeSkuSpec(
        canonical="NVIDIA A100",
        query_aliases=["NVIDIA A100", "A100 80GB", "A100 40GB"],
        title_patterns=[_p(r"\ba100\b")],
        price_band_usd=(5000, 25000),
    ),

    # ── Apple Silicon Mac Studio (compute-class workstation) ─────────
    # Tracked because some compute workflows use M-series for ML inference
    ComputeSkuSpec(
        canonical="Apple Mac Studio M2 Ultra",
        query_aliases=["Mac Studio M2 Ultra"],
        title_patterns=[_p(r"\bmac\s*studio\b.*m2\s*ultra\b")],
        price_band_usd=(2500, 8000),
    ),
]


# Default per-call SKU list for compute_market_watch.ingest.run_default_ingest()
# Targeted at the highest-volume Defendable lanes (rig + portfolio brands).
DEFAULT_INGEST_SKUS: tuple[str, ...] = (
    "RTX 3090",
    "RTX 4090",
    "RTX A6000",
    "RTX 4500 Ada",
    "RTX PRO 6000 Blackwell",
    "NVIDIA H100",
    "NVIDIA A100",
)


def match_compute_sku(title: str, *, queried_hint: str | None = None) -> ComputeSkuSpec | None:
    """Return the SKU whose title pattern matches · or None if no match.

    `queried_hint` is the q= string we used to call Insights · helps when
    multiple SKUs could match (e.g. a "RTX 3090" query result that contains
    both "3090" and "3090 Ti" patterns · we prefer the SKU whose alias
    matches the queried hint).
    """
    candidates: list[ComputeSkuSpec] = []
    for sku in SKUS:
        for pat in sku.title_patterns:
            if pat.search(title):
                candidates.append(sku)
                break
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    # Multiple matches · prefer the one whose alias matches the queried hint
    if queried_hint:
        hint_lower = queried_hint.lower()
        for sku in candidates:
            for alias in sku.query_aliases:
                if alias.lower() in hint_lower or hint_lower in alias.lower():
                    return sku
    # Fall back to the first match · longest canonical name wins (more specific)
    return max(candidates, key=lambda s: len(s.canonical))


def find_sku_by_alias(alias: str) -> ComputeSkuSpec | None:
    """Lookup helper · used by ingest to validate the operator's SKU list."""
    al = alias.lower()
    for sku in SKUS:
        for a in sku.query_aliases:
            if a.lower() == al:
                return sku
    return None
