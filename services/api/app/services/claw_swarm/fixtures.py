"""Seeded demonstration fixtures for SwarmScout / RefundRanger / RootClaw.

These fixtures match the public Claw Bakery page's three example lanes.
They are used by:
  · tests/test_risk_doctrine.py (correct tier emerges per rule)
  · the public /claw-bakery page (seeded demo lane cards)
  · the bakery pair-factory test suite (representative inputs)

No real customer data lives here. Every operator_attested_context is
the exact founder-supplied description for the corresponding agent.
"""
from __future__ import annotations

from typing import Any


SWARMSCOUT_V0_1: dict[str, Any] = {
    "agent_name": "SwarmScout v0.1",
    "worker_kind": "Business Agent",
    "deployment_target": "Cloud Server",
    "model_provider": "Kimi K2.6",
    "memory_enabled": True,
    "access_surfaces": ["Files", "Messages", "Email", "Browser", "APIs"],
    "operator_attested_context": (
        "Always-on AI business assistant powered by Kimi K2.6 Thinking through an API. "
        "Runs 24/7 on a cloud server with persistent memory. Available through "
        "Discord and Telegram. Reviews incoming leads, answers basic business "
        "questions, researches prospects, summarizes uploaded documents, drafts "
        "replies, and creates internal tasks.\n\n"
        "Access: customer names, email addresses, submitted project details; "
        "uploaded PDFs and business documents; browser/search; Discord and "
        "Telegram messages; CRM API for reading lead information; email drafting "
        "tool.\n\n"
        "Authority boundaries: email drafting only; no external sending without "
        "human approval; CRM read-only; no payments; no bank accounts; no crypto "
        "wallets; no production server credentials; no permanent file deletion."
    ),
    "expected": {
        "rule_id": "ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE",
        "tier": "ELEVATED",
        "deployment_status": "TESTING_REQUIRED",
        "future_deed_path": "Defendable Agent Deed",
    },
}


REFUNDRANGER_V0_1: dict[str, Any] = {
    "agent_name": "RefundRanger v0.1",
    "worker_kind": "Sales / Support Agent",
    "deployment_target": "Cloud Server",
    "model_provider": "Kimi K2.6",
    "memory_enabled": True,
    "access_surfaces": ["Messages", "Email", "APIs", "Payments"],
    "operator_attested_context": (
        "Autonomous customer-service AI agent for an online store. Runs continuously "
        "on a cloud server using Kimi K2.6 Thinking through an API. Persistent "
        "memory enabled. Communicates through Telegram and email. Reads customer "
        "names, shipping addresses, order histories, invoices, uploaded "
        "screenshots, and refund requests.\n\n"
        "Autonomous authority: sends customer emails without human review; "
        "updates shipping addresses; generates payment links; approves and "
        "issues refunds up to $250 through a payment API; deletes completed "
        "support tickets.\n\n"
        "Restrictions: no direct bank-login access; no crypto-wallet access."
    ),
    "expected": {
        "rule_id": "HIGH_FINANCIAL_AUTONOMOUS_ACTION",
        "tier": "HIGH",
        "deployment_status": "RESTRICTED_PENDING_CONTROLS",
        "deed_eligibility": "NOT_YET_ELIGIBLE",
        "future_deed_path": "AI Work Unit Deed",
    },
}


ROOTCLAW_V0_1: dict[str, Any] = {
    "agent_name": "RootClaw v0.1",
    "worker_kind": "Coding Agent",
    "deployment_target": "My Computer",
    "model_provider": "Kimi K2.6",
    "memory_enabled": True,
    "access_surfaces": ["Files", "Messages", "Browser", "Shell", "APIs"],
    "operator_attested_context": (
        "Coding and systems-operations agent powered by Kimi K2.6 Thinking through "
        "an API. Runs locally on a workstation. Persistent memory enabled. Receives "
        "instructions through Discord, including untrusted instructions.\n\n"
        "Work: reviews repositories; diagnoses Docker failures; checks GPU rental "
        "services; edits configuration files; restarts services; runs sudo shell "
        "commands without human approval; pushes code changes to GitHub; operates "
        "against Vast.ai dashboard/API workflows; interacts with Cloudflare Tunnel "
        "configuration/dashboard/API.\n\n"
        "Access: local files; .env files; SSH configuration; GitHub credentials/"
        "tokens; Docker; systemd; cloud tunnel configuration; browser dashboards; "
        "APIs; shell with sudo.\n\n"
        "Restrictions: no bank account access; no payment API access; no "
        "crypto-wallet access."
    ),
    "expected": {
        "rule_id": "HIGH_PRIVILEGED_OPERATIONS_COMPROMISE",
        "tier": "HIGH",
        "deployment_status": "RESTRICTED_PENDING_CONTROLS",
        "deed_eligibility": "NOT_YET_ELIGIBLE",
        "future_deed_path": "AI Work Unit Deed",
    },
}


ALL_FIXTURES: dict[str, dict[str, Any]] = {
    "swarmscout_v0_1": SWARMSCOUT_V0_1,
    "refundranger_v0_1": REFUNDRANGER_V0_1,
    "rootclaw_v0_1": ROOTCLAW_V0_1,
}
