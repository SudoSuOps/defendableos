"""ITAD partner-feed lane · doctrine boundary tests.

Pure-Python boundary checks for the rules encoded in
comp_foundry.add_partner_transaction_observation, the schema defaults,
and the partnership state machine. If any of these break, someone
weakened the ITAD doctrine and the PR should be rejected.
"""
import pytest

from app.models.goods import (
    ItadAgreementStatus,
    ItadAmountDisclosureType,
    ItadConditionClass,
    ItadFormFactor,
    ItadPartner,
    ItadPartnershipStatus,
    ItadTransactionType,
    PartnerTransactionObservation,
    ProviderName,
    ProviderStatus,
    RightsStatus,
    CompQualityGrade,
)
from app.services.comp_foundry import (
    CompFoundryError,
    add_partner_transaction_observation,
)
from app.services.connector_registry import CONNECTOR_DEFINITIONS, resolve_status


# ════════════════════════════════════════════════════════════════════
# Schema + enum sanity
# ════════════════════════════════════════════════════════════════════


def test_itad_provider_name_registered():
    assert ProviderName.ITAD_PARTNER_FEED.value == "ITAD_PARTNER_FEED"


def test_itad_provider_status_extensions_present():
    assert ProviderStatus.OUTREACH_PENDING.value == "OUTREACH_PENDING"
    assert ProviderStatus.OUTREACH_READY.value == "OUTREACH_READY"
    assert ProviderStatus.IN_CONVERSATION.value == "IN_CONVERSATION"
    assert ProviderStatus.AGREEMENT_REQUIRED.value == "AGREEMENT_REQUIRED"
    assert ProviderStatus.RESEARCH_VERIFIED.value == "RESEARCH_VERIFIED"


def test_rights_status_agreement_required_added():
    assert RightsStatus.AGREEMENT_REQUIRED.value == "AGREEMENT_REQUIRED"


def test_itad_partner_default_status_is_research_verified():
    """ItadPartner.partnership_status default must be RESEARCH_VERIFIED ·
    nobody enters the table claiming PRODUCTION_PARTNER by accident.
    """
    col = ItadPartner.__table__.c.partnership_status
    assert col.default.arg == ItadPartnershipStatus.RESEARCH_VERIFIED


def test_itad_partner_default_agreement_is_none():
    col = ItadPartner.__table__.c.agreement_status
    assert col.default.arg == ItadAgreementStatus.NONE


def test_itad_partner_default_rights_is_agreement_required():
    col = ItadPartner.__table__.c.rights_scope
    assert col.default.arg == RightsStatus.AGREEMENT_REQUIRED


def test_partner_observation_default_rights_is_agreement_required():
    col = PartnerTransactionObservation.__table__.c.rights_status
    assert col.default.arg == RightsStatus.AGREEMENT_REQUIRED


def test_partner_observation_default_training_eligible_false():
    col = PartnerTransactionObservation.__table__.c.training_eligible
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


def test_partner_observation_default_public_display_eligible_false():
    col = PartnerTransactionObservation.__table__.c.public_display_eligible
    default = col.default.arg
    assert default is False or str(default).lower() in {"false", "f", "0"}


# ════════════════════════════════════════════════════════════════════
# Service-boundary rules
# ════════════════════════════════════════════════════════════════════


def _fake_partner(status: ItadPartnershipStatus, agreement: ItadAgreementStatus = ItadAgreementStatus.NONE) -> ItadPartner:
    return ItadPartner(
        slug="test",
        company_name="Test ITAD Partner",
        partnership_status=status,
        agreement_status=agreement,
        rights_scope=RightsStatus.AGREEMENT_REQUIRED,
    )


def _fake_observation(
    *,
    rights_status: RightsStatus = RightsStatus.AGREEMENT_REQUIRED,
    grade: CompQualityGrade | None = None,
) -> PartnerTransactionObservation:
    return PartnerTransactionObservation(
        partner_transaction_ref="TXN-TEST-001",
        partner_id=None,  # set by FakeSession
        asset_type=None,
        manufacturer="NVIDIA",
        model="H100 80GB",
        form_factor=ItadFormFactor.SXM,
        memory_configuration="80GB HBM3",
        quantity=1,
        condition_class=ItadConditionClass.TESTED,
        transaction_type=ItadTransactionType.REMARKETING_SALE,
        amount_disclosure_type=ItadAmountDisclosureType.EXACT,
        rights_status=rights_status,
        comp_quality_grade=grade,
        training_eligible=False,
        public_display_eligible=False,
    )


def test_partner_observation_refuses_outreach_ready_partner():
    """A partner still in OUTREACH_READY has no data yet · no observation
    may flow to a comp set."""
    partner = _fake_partner(ItadPartnershipStatus.OUTREACH_READY)
    obs = _fake_observation(rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY)

    class FakeSession:
        def get(self, model, _id):
            if model is PartnerTransactionObservation:
                return obs
            if model is ItadPartner:
                return partner
            return None
        def flush(self): pass
        def add(self, _r): pass

    with pytest.raises(CompFoundryError, match="partnership_status=OUTREACH_READY"):
        add_partner_transaction_observation(
            FakeSession(),
            comp_set_id=None,
            partner_observation_id="any",
        )


def test_partner_observation_refuses_agreement_required_rights():
    """rights_status=AGREEMENT_REQUIRED is a hard refuse · the partner
    must have moved past the pre-agreement state."""
    partner = _fake_partner(ItadPartnershipStatus.IN_CONVERSATION)
    obs = _fake_observation(rights_status=RightsStatus.AGREEMENT_REQUIRED)

    class FakeSession:
        def get(self, model, _id):
            if model is PartnerTransactionObservation:
                return obs
            return partner
        def flush(self): pass
        def add(self, _r): pass

    with pytest.raises(CompFoundryError, match="AGREEMENT_REQUIRED"):
        add_partner_transaction_observation(
            FakeSession(),
            comp_set_id=None,
            partner_observation_id="any",
        )


def test_partner_observation_refuses_grade_a_directly():
    """Only validator may elevate to Grade A · service refuses A on add."""
    partner = _fake_partner(ItadPartnershipStatus.PILOT_AGREEMENT)
    obs = _fake_observation(
        rights_status=RightsStatus.INTERNAL_RESEARCH_ONLY,
        grade=CompQualityGrade.A,
    )

    class FakeSession:
        def get(self, model, _id):
            if model is PartnerTransactionObservation:
                return obs
            return partner
        def flush(self): pass
        def add(self, _r): pass

    with pytest.raises(CompFoundryError, match="cannot enter a comp set directly at Grade A"):
        add_partner_transaction_observation(
            FakeSession(),
            comp_set_id=None,
            partner_observation_id="any",
        )


def test_partner_observation_accepts_grade_b_in_conversation():
    """Happy path · IN_CONVERSATION partner + EVAL_DERIVATIVE_ALLOWED
    rights + Grade B observation can be added."""
    partner = _fake_partner(ItadPartnershipStatus.IN_CONVERSATION)
    obs = _fake_observation(
        rights_status=RightsStatus.EVAL_DERIVATIVE_ALLOWED,
        grade=CompQualityGrade.B,
    )
    added = {}

    class FakeSession:
        def get(self, model, _id):
            if model is PartnerTransactionObservation:
                return obs
            return partner
        def flush(self): pass
        def add(self, row):
            added["member"] = row

    add_partner_transaction_observation(
        FakeSession(),
        comp_set_id=None,
        partner_observation_id="any",
    )
    member = added["member"]
    assert member.quality_grade == CompQualityGrade.B
    assert "ITAD_PARTNER_PERMISSIONED_TRANSACTION" in member.limitations
    assert "GRADE_CEILING_B_UNTIL_VALIDATOR_REVIEW" in member.limitations


# ════════════════════════════════════════════════════════════════════
# Connector registry · ITAD lane registered
# ════════════════════════════════════════════════════════════════════


def test_itad_connector_in_definitions():
    """ITAD_PARTNER_FEED is registered alongside the other connectors."""
    names = {d["provider_name"] for d in CONNECTOR_DEFINITIONS}
    assert ProviderName.ITAD_PARTNER_FEED in names


def test_itad_connector_status_resolves_outreach_ready():
    """Status helper returns OUTREACH_READY · honest signal that the
    table has partners seeded but no agreement is signed."""
    assert resolve_status(ProviderName.ITAD_PARTNER_FEED) == ProviderStatus.OUTREACH_READY
