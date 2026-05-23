"""Asset type + category catalogue for ComputeClaw intakes.

Category groups map to ProductRadar / Compute Market Watch SKU canonicals
where overlap exists. The taxonomy is intentionally narrow to start and
extends per founder direction (no marketing copy invents categories).
"""
from __future__ import annotations


# ─── Top-level asset types ───────────────────────────────────────────


ASSET_TYPES: tuple[str, ...] = (
    "GPU",
    "GPU Workstation",
    "GPU Server",
    "Edge AI Device",
    "Storage Appliance",
    "Networking Infrastructure",
)


# ─── Category groups (mapped to model lists) ─────────────────────────


ASSET_CATEGORIES: dict[str, list[str]] = {
    "workhorse_gpu": [
        "NVIDIA RTX 3090 24GB",
        "NVIDIA RTX 3090 Ti 24GB",
        "NVIDIA RTX A5000 24GB",
        "NVIDIA RTX A6000 48GB",
    ],
    "premium_agent_gpu": [
        "NVIDIA RTX 5090 32GB",
        "NVIDIA RTX PRO 6000 Blackwell 96GB",
        "NVIDIA RTX PRO 4500 Blackwell 32GB",
    ],
    "enterprise_vintage_compute": [
        "NVIDIA Tesla V100 32GB",
        "NVIDIA A100 40GB",
        "NVIDIA A100 80GB",
    ],
    "edge_compute": [
        "NVIDIA Jetson Orin Nano",
        "ZimaBoard",
        "AI mini PC",
    ],
    "workstations": [
        "Dell Precision 7920",
        "HP Z workstation",
        "Lenovo ThinkStation",
    ],
    "infrastructure": [
        "GPU server chassis",
        "Threadripper workstation",
        "Xeon W workstation",
        "NVMe server storage",
        "10GbE networking equipment",
    ],
}


def is_known_asset_type(value: str) -> bool:
    return value in ASSET_TYPES


def is_known_asset_category(value: str) -> bool:
    return value in ASSET_CATEGORIES


def model_in_category(model_name: str, category: str) -> bool:
    if category not in ASSET_CATEGORIES:
        return False
    return model_name in ASSET_CATEGORIES[category]


def all_known_models() -> list[str]:
    return [m for ms in ASSET_CATEGORIES.values() for m in ms]
