"""Defendable AgentGrade™ · `defendable-agentgrade` CLI.

Sibling to `defendable-compute`. Same edge-agent package · same install
path · same SHA-256 + receipt-bundle discipline.

MVP commands:
  · run            execute a pack against an agent · produce a receipt bundle

Phase B/C stubs:
  · score-existing re-score an existing bundle against a different pack version
  · attest         promote a complete bundle to AGENT_ATTESTED
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from defendable_box.agentgrade.agent_adapter import MockReferenceAgent
from defendable_box.agentgrade.refund_agents import (
    ControlledRefundDraftAgent,
    UnsafeRefundAgent,
)
from defendable_box.agentgrade.refund_runner import run_refund_pack
from defendable_box.agentgrade.runner import run_pack

app = typer.Typer(
    add_completion=False,
    help=(
        "Defendable AgentGrade™ · benchmark the agent before you trust the work. "
        "MVP: run a pack against a reference agent · produce a hashed receipt bundle."
    ),
)
console = Console()


def _load_agent(agent_id: str):
    """Resolve --agent string to an adapter instance.

    Registered:
      · mock-reference-inspector-v0 · MockReferenceAgent · compute-inspector pack
      · unsafe-refund-agent          · UnsafeRefundAgent · refund-agent pack
      · controlled-refund-draft-agent · ControlledRefundDraftAgent · refund-agent pack
    """
    if agent_id in ("mock-reference-inspector-v0", "mock", "stub"):
        return MockReferenceAgent()
    if agent_id in ("unsafe-refund-agent", "unsafe"):
        return UnsafeRefundAgent()
    if agent_id in ("controlled-refund-draft-agent", "controlled"):
        return ControlledRefundDraftAgent()
    raise typer.BadParameter(
        f"Agent '{agent_id}' not registered. Available: "
        "mock-reference-inspector-v0 · unsafe-refund-agent · controlled-refund-draft-agent."
    )


def _is_refund_pack(pack_dir: Path) -> bool:
    """Auto-detect refund-style packs (presence of policy/scoring_rubric.yaml)."""
    return (pack_dir / "policy" / "scoring_rubric.yaml").exists()


@app.command()
def run(
    pack: Path = typer.Option(..., help="Path to packs/<pack_id> directory"),
    agent: str = typer.Option("mock-reference-inspector-v0", help="Agent adapter id"),
    output: Path = typer.Option(Path("./agentgrade-runs"), help="Output directory · run subdir created inside"),
    compute_deed: str = typer.Option(
        "DDEED-DOV-COMPUTE-000001-BENCH-v2",
        help="Defendable Compute Deed this run binds to (forms half of the future Work Unit deed)",
    ),
    captured_by: str = typer.Option("swarm-and-bee", help="Org slug for the deed"),
    role_lane: str = typer.Option(
        "COMPUTE_INSPECTION_DRAFT",
        help="The defined workflow lane this agent is being certified for",
    ),
    intended_workflow_boundary: str = typer.Option(
        "Drafting only · final inspection record requires human review",
        help="Explicit workflow boundary clause embedded in the deed",
    ),
    kwh_rate: float = typer.Option(0.13, help="Operator-attested local kWh rate for cost accounting"),
    judge: str = typer.Option(
        "stub",
        help="Judge provider · stub · kimi · openai · auto. Keys loaded from local .env.",
    ),
) -> None:
    """Execute a pack against an agent · produce a receipt bundle.

    Reads pack from disk · runs each task through the agent adapter ·
    applies the Tribunal rule layer · scores grades · assembles the
    bundle with SHA-256 manifest · writes public-safe attestation.

    MVP: agent = mock-reference-inspector-v0 · judge = stub.
    """
    if not pack.is_dir():
        console.print(f"[red]Pack directory not found:[/red] {pack}")
        raise typer.Exit(1)

    agent_obj = _load_agent(agent)
    output.mkdir(parents=True, exist_ok=True)

    # ── Route refund-style packs to the deterministic-policy runner ────
    if _is_refund_pack(pack) or judge == "deterministic-policy":
        console.print(
            Panel.fit(
                f"Running [bold]refund-pack[/bold] [bold]{pack.name}[/bold] against agent [bold]{agent_obj.agent_id}[/bold]\n"
                f"Output → {output}\n"
                f"Judge → deterministic-policy (no LLM call)\n"
                f"NOTE · No deed will issue from this run · Validator review required",
                title="defendable-agentgrade · run (refund-pack mode)",
                style="cyan",
            )
        )
        result = run_refund_pack(
            pack_dir=pack,
            agent=agent_obj,
            output_dir=output,
        )
        t = Table(title=f"AgentGrade · {result.run_id}")
        t.add_column("field")
        t.add_column("value")
        t.add_row("Pack", f"{result.pack_id} · {result.pack_version}")
        t.add_row("Agent", result.agent_id)
        t.add_row("Tasks", str(result.task_count))
        t.add_row("Adversarial", str(result.adversarial_count))
        t.add_row("Final verdict", f"[bold]{result.final_verdict}[/bold]")
        t.add_row("Deployment status", result.deployment_status)
        t.add_row("Deed eligibility", result.deed_eligibility)
        t.add_row("Hard fails", str(result.hard_fail_summary["total_hard_fail_conditions_triggered"]))
        t.add_row("Resisted", str(len(result.hard_fail_summary["resisted_adversarial_cases"])))
        t.add_row("Compromised", str(len(result.hard_fail_summary["compromised_adversarial_cases"])))
        t.add_row("Bundle dir", str(result.run_dir))
        t.add_row("Bundle sha256", result.bundle_sha256)
        console.print(t)
        console.print(
            "\n[dim]Doctrine seal: no deed issued · Validator review required · "
            "no training admission · receipts written immutably.[/dim]"
        )
        return

    # ── Otherwise fall through to the existing compute-inspector runner ─
    console.print(
        Panel.fit(
            f"Running pack [bold]{pack.name}[/bold] against agent [bold]{agent_obj.agent_id}[/bold]\n"
            f"Output → {output}\n"
            f"Compute deed binding → {compute_deed}\n"
            f"Role lane → {role_lane}",
            title="defendable-agentgrade · run",
            style="cyan",
        )
    )
    result = run_pack(
        pack_dir=pack,
        agent=agent_obj,
        output_dir=output,
        compute_deed_reference=compute_deed,
        captured_by=captured_by,
        role_lane=role_lane,
        intended_workflow_boundary=intended_workflow_boundary,
        kwh_rate_usd=kwh_rate,
        judge_provider=judge,
    )

    # Print summary
    table = Table(title=f"AgentGrade · {result.run_id}")
    table.add_column("field")
    table.add_column("value")
    table.add_row("Agent", agent_obj.agent_id)
    table.add_row("Pack", f"{pack.name} · {result.public_safe.get('benchmark_pack_version', '?')}")
    table.add_row("Compute deed", compute_deed)
    cap_detail = result.grades_card.get("capability", {})
    table.add_row("Tasks run", str(cap_detail.get("total", 0)))
    table.add_row("Successes", str(cap_detail.get("successes", 0)))
    console.print(table)

    grades = result.grades_card
    g_table = Table(show_header=False, box=None)
    g_table.add_column("g", style="bold")
    g_table.add_column("v")
    for key in ("capability", "truth", "safety", "numeric_structural", "efficiency", "reproducibility"):
        cell = grades.get(key, {})
        score = cell.get("score", "?")
        g_table.add_row(key.upper(), f"{score} ({cell.get('weight', 0)}%)")
    g_table.add_row("COMPOSITE", f"{grades.get('agentgrade_composite', '?')}")
    console.print(g_table)

    console.print(f"\n  Tier         [bold]{grades.get('deployment_tier', '?')}[/bold]")
    console.print(f"  Rationale    {grades.get('deployment_tier_rationale', '?')}")
    console.print(f"  Lane         {grades.get('deployment_lane', '?')}")
    console.print(f"\n  Tribunal     Honey {result.tribunal_summary.get('honey_pct', 0)}% · "
                  f"Jelly {result.tribunal_summary.get('jelly_pct', 0)}% · "
                  f"Propolis {result.tribunal_summary.get('propolis_pct', 0)}%")
    console.print(f"  Safety       {result.adversarial_summary['resisted']}/{result.adversarial_summary['adversarial_cases_total']} resisted · "
                  f"{result.adversarial_summary['compromised']} compromised · "
                  f"{result.adversarial_summary['conditional']} conditional")
    console.print(f"\n  Bundle       [bold]{result.run_dir}[/bold]/")
    console.print(f"  Manifest     sha256:{result.bundle_hash}")
    console.print(f"  Public safe  {result.run_dir / 'public_safe_attestation.json'}")

    if grades.get("pack_status_cap_applied"):
        console.print(
            "\n  [yellow]⚠[/yellow]  Pack v1.0-alpha · tier capped at OBSERVED per pack-approval doctrine."
        )


@app.command("score-existing")
def score_existing(run_id: str = typer.Option(..., help="Existing run_id to re-score")) -> None:
    """Re-score an existing bundle (Phase B · not implemented in MVP)."""
    console.print(
        Panel.fit(
            "score-existing is documented but not implemented in MVP.\n\n"
            "MVP scope: only `run` command. Phase B/C wires re-scoring,\n"
            "validator attest, export-public-safe re-derive.",
            title="not-implemented",
            style="cyan",
        )
    )
    raise typer.Exit(0)


@app.command()
def attest(run_id: str = typer.Option(..., help="Run id to promote")) -> None:
    """Promote a bundle to AGENT_ATTESTED (Phase B · not implemented in MVP)."""
    console.print(
        Panel.fit(
            "attest is documented but not implemented in MVP.\n\n"
            "MVP scope: run + bundle. Validator review + AGENT_ATTESTED\n"
            "state transition land next session.",
            title="not-implemented",
            style="cyan",
        )
    )
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
