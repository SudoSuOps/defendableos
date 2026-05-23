"""Structured intake derivation · turns free-text + 5-dimension capture
into machine-readable authority / permission / sensitive-access flags.

The Intake Agent (intake_agent.py) collects the 5 ClawCheck dimensions
plus a free-text operator_attested_context. This module performs a
deterministic, evidence-specific projection of those captures into the
structured flags the risk engine + bakery pair factory rely on.

NO inference is performed by a model here. Every flag is derived from
explicit selections (access_surfaces) or from grep-style detection in
operator_attested_context using a defendable, transparent keyword list.

Detection rules are intentionally conservative · a positive detection
must come from an affirmative phrase (e.g. "runs sudo", "GitHub push"),
NOT from a denial ("no sudo access", "no payment APIs"). This is the
same false-positive trap doctrine that bit the Validator checks twice
earlier · we will not repeat it here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ─── Detection keyword tables ─────────────────────────────────────────
# Order matters · longer, more specific phrases first.

_PRIVILEGED_EXECUTION = [
    r"\bsudo\b",
    r"\broot shell\b",
    r"\bprivileged\b",
    r"\bsystemd\b",
    r"\bservice restart\b",
    r"\brestart services\b",
]
_CODE_PUSH = [
    r"\bgithub push(es)?\b",
    r"\bgit push\b",
    r"\bpushes? code\b",
    r"\bcommit(s)? to (the )?main\b",
]
_INFRASTRUCTURE_WRITE = [
    r"\binfrastructure\b",
    r"\bcloud(flare)? tunnel\b",
    r"\bvast\.ai\b",
    r"\bdashboard/api\b",
    r"\bedit(s|ing)? configuration\b",
    r"\bconfig(uration)? files?\b",
    r"\bconfig writes?\b",
]
_CREDENTIAL_ACCESS = [
    r"\bcredentials?\b",
    r"\bssh (config(uration)?|keys?)\b",
    r"\b\.env files?\b",
    r"\bsecrets?\b",
    r"\btokens?\b",
    r"\bapi keys?\b",
]
_PAYMENT_ACTION = [
    r"\brefund(s|ed|ing)?\b",
    r"\bpayment( ?api| ?link)?\b",
    r"\bissue(s|d)? refund\b",
    r"\bcharge(s|d)? customer\b",
]
_OUTBOUND_MESSAGING_AUTONOMOUS = [
    r"\bsend(s|ing)? (customer )?emails?( without)?\b",
    r"\bemail(s)? customers? (without )?(human )?(approval|review)\b",
    r"\boutbound (customer )?(email|message)s?\b",
    r"\bautonomous (customer )?(email|message)\b",
]
_TICKET_DELETION = [
    r"\bdelete(s|d)? (completed )?support tickets?\b",
    r"\bticket deletion\b",
    r"\bpermanent(ly)? delete\b",
]
_SHIPPING_ADDRESS_WRITE = [
    r"\bshipping address(es)?\b",
    r"\baddress update(s)?\b",
    r"\baddress changes?\b",
]
_UNTRUSTED_INSTRUCTION_CHANNEL = [
    r"\buntrusted (inbound )?instructions?\b",
    r"\buntrusted (channel|message|input)s?\b",
    r"\binstructions? through discord\b",
    r"\bdiscord(,)?( including untrusted)?\b",
    r"\btelegram(,)?( including untrusted)?\b",
]
_PERSISTENT_MEMORY = [r"\bpersistent memory\b", r"\bmemory enabled\b"]
_CUSTOMER_DATA = [
    r"\bcustomer (names?|emails?|addresses?|data|contact)\b",
    r"\border histor(y|ies)\b",
    r"\binvoices?\b",
    r"\brefund requests?\b",
    r"\blead(s)? (information)?\b",
    r"\bsubmitted project details\b",
]
_BUSINESS_DOCUMENTS = [
    r"\b(uploaded )?pdfs?\b",
    r"\b(uploaded )?(business )?documents?\b",
    r"\b(uploaded )?screenshots?\b",
]


# Negation guard · sentence-level scan that suppresses keyword hits when
# the same sentence/clause begins with a negation token.
_NEGATION_TOKENS = (
    "no ", "not ", "never ", "without ", "absent", "not allowed",
    "is not", "are not", "doesn't", "does not", "cannot", "can't",
    "restrictions:", "restriction:",
)


def _affirmative_match(text: str, patterns: list[str]) -> bool:
    """Match any pattern · but only when the surrounding clause is NOT a
    negation. We split on common clause separators and check each clause
    independently. A pattern hit inside a clause beginning with a
    negation token is suppressed.
    """
    if not text:
        return False
    lowered = text.lower()
    # Split on sentence ends, semicolons, dashes, bullet/list openings.
    clauses = re.split(r"[\.\;\n\r]|(?:\s-\s)|(?:\s—\s)", lowered)
    for clause in clauses:
        c = clause.strip()
        if not c:
            continue
        if any(c.startswith(tok) for tok in _NEGATION_TOKENS):
            continue
        # Also handle short suppressed phrases like "no X" mid-clause
        for pat in patterns:
            for m in re.finditer(pat, c):
                start = max(0, m.start() - 20)
                window = c[start:m.start()]
                if any(neg in window for neg in ("no ", "not ", "never ", "without ", "doesn't ", "does not ", "absent ")):
                    continue
                return True
    return False


@dataclass
class StructuredIntake:
    """Machine-readable projection of an intake capture.

    Field naming mirrors the founder-supplied schema. Defaults are
    explicit and conservative · unknown is False (not "unknown") so the
    risk engine can reason monotonically.
    """

    # 5 captured dimensions (verbatim)
    agent_name: str | None = None
    worker_kind: str | None = None
    deployment_target: str | None = None
    model_provider: str | None = None
    memory_enabled: bool = False
    access_surfaces: list[str] = field(default_factory=list)

    # Derived structured permissions
    permissions: dict[str, bool] = field(default_factory=dict)

    # Derived sensitive access
    sensitive_access: dict[str, bool] = field(default_factory=dict)

    # Derived approval boundaries (true = human approval REQUIRED for that action class)
    human_approval_boundaries: dict[str, bool] = field(default_factory=dict)

    # Derived instruction channels (each entry is a {channel, trust_level} dict)
    instruction_channels: list[dict[str, str]] = field(default_factory=list)

    # Detection trace · which keyword tables fired
    detection_trace: dict[str, bool] = field(default_factory=dict)

    # Original operator text preserved (private)
    operator_attested_context: str = ""

    # Consent (defaults conservative · false unless operator opts in)
    consent: dict[str, bool] = field(default_factory=lambda: {
        "store_for_snapshot": True,
        "allow_deidentified_training_use": False,
        "allow_evaluation_use": False,
    })

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "worker_kind": self.worker_kind,
            "deployment_target": self.deployment_target,
            "model_provider": self.model_provider,
            "memory_enabled": self.memory_enabled,
            "access_surfaces": list(self.access_surfaces),
            "permissions": dict(self.permissions),
            "sensitive_access": dict(self.sensitive_access),
            "human_approval_boundaries": dict(self.human_approval_boundaries),
            "instruction_channels": list(self.instruction_channels),
            "detection_trace": dict(self.detection_trace),
            "operator_attested_context": self.operator_attested_context,
            "consent": dict(self.consent),
        }


def derive_structured_intake(
    *,
    agent_name: str | None,
    worker_kind: str | None,
    deployment_target: str | None,
    model_provider: str | None,
    memory_enabled: bool | None,
    access_surfaces: list[str] | None,
    operator_attested_context: str | None,
    consent: dict[str, bool] | None = None,
) -> StructuredIntake:
    """Build a StructuredIntake from raw capture + free-text projection."""

    text = operator_attested_context or ""
    surfaces = set(access_surfaces or [])

    # ── Permission detection (combine explicit surface + text projection) ──
    has_shell = "Shell" in surfaces
    has_payments = "Payments" in surfaces
    has_files = "Files" in surfaces
    has_browser = "Browser" in surfaces
    has_apis = "APIs" in surfaces
    has_email_or_msg = bool(surfaces & {"Email", "Messages"})

    privileged = has_shell and _affirmative_match(text, _PRIVILEGED_EXECUTION)
    code_push = _affirmative_match(text, _CODE_PUSH)
    infra_write = _affirmative_match(text, _INFRASTRUCTURE_WRITE)
    cred_access = _affirmative_match(text, _CREDENTIAL_ACCESS)
    payment_action = has_payments or _affirmative_match(text, _PAYMENT_ACTION)
    autonomous_outbound = _affirmative_match(text, _OUTBOUND_MESSAGING_AUTONOMOUS)
    ticket_delete = _affirmative_match(text, _TICKET_DELETION)
    address_write = _affirmative_match(text, _SHIPPING_ADDRESS_WRITE)
    untrusted_channel = _affirmative_match(text, _UNTRUSTED_INSTRUCTION_CHANNEL)
    customer_pii = _affirmative_match(text, _CUSTOMER_DATA)
    business_docs = _affirmative_match(text, _BUSINESS_DOCUMENTS)

    permissions = {
        "files_read": has_files,
        "files_write": has_files,
        "browser_use": has_browser,
        "api_use": has_apis,
        "email_draft": has_email_or_msg,
        "email_send": autonomous_outbound,
        "payment_action": payment_action,
        "shell_execute": has_shell,
        "sudo_execute": privileged,
        "service_restart": infra_write,
        "config_write": infra_write,
        "github_push": code_push,
        "infrastructure_modify": infra_write,
        "permanent_delete": ticket_delete,
        "shipping_address_write": address_write,
    }

    sensitive_access = {
        "env_files": cred_access,
        "ssh_configuration": cred_access,
        "tokens_or_credentials": cred_access,
        "customer_personal_data": customer_pii,
        "payment_data": payment_action,
        "business_documents": business_docs,
    }

    # Approval boundaries · TRUE means human approval IS required for
    # that action class. False means the agent has been granted
    # autonomous authority (which is what RefundRanger v0.1 has).
    human_approval_boundaries = {
        "external_messages": not autonomous_outbound,
        "payment_actions": not payment_action,  # if no payment authority, boundary is trivially satisfied
        "privileged_shell_actions": not privileged,
        "infrastructure_changes": not infra_write,
    }

    instruction_channels: list[dict[str, str]] = []
    if untrusted_channel:
        # Try to identify named channels
        for ch_pattern, ch_name in (
            (r"\bdiscord\b", "Discord"),
            (r"\btelegram\b", "Telegram"),
            (r"\bemail\b", "Email"),
        ):
            if re.search(ch_pattern, text, re.IGNORECASE):
                instruction_channels.append({"channel": ch_name, "trust_level": "untrusted_inbound"})
        if not instruction_channels:
            instruction_channels.append({"channel": "Unspecified", "trust_level": "untrusted_inbound"})

    detection_trace = {
        "privileged_execution": privileged,
        "code_push": code_push,
        "infrastructure_write": infra_write,
        "credential_access": cred_access,
        "payment_action": payment_action,
        "autonomous_outbound_messaging": autonomous_outbound,
        "ticket_deletion": ticket_delete,
        "shipping_address_write": address_write,
        "untrusted_instruction_channel": untrusted_channel,
        "customer_pii_access": customer_pii,
        "business_documents_access": business_docs,
    }

    return StructuredIntake(
        agent_name=agent_name,
        worker_kind=worker_kind,
        deployment_target=deployment_target,
        model_provider=model_provider,
        memory_enabled=bool(memory_enabled),
        access_surfaces=sorted(surfaces),
        permissions=permissions,
        sensitive_access=sensitive_access,
        human_approval_boundaries=human_approval_boundaries,
        instruction_channels=instruction_channels,
        detection_trace=detection_trace,
        operator_attested_context=text,
        consent=consent or {
            "store_for_snapshot": True,
            "allow_deidentified_training_use": False,
            "allow_evaluation_use": False,
        },
    )
