"""Claw Bakery · public + admin endpoints.

Public:
  GET  /claw-bakery/healthcheck       · driver / dir-tree / ClawForge status
  GET  /claw-bakery/public-metrics    · aggregate-only counts safe to render
  GET  /claw-bakery/seeded-fixtures   · SwarmScout · RefundRanger · RootClaw

Admin (placeholder · 501 until auth wire-up):
  GET  /claw-bakery/admin/pair-candidates
  POST /claw-bakery/admin/pair-candidates/{pair_id}/tribunal
  POST /claw-bakery/admin/clawforge/generate
  GET  /claw-bakery/admin/events

The admin layer requires the existing JWT admin pattern. v1 of this
file documents the routes and returns 501 NotImplemented until the
auth wire-up lands · we will not expose private bakery records over
an unauthenticated route.
"""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import require_platform_admin
from app.models.user import User
from app.services.claw_bakery.bakery_storage import (
    BAKERY_DIRS,
    bakery_key,
    get_bakery_store,
    safe_key_part,
)
from app.services.claw_bakery.clawforge import (
    generate_synthetic_candidate,
    is_enabled as clawforge_enabled,
    status_summary as clawforge_status_summary,
)
from app.services.claw_bakery.ingest import safe_public_metrics
from app.services.claw_bakery.pair_factory import (
    PairCandidate,
    PairFactoryError,
    TribunalLabel,
    ValidatorStatus,
    assign_tribunal_label,
    set_validator_status,
)
from app.services.claw_bakery.validator_review import (
    CHECK_REGISTRY,
    list_doctrine_checks,
    run_validator_review,
)
from app.services.claw_swarm import fixtures
from app.services.claw_swarm.risk import evaluate_intake
from app.services.claw_swarm.structured_intake import derive_structured_intake


router = APIRouter(prefix="/claw-bakery", tags=["claw-bakery"])


# ─── Public ──────────────────────────────────────────────────────────


@router.get("/healthcheck")
def bakery_healthcheck() -> dict[str, Any]:
    store = get_bakery_store()
    forge = clawforge_status_summary(store)
    return {
        "service": "claw-bakery",
        "driver": store.driver.name,
        "bakery_dirs": list(BAKERY_DIRS),
        "clawforge": {
            "enabled": forge.enabled,
            "generated_total": forge.generated_total,
            "pending": forge.pending,
            "honey": forge.honey,
            "jelly_repaired": forge.jelly_repaired,
            "propolis": forge.propolis,
            "sealed_holdouts": forge.sealed_holdouts,
        },
        "doctrine": {
            "real_time_ingestion": "allowed",
            "real_time_candidate_pair_creation": "allowed",
            "real_time_hash_receipts": "allowed",
            "synthetic_case_generation": "allowed_in_controlled_queue",
            "automatic_positive_labeling": "prohibited",
            "automatic_training_on_raw_records": "prohibited",
            "tribunal_required_before_training_admission": True,
            "validator_required_before_deed_eligibility": True,
            "raw_evidence_is_immutable": True,
            "training_requires_redaction_and_consent": True,
            "holdout_contamination": "prohibited",
        },
    }


@router.get("/public-metrics")
def public_metrics() -> dict[str, Any]:
    """Aggregate-only counts safe to render on /claw-bakery. NEVER
    exposes raw user records, agent names, or operator_attested_context.
    """
    return safe_public_metrics()


@router.get("/seeded-fixtures")
def seeded_fixtures() -> dict[str, Any]:
    """Return SwarmScout / RefundRanger / RootClaw demo fixtures with
    computed rule_ids. Used by the public /claw-bakery seeded-lanes
    section. No private user data.
    """
    out: dict[str, dict[str, Any]] = {}
    for key, fx in fixtures.ALL_FIXTURES.items():
        si = derive_structured_intake(
            agent_name=fx["agent_name"],
            worker_kind=fx["worker_kind"],
            deployment_target=fx["deployment_target"],
            model_provider=fx["model_provider"],
            memory_enabled=fx["memory_enabled"],
            access_surfaces=fx["access_surfaces"],
            operator_attested_context=fx["operator_attested_context"],
        )
        risk = evaluate_intake(si)
        out[key] = {
            "agent_name": fx["agent_name"],
            "worker_kind": fx["worker_kind"],
            "deployment_target": fx["deployment_target"],
            "tier": risk["tier"],
            "rule_id": risk["rule_id"],
            "risk_class": risk.get("risk_class"),
            "deployment_status": risk["deployment_status"],
            "deed_eligibility": risk["deed_eligibility"],
            "future_deed_path": risk.get("future_deed_path"),
            "reason": risk["reason"],
            "evidence_cited": risk["evidence_cited"],
            "recommended_path": risk["recommended_path"],
            "doctrine_note": (
                "Seeded demonstration fixture · not a real customer record. "
                "Risk derived from explicit access_surfaces + grounded "
                "keyword detection over operator_attested_context. No agent "
                "approves its own tier."
            ),
        }
    return {"fixtures": out, "fixture_count": len(out)}


# ─── Admin (placeholders · auth required before live) ────────────────


class TribunalAssignIn(BaseModel):
    label: Literal["HONEY", "JELLY", "JELLY_REPAIRED_TO_HONEY", "PROPOLIS", "QUARANTINED"]
    reason: str


@router.get("/admin/pair-candidates")
def admin_list_pair_candidates(
    bucket: Literal["pending", "honey", "jelly", "jelly-repaired",
                    "propolis-failures", "quarantined"] = "pending",
    limit: int = 50,
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """List pair candidate IDs in a label bucket · platform-admin only.

    Returns IDs + pair label + source_run_id + risk_class only · NEVER
    raw operator_attested_context · NEVER secret bits. For full pair
    detail use GET /admin/pair-candidates/{pair_id}.
    """
    store = get_bakery_store()
    keys = store.list_pair_candidates(bucket)[:limit]
    pairs = []
    for k in keys:
        try:
            doc = store.read_json(k)
            pairs.append({
                "pair_id": doc.get("pair_id"),
                "source_run_id": doc.get("source_run_id"),
                "source_type": doc.get("source_type"),
                "domain": doc.get("domain"),
                "risk_class": doc.get("risk_class"),
                "tribunal_label": doc.get("tribunal_label"),
                "validator_status": doc.get("validator_status"),
                "redaction_status": doc.get("redaction_status"),
                "eligible_for_training": doc.get("eligible_for_training"),
                "hard_fail": doc.get("hard_fail"),
                "created_at": doc.get("created_at"),
                "last_transition": doc.get("last_transition"),
            })
        except Exception:  # noqa: BLE001
            continue
    return {
        "bucket": bucket,
        "count": len(pairs),
        "pairs": pairs,
        "admin_user_id": str(admin.id),
    }


@router.get("/admin/pair-candidates/{pair_id}")
def admin_get_pair_candidate(
    pair_id: str,
    bucket: Literal["pending", "honey", "jelly", "jelly-repaired",
                    "propolis-failures", "quarantined"] = "pending",
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """Fetch a single pair candidate · full record · platform-admin only."""
    store = get_bakery_store()
    key = bakery_key("pair-candidates", bucket, f"{safe_key_part(pair_id)}.json")
    try:
        doc = store.read_json(key)
    except Exception:
        raise HTTPException(status_code=404, detail=f"pair {pair_id} not found in {bucket}")
    return {"pair": doc, "admin_user_id": str(admin.id)}


@router.post("/admin/pair-candidates/{pair_id}/tribunal")
def admin_assign_tribunal_label(
    pair_id: str,
    payload: TribunalAssignIn,
    bucket: Literal["pending", "honey", "jelly", "jelly-repaired",
                    "propolis-failures", "quarantined"] = "pending",
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """Manually assign a Tribunal label to a pair candidate.

    Doctrine-enforced: PROPOLIS → HONEY is REFUSED (PairFactoryError ·
    400). Reason text is required and stored in the transition_log.
    """
    store = get_bakery_store()
    key = bakery_key("pair-candidates", bucket, f"{safe_key_part(pair_id)}.json")
    try:
        doc = store.read_json(key)
    except Exception:
        raise HTTPException(status_code=404, detail=f"pair {pair_id} not found in {bucket}")
    # Rehydrate the dataclass · use a defensive subset of fields
    pair = PairCandidate(
        pair_id=doc["pair_id"], source_run_id=doc["source_run_id"],
        source_type=doc.get("source_type", "live_intake"),
        synthetic=bool(doc.get("synthetic", False)),
        agent_name=doc.get("agent_name"),
        domain=doc.get("domain", "unspecified"),
        risk_class=doc.get("risk_class", "UNCLASSIFIED"),
        input_record_key=doc.get("input_record_key"),
        raw_snapshot_key=doc.get("raw_snapshot_key"),
        tribunal_label=doc.get("tribunal_label", "PENDING"),
        validator_status=doc.get("validator_status", "PENDING"),
        redaction_status=doc.get("redaction_status", "PENDING"),
        operator_training_consent=bool(doc.get("operator_training_consent", False)),
        operator_evaluation_consent=bool(doc.get("operator_evaluation_consent", False)),
        eligible_for_training=bool(doc.get("eligible_for_training", False)),
        eligible_for_evaluation=bool(doc.get("eligible_for_evaluation", False)),
        eligible_for_holdout=bool(doc.get("eligible_for_holdout", False)),
        hard_fail=bool(doc.get("hard_fail", False)),
        sha256=doc.get("sha256"),
        created_at=doc.get("created_at", ""),
        last_transition=doc.get("last_transition", ""),
        transition_log=list(doc.get("transition_log", [])),
    )
    try:
        assign_tribunal_label(
            pair,
            label=TribunalLabel(payload.label),
            reason=f"{payload.reason} (by admin {admin.email})",
            store=store,
        )
    except PairFactoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "pair_id": pair.pair_id,
        "new_label": pair.tribunal_label,
        "eligible_for_training": pair.eligible_for_training,
        "transition_count": len(pair.transition_log),
        "admin_user_id": str(admin.id),
    }


@router.post("/admin/clawforge/generate")
def admin_clawforge_generate(
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """Generate one synthetic candidate · platform-admin · ClawForge must be enabled."""
    if not clawforge_enabled():
        raise HTTPException(
            status_code=409,
            detail=(
                "ClawForge is disabled. Set CLAW_BAKERY_CLAWFORGE_ENABLED=true "
                "to enable controlled synthetic-case generation."
            ),
        )
    try:
        pair = generate_synthetic_candidate()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "pair_id": pair.pair_id,
        "source_type": pair.source_type,
        "domain": pair.domain,
        "risk_class": pair.risk_class,
        "tribunal_label": pair.tribunal_label,
        "eligible_for_training": pair.eligible_for_training,
        "admin_user_id": str(admin.id),
    }


@router.get("/admin/events")
def admin_events(
    limit: int = 100,
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """List recent events from the bakery outbox · platform-admin only."""
    store = get_bakery_store()
    keys = sorted(store.list_under("events"))[-limit:]
    events = []
    for k in keys:
        try:
            doc = store.read_json(k)
            events.append({
                "event_id": doc.get("event_id"),
                "event_type": doc.get("event_type"),
                "run_id": doc.get("run_id"),
                "created_at": doc.get("created_at"),
            })
        except Exception:  # noqa: BLE001
            continue
    return {"count": len(events), "events": events, "admin_user_id": str(admin.id)}


# ─── Validator review chain ──────────────────────────────────────────


@router.get("/admin/validator-review/doctrine-checks")
def admin_list_doctrine_checks(
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """Return the 12-check doctrine catalogue · admin only · no state."""
    return {
        "check_count": len(CHECK_REGISTRY),
        "checks": list_doctrine_checks(),
        "doctrine_note": (
            "Critical checks block advancement on failure (pair → QUARANTINED). "
            "Advisory checks downgrade on failure (pair → JELLY). All checks "
            "are pure code · no LLM judgement."
        ),
        "admin_user_id": str(admin.id),
    }


@router.post("/admin/pair-candidates/{pair_id}/validator-review")
def admin_run_validator_review(
    pair_id: str,
    bucket: Literal["pending", "honey", "jelly", "jelly-repaired",
                    "propolis-failures", "quarantined"] = "pending",
    advance: bool = False,
    admin: User = Depends(require_platform_admin),
) -> dict[str, Any]:
    """Run the 12-check Validator review chain on a pair candidate.

    Returns the session record (every check + verdict). If `advance=true`
    AND overall_status=PASSED, also flips the pair's validator_status to
    PASSED and updates the tribunal label to advance_to_label. Otherwise
    the session is recorded but the pair stays as-is for human review.
    """
    store = get_bakery_store()
    key = bakery_key("pair-candidates", bucket, f"{safe_key_part(pair_id)}.json")
    try:
        doc = store.read_json(key)
    except Exception:
        raise HTTPException(status_code=404, detail=f"pair {pair_id} not found in {bucket}")
    session = run_validator_review(
        pair=doc, reviewer_user_id=str(admin.id), store=store,
    )
    if advance and session.overall_status == "PASSED":
        pair = PairCandidate(
            pair_id=doc["pair_id"], source_run_id=doc["source_run_id"],
            source_type=doc.get("source_type", "live_intake"),
            synthetic=bool(doc.get("synthetic", False)),
            agent_name=doc.get("agent_name"),
            domain=doc.get("domain", "unspecified"),
            risk_class=doc.get("risk_class", "UNCLASSIFIED"),
            input_record_key=doc.get("input_record_key"),
            raw_snapshot_key=doc.get("raw_snapshot_key"),
            tribunal_label=doc.get("tribunal_label", "PENDING"),
            validator_status=doc.get("validator_status", "PENDING"),
            redaction_status=doc.get("redaction_status", "PENDING"),
            operator_training_consent=bool(doc.get("operator_training_consent", False)),
            operator_evaluation_consent=bool(doc.get("operator_evaluation_consent", False)),
            eligible_for_training=bool(doc.get("eligible_for_training", False)),
            eligible_for_evaluation=bool(doc.get("eligible_for_evaluation", False)),
            eligible_for_holdout=bool(doc.get("eligible_for_holdout", False)),
            hard_fail=bool(doc.get("hard_fail", False)),
            sha256=doc.get("sha256"),
            created_at=doc.get("created_at", ""),
            last_transition=doc.get("last_transition", ""),
            transition_log=list(doc.get("transition_log", [])),
        )
        try:
            set_validator_status(
                pair, status=ValidatorStatus.PASSED,
                reason=f"Validator review session {session.session_id} passed all critical checks.",
                store=store,
            )
        except PairFactoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    return {
        "session_id": session.session_id,
        "pair_id": session.pair_id,
        "overall_status": session.overall_status,
        "advance_to_label": session.advance_to_label,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "reviewer_user_id": session.reviewer_user_id,
        "checks": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "severity": c.severity.value,
                "status": c.status.value,
                "reason": c.reason,
            } for c in session.checks
        ],
        "doctrine_seal": session.doctrine_seal,
        "pair_advanced": advance and session.overall_status == "PASSED",
        "admin_user_id": str(admin.id),
    }
