"""Defendable Pair Factory · rights-aware pair candidate production.

Generates structured training/eval pairs from normalized observations
with HARD source-rights gating. Defaults:
  · use_class = CANDIDATE_ONLY
  · training_eligible = False
  · source_rights_status = INTERNAL_RESEARCH_ONLY

A pair only graduates to TRAINING_ELIGIBLE when ALL of:
  · The source artifact has SourceRightsRecord with
    rights_status == TRAINING_ALLOWED AND training_eligible=True
  · The pair batch has batch_status == APPROVED_FOR_TRAINING
  · A validator review has passed

Today this module ships the candidate generator + the rights gate.
The validator review pathway is a documented next-session task.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.goods import (
    GoodsClass,
    MarketObservation,
    PairBatch,
    PairBatchStatus,
    PairBatchType,
    RightsStatus,
    SourceType,
    TrainingPair,
    TrainingPairUseClass,
)


class PairFactoryError(ValueError):
    pass


def create_batch(
    db: Session,
    *,
    batch_id: str,
    goods_class: GoodsClass,
    batch_type: PairBatchType,
    source_rights_status: RightsStatus = RightsStatus.INTERNAL_RESEARCH_ONLY,
) -> PairBatch:
    batch = PairBatch(
        id=uuid.uuid4(),
        batch_id=batch_id,
        goods_class=goods_class,
        batch_type=batch_type,
        batch_status=PairBatchStatus.DRAFT_CANDIDATES,
        source_rights_status=source_rights_status,
        validator_status=None,
        training_eligible=False,
    )
    db.add(batch)
    db.flush()
    return batch


def generate_listing_classification_pair(
    db: Session,
    *,
    batch: PairBatch,
    observation: MarketObservation,
    pair_id: str,
) -> TrainingPair:
    """Generate a LISTING_VS_TRANSACTION_CLASSIFICATION pair.

    Always:
      · use_class = CANDIDATE_ONLY
      · training_eligible = False
      · validator_status = VALIDATOR_REVIEW_REQUIRED
    """
    if observation.source_type != SourceType.PUBLIC_ACTIVE_LISTING:
        raise PairFactoryError(
            "listing classification pair requires PUBLIC_ACTIVE_LISTING observation"
        )

    lineage = {
        "provider": observation.source_provider.value,
        "observation_id": str(observation.id),
        "source_type": observation.source_type.value,
        "rights_status": observation.rights_status.value,
        "raw_artifact_id": str(observation.raw_artifact_id) if observation.raw_artifact_id else None,
    }
    pair = TrainingPair(
        id=uuid.uuid4(),
        pair_id=pair_id,
        pair_batch_id=batch.id,
        goods_id=observation.goods_id,
        pair_type=PairBatchType.LISTING_VS_TRANSACTION_CLASSIFICATION,
        source_lineage=lineage,
        input_json={
            "product_title": observation.title_normalized or observation.title_raw,
            "displayed_price_present": observation.price_amount is not None,
            "sale_confirmation_present": False,
            "source_type": observation.source_type.value,
        },
        expected_output_json={
            "classification": "ASKING_PRICE_OBSERVATION",
            "transaction_confirmed": False,
            "allowed_comp_use": "MARKET_CONTEXT_ONLY",
            "quality_grade_ceiling": "C",
            "required_disclosure": "Asking price is not confirmed transaction evidence.",
        },
        validator_status="VALIDATOR_REVIEW_REQUIRED",
        source_rights_status=observation.rights_status,
        use_class=TrainingPairUseClass.CANDIDATE_ONLY,
        training_eligible=False,
    )
    db.add(pair)
    db.flush()
    return pair


def assert_training_eligible(pair: TrainingPair) -> None:
    """Doctrine gate · raises unless every condition for training is met."""
    if pair.use_class != TrainingPairUseClass.TRAINING_ELIGIBLE:
        raise PairFactoryError(
            f"pair {pair.pair_id} use_class={pair.use_class.value} · not training-eligible"
        )
    if not pair.training_eligible:
        raise PairFactoryError(
            f"pair {pair.pair_id} training_eligible=False · refuse export"
        )
    if pair.source_rights_status != RightsStatus.TRAINING_ALLOWED:
        raise PairFactoryError(
            f"pair {pair.pair_id} source_rights_status={pair.source_rights_status.value} · "
            f"requires TRAINING_ALLOWED"
        )
    if pair.validator_status != "PASSED":
        raise PairFactoryError(
            f"pair {pair.pair_id} validator_status={pair.validator_status} · "
            f"must be PASSED to export"
        )


def approve_batch_for_training(*args, **kwargs):
    """NotImplemented today · requires validator-review wiring and an
    explicit operator approval. The seam exists so tests can verify
    the gate is closed by default.
    """
    raise NotImplementedError(
        "approve_batch_for_training requires validator review · not implemented this turn"
    )
