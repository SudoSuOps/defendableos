"""All ORM models. Imported by alembic env.py to register with Base.metadata."""
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership
from app.models.asset import Asset, ComputeAssetProfile
from app.models.evidence import (
    EvidenceItem,
    EvidenceManifest,
    ExtractedDocument,
    EvidenceChunk,
)
from app.models.research import ResearchSession, ResearchSource
from app.models.ai import AIOutput, AIOVAnalysis
from app.models.validator import ValidatorReview
from app.models.deed import DefendableDeed
from app.models.ens import ENSIdentity
from app.models.edge import EdgeNode, EdgeUploadEvent, EdgeEnrollmentToken
from app.models.audit import AuditEvent
from app.models.productradar import (
    BrandPlacementSignal,
    BrandWatchlist,
    ConnectedStoreOutcome,
    EcommerceProductClickSignal,
    KeywordDemandSignal,
    MarginScenario,
    MarketplaceSalesResearch,
    OpportunityScoreReceipt,
    ProductOpportunity,
    ShoppingPopularitySignal,
    SocialTrendSignal,
    StoreIntelligenceObservation,
    SupplierCandidate,
)
from app.models.goods import (
    ApprovedClaim,
    ArtifactRegistry,
    CanonicalGood,
    CompSet,
    CompSetMember,
    DiscoveryRun,
    GoodsIdentifier,
    ItadFeedImportRun,
    ItadPartner,
    MarketObservation,
    MarketReadyDataLink,
    PairBatch,
    PartnerTransactionObservation,
    SourceConnector,
    SourceRightsRecord,
    TrainingPair,
    TransactionEvidence,
    TrendSignal,
)

__all__ = [
    "User",
    "Organization",
    "OrganizationMembership",
    "Asset",
    "ComputeAssetProfile",
    "EvidenceItem",
    "EvidenceManifest",
    "ExtractedDocument",
    "EvidenceChunk",
    "ResearchSession",
    "ResearchSource",
    "AIOutput",
    "AIOVAnalysis",
    "ValidatorReview",
    "DefendableDeed",
    "ENSIdentity",
    "EdgeNode",
    "EdgeUploadEvent",
    "EdgeEnrollmentToken",
    "AuditEvent",
    # Goods Intelligence
    "ApprovedClaim",
    "ArtifactRegistry",
    "CanonicalGood",
    "CompSet",
    "CompSetMember",
    "DiscoveryRun",
    "GoodsIdentifier",
    "MarketObservation",
    "MarketReadyDataLink",
    "PairBatch",
    "SourceConnector",
    "SourceRightsRecord",
    "TrainingPair",
    "TransactionEvidence",
    "TrendSignal",
    # ITAD partner lane
    "ItadFeedImportRun",
    "ItadPartner",
    "PartnerTransactionObservation",
    # ProductRadar · demand intelligence
    "ConnectedStoreOutcome",
    "KeywordDemandSignal",
    "MarginScenario",
    "MarketplaceSalesResearch",
    "OpportunityScoreReceipt",
    "ProductOpportunity",
    "ShoppingPopularitySignal",
    "SocialTrendSignal",
    "StoreIntelligenceObservation",
    "SupplierCandidate",
    "BrandWatchlist",
    "BrandPlacementSignal",
    "EcommerceProductClickSignal",
]
