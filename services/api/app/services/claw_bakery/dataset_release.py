"""Dataset release manifest builder.

A release is the only artifact downstream training pipelines may
consume. The default initial release is DRAFT · it is never marked
APPROVED automatically.

Doctrine:
  · only pair candidates passing assert_can_enter_training_release()
    may be enumerated in the release
  · holdouts are explicitly excluded (separate manifest)
  · raw evidence keys are NEVER referenced from a release manifest
  · the manifest's sha256_manifest_path is set ONLY after a separate
    receipt-bundle is built
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.claw_bakery.bakery_storage import BakeryStore, get_bakery_store
from app.services.claw_bakery.pair_factory import (
    PairCandidate,
    assert_can_enter_training_release,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_draft_release(
    *,
    dataset_id: str,
    version: str,
    pair_candidates: list[PairCandidate],
    store: BakeryStore | None = None,
) -> dict[str, Any]:
    """Build a DRAFT release manifest. Refuses to enumerate any pair that
    fails the training-eligibility doctrine. Holdouts are excluded.

    The returned manifest is written immutably under
    claw-bakery/dataset-releases/<dataset_id>_<version>.json.
    """
    store = store or get_bakery_store()
    honey: list[str] = []
    jelly_repaired: list[str] = []
    propolis_adversarial: list[str] = []
    excluded_holdouts: list[str] = []
    refused: list[dict[str, str]] = []
    for p in pair_candidates:
        if p.eligible_for_holdout:
            excluded_holdouts.append(p.pair_id)
            continue
        if p.tribunal_label == "PROPOLIS":
            # PROPOLIS is allowed as an *adversarial-evaluation* entry only ·
            # this manifest carries its presence but the consumer must read
            # the label and route it appropriately.
            propolis_adversarial.append(p.pair_id)
            continue
        try:
            assert_can_enter_training_release(p)
        except Exception as exc:  # noqa: BLE001
            refused.append({"pair_id": p.pair_id, "reason": str(exc)})
            continue
        if p.tribunal_label == "HONEY":
            honey.append(p.pair_id)
        elif p.tribunal_label == "JELLY_REPAIRED_TO_HONEY":
            jelly_repaired.append(p.pair_id)
    manifest = {
        "dataset_id": dataset_id,
        "version": version,
        "status": "DRAFT",
        "pair_counts": {
            "honey": len(honey),
            "jelly_repaired_to_honey": len(jelly_repaired),
            "propolis_adversarial": len(propolis_adversarial),
            "sealed_holdout": 0,
            "refused": len(refused),
        },
        "training_admission_policy": {
            "tribunal_required": True,
            "redaction_required": True,
            "operator_consent_required_for_live_intakes": True,
            "raw_evidence_excluded": True,
        },
        "pair_ids": {
            "honey": sorted(honey),
            "jelly_repaired_to_honey": sorted(jelly_repaired),
            "propolis_adversarial": sorted(propolis_adversarial),
        },
        "excluded_holdouts": sorted(excluded_holdouts),
        "refused_with_reason": refused,
        "sha256_manifest_path": None,
        "created_at": _now(),
    }
    store.put_dataset_release(dataset_id, version, manifest)
    return manifest
