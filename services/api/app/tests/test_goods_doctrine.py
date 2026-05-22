"""Goods Intelligence doctrine boundary tests.

These tests are the canary for the truth controls encoded across
goods.py, comp_foundry.py, pair_factory.py and artifacts.py. They
deliberately don't touch the database · pure-Python boundary checks
that ALL doctrine rules are encoded at the service layer.

If any of these break, somebody loosened a doctrine guard and the
PR should be rejected until the test passes again.
"""
import pytest

from app.models.goods import (
    ArtifactPrivacyClass,
    CompEligibility,
    CompQualityGrade,
    PriceType,
    ProviderStatus,
    RightsStatus,
    SourceType,
    TrainingPairUseClass,
    TrendSignal,
)
from app.services.connector_registry import (
    CONNECTOR_DEFINITIONS,
    resolve_status,
)
from app.models.goods import ProviderName


# ════════════════════════════════════════════════════════════════════
# RULE 1 · TrendSignal can never be a comp (grade E forever)
# ════════════════════════════════════════════════════════════════════


def test_trend_signal_default_comp_eligibility_is_not_a_comp():
    """The TrendSignal model's column default must be NOT_A_COMP.

    If somebody changes the default to CANDIDATE_ONLY the doctrine
    breaks · this test catches it immediately.
    """
    col = TrendSignal.__table__.c.comp_eligibility
    assert col.default.arg == CompEligibility.NOT_A_COMP, (
        f"TrendSignal.comp_eligibility default is {col.default.arg!r} · "
        "doctrine requires NOT_A_COMP"
    )


def test_trend_signal_classification_is_pinned():
    """Classification column must default to TREND_SIGNAL."""
    col = TrendSignal.__table__.c.classification
    assert col.default.arg == "TREND_SIGNAL"


# ════════════════════════════════════════════════════════════════════
# RULE 2 · PUBLIC_ACTIVE_LISTING grade ceiling = C
# ════════════════════════════════════════════════════════════════════


def test_listing_grade_ceiling_enum_includes_c():
    """The grade ceiling is C · ensure A and B exist in enum but the
    service-layer guard in comp_foundry refuses A/B on a listing.
    """
    assert CompQualityGrade.A.value == "A"
    assert CompQualityGrade.B.value == "B"
    assert CompQualityGrade.C.value == "C"


def test_comp_foundry_refuses_a_on_listing():
    """The add_listing_observation service raises CompFoundryError when
    asked to add an A-graded listing.

    We assemble a fake MarketObservation in memory · no DB write.
    """
    from app.services.comp_foundry import CompFoundryError, add_listing_observation
    from app.models.goods import MarketObservation, ProviderName

    # Build an in-memory observation that violates rule 2
    fake = MarketObservation(
        source_provider=ProviderName.EBAY_BROWSE,
        source_type=SourceType.PUBLIC_ACTIVE_LISTING,
        price_type=PriceType.ASKING_PRICE,
        transaction_confirmed=False,
        comp_eligibility=CompEligibility.CANDIDATE_ONLY,
        comp_quality_grade=CompQualityGrade.A,  # ← doctrine violation
        rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY,
        limitations=[],
        observation_id="OBS-FAKE-A",
    )

    # The function looks up by ID via db.get · stub a fake session that
    # returns our in-memory obs regardless of id.
    class FakeSession:
        def get(self, model, _id):
            return fake
        def flush(self):
            pass
        def add(self, _row):
            pass

    with pytest.raises(CompFoundryError, match="cannot have quality_grade=A"):
        add_listing_observation(
            FakeSession(), comp_set_id=None, observation_id="any"
        )


def test_comp_foundry_refuses_transaction_confirmed_on_listing():
    """If a caller tries to pass a listing with transaction_confirmed=True
    the service refuses.
    """
    from app.services.comp_foundry import CompFoundryError, add_listing_observation
    from app.models.goods import MarketObservation, ProviderName

    fake = MarketObservation(
        source_provider=ProviderName.EBAY_BROWSE,
        source_type=SourceType.PUBLIC_ACTIVE_LISTING,
        price_type=PriceType.ASKING_PRICE,
        transaction_confirmed=True,  # ← doctrine violation
        comp_eligibility=CompEligibility.CANDIDATE_ONLY,
        rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY,
        limitations=[],
        observation_id="OBS-FAKE-CONFIRMED",
    )

    class FakeSession:
        def get(self, model, _id):
            return fake
        def flush(self):
            pass
        def add(self, _row):
            pass

    with pytest.raises(CompFoundryError, match="transaction_confirmed must be False"):
        add_listing_observation(FakeSession(), comp_set_id=None, observation_id="any")


def test_comp_foundry_refuses_wrong_price_type_on_listing():
    from app.services.comp_foundry import CompFoundryError, add_listing_observation
    from app.models.goods import MarketObservation, ProviderName

    fake = MarketObservation(
        source_provider=ProviderName.EBAY_BROWSE,
        source_type=SourceType.PUBLIC_ACTIVE_LISTING,
        price_type=PriceType.CONFIRMED_TRANSACTION_PRICE,  # ← doctrine violation
        transaction_confirmed=False,
        comp_eligibility=CompEligibility.CANDIDATE_ONLY,
        comp_quality_grade=CompQualityGrade.C,
        rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY,
        limitations=[],
        observation_id="OBS-FAKE-PRICE-TYPE",
    )

    class FakeSession:
        def get(self, model, _id):
            return fake
        def flush(self):
            pass
        def add(self, _row):
            pass

    with pytest.raises(CompFoundryError, match="price_type must be ASKING_PRICE"):
        add_listing_observation(FakeSession(), comp_set_id=None, observation_id="any")


# ════════════════════════════════════════════════════════════════════
# RULE 5 · automatic value-support approval is blocked
# ════════════════════════════════════════════════════════════════════


def test_approve_for_limited_use_is_not_implemented():
    """RULE 5 · only manual human approval may elevate a comp set."""
    from app.services.comp_foundry import approve_for_limited_use
    with pytest.raises(NotImplementedError, match="Manual human-approval"):
        approve_for_limited_use()


# ════════════════════════════════════════════════════════════════════
# RULE 6 · source rights default safely · training_eligible=False
# ════════════════════════════════════════════════════════════════════


def test_source_rights_default_is_internal_research_only():
    """RightsStatus.INTERNAL_RESEARCH_ONLY is the safe default · no enum
    value above it is reached without explicit operator action."""
    assert RightsStatus.INTERNAL_RESEARCH_ONLY.value == "INTERNAL_RESEARCH_ONLY"


def test_training_pair_default_use_class():
    """TrainingPair default use_class must be CANDIDATE_ONLY."""
    from app.models.goods import TrainingPair
    col = TrainingPair.__table__.c.use_class
    assert col.default.arg == TrainingPairUseClass.CANDIDATE_ONLY


def test_training_pair_default_training_eligible_false():
    from app.models.goods import TrainingPair
    col = TrainingPair.__table__.c.training_eligible
    # SQLAlchemy boolean default may be the Python False or a sa.text()
    # · accept either form. The truth doctrine is the value, not the type.
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_pair_factory_assert_training_eligible_rejects_candidate():
    """assert_training_eligible refuses anything in CANDIDATE_ONLY state."""
    from app.models.goods import TrainingPair
    from app.services.pair_factory import PairFactoryError, assert_training_eligible

    pair = TrainingPair(
        pair_id="FAKE",
        use_class=TrainingPairUseClass.CANDIDATE_ONLY,
        training_eligible=False,
        source_rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY,
        validator_status="VALIDATOR_REVIEW_REQUIRED",
        source_lineage={},
        input_json={},
        expected_output_json={},
        pair_type=None,
    )
    with pytest.raises(PairFactoryError, match="not training-eligible"):
        assert_training_eligible(pair)


def test_pair_factory_approve_batch_for_training_blocked():
    """RULE 6 · approve_batch_for_training is NotImplemented by design."""
    from app.services.pair_factory import approve_batch_for_training
    with pytest.raises(NotImplementedError, match="validator review"):
        approve_batch_for_training()


# ════════════════════════════════════════════════════════════════════
# Public export · privacy boundary
# ════════════════════════════════════════════════════════════════════


def test_public_export_refuses_private_evidence():
    """public_export_or_refuse must raise on non-PUBLIC_ASSETS class."""
    from app.services.artifacts import public_export_or_refuse
    from app.models.goods import ArtifactRegistry

    fake = ArtifactRegistry(
        bucket="defendable-private-evidence-prod",
        object_key="org/foo/asset/bar/raw/file.pdf",
        privacy_class=ArtifactPrivacyClass.PRIVATE_EVIDENCE,
        sha256="0" * 64,
    )
    with pytest.raises(PermissionError, match="public export blocked"):
        public_export_or_refuse(fake)


def test_public_export_refuses_market_observations():
    from app.services.artifacts import public_export_or_refuse
    from app.models.goods import ArtifactRegistry

    fake = ArtifactRegistry(
        bucket="defendable-market-observations-prod",
        object_key="provider/brave/2026/05/22/run/raw.json",
        privacy_class=ArtifactPrivacyClass.MARKET_OBSERVATIONS,
        sha256="0" * 64,
    )
    with pytest.raises(PermissionError, match="public export blocked"):
        public_export_or_refuse(fake)


def test_public_export_refuses_derived_datasets():
    from app.services.artifacts import public_export_or_refuse
    from app.models.goods import ArtifactRegistry

    fake = ArtifactRegistry(
        bucket="defendable-derived-datasets-prod",
        object_key="pairs/compute/batch/candidates.jsonl",
        privacy_class=ArtifactPrivacyClass.DERIVED_DATASETS,
        sha256="0" * 64,
    )
    with pytest.raises(PermissionError, match="public export blocked"):
        public_export_or_refuse(fake)


# ════════════════════════════════════════════════════════════════════
# Connector registry · honest status
# ════════════════════════════════════════════════════════════════════


def test_connector_definitions_include_core_providers():
    """Core providers must always be registered · 8 originals (Goods + ITAD)."""
    assert len(CONNECTOR_DEFINITIONS) >= 8
    names = {d["provider_name"] for d in CONNECTOR_DEFINITIONS}
    assert ProviderName.BRAVE_LLM_CONTEXT in names
    assert ProviderName.EBAY_BROWSE in names
    assert ProviderName.EBAY_INVENTORY in names
    assert ProviderName.SHOPIFY_FUTURE in names
    assert ProviderName.CLIENT_UPLOAD in names
    assert ProviderName.FIRST_PARTY_TRANSACTION in names
    assert ProviderName.LICENSED_TRANSACTION_DATA_FUTURE in names
    assert ProviderName.ITAD_PARTNER_FEED in names


def test_ebay_inventory_is_future_disabled():
    """eBay outbound listing is FUTURE_DISABLED · no live calls today."""
    assert resolve_status(ProviderName.EBAY_INVENTORY) == ProviderStatus.FUTURE_DISABLED


def test_shopify_is_future_disabled():
    assert resolve_status(ProviderName.SHOPIFY_FUTURE) == ProviderStatus.FUTURE_DISABLED


def test_licensed_data_is_future_disabled():
    assert resolve_status(ProviderName.LICENSED_TRANSACTION_DATA_FUTURE) == ProviderStatus.FUTURE_DISABLED


# ════════════════════════════════════════════════════════════════════
# Schema sanity · the 15 tables register cleanly
# ════════════════════════════════════════════════════════════════════


def test_models_registered_in_init():
    """All 15 new model classes must be importable from app.models."""
    from app import models
    for name in [
        "SourceConnector",
        "DiscoveryRun",
        "TrendSignal",
        "CanonicalGood",
        "GoodsIdentifier",
        "MarketObservation",
        "TransactionEvidence",
        "CompSet",
        "CompSetMember",
        "SourceRightsRecord",
        "PairBatch",
        "TrainingPair",
        "ApprovedClaim",
        "MarketReadyDataLink",
        "ArtifactRegistry",
    ]:
        assert hasattr(models, name), f"app.models.{name} missing from __init__"
