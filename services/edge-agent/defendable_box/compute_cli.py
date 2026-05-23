"""Defendable Compute Bench · `defendable-compute` CLI.

Phase A scope (this turn):
  · inspect   read-only identity + system + runtime capture
              produces structured JSON bundle + manifest.sha256
              + public_safe_attestation.json

Phase B/C commands (diagnose / benchmark / attest / validate /
export-public-safe / best-next-use) are stubbed with explicit
"not implemented in Phase A · spec in docs/" messages so the
operator surface is discoverable.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from defendable_box.compute import capture, classify, manifest, safety

app = typer.Typer(
    add_completion=False,
    help=(
        "Defendable Compute Bench · benchmark-attested proof of utility "
        "before Opinion of Value. Phase A: read-only identity + system "
        "capture. Phase B/C add diagnostic + workload tests."
    ),
)
console = Console()


def _generate_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"cb-{ts}-{secrets.token_hex(2)}"


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")


@app.command()
def inspect(
    output: Path = typer.Option(
        Path("./runs"),
        help="Output directory · a <run_id> subdir is created inside it",
    ),
    gpu: int = typer.Option(
        0,
        help="GPU index to inspect (Phase A is read-only · default 0)",
    ),
    scope: str = typer.Option(
        "quick",
        help="Test scope · quick · standard · extended (Phase A captures only · no workload)",
    ),
    captured_by: str = typer.Option(
        "swarm-and-bee",
        help="Org slug recorded in the public-safe attestation",
    ),
    force_occupied_gpu: str = typer.Option(
        None,
        help=(
            "Bypass occupied-GPU refusal by typing the PCI Bus ID of "
            "the GPU you intend to inspect. Phase A is read-only so even "
            "with override no workload runs · but the safety doctrine "
            "still applies."
        ),
    ),
) -> None:
    """Phase A · read-only identity + system + runtime capture.

    Writes a structured JSON receipt bundle to
    <output>/<run_id>/ with manifest.sha256 and
    public_safe_attestation.json. No workload tests. No system mutation.
    No upload.
    """
    run_id = _generate_run_id()
    run_dir = output / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # ── 1 · safety pre-flight ───────────────────────────────────────────
    try:
        occupied = safety.assert_gpu_safe_to_bench(
            gpu_index=gpu,
            force_occupied_pci_bus_id=force_occupied_gpu,
        )
        if occupied:
            console.print(
                Panel.fit(
                    f"⚠ GPU {gpu} has active compute process(es) — Phase A capture "
                    f"proceeds under explicit operator override. Phase B/C "
                    f"workload tests would still be REFUSED on this GPU.",
                    title="OCCUPIED-GPU OVERRIDE",
                    style="yellow",
                )
            )
            for proc in occupied:
                console.print(
                    f"  PID {proc.pid}  {proc.process_name}  "
                    f"({proc.used_memory_mib} MiB · {proc.pci_bus_id})"
                )
    except safety.BenchSafetyError as exc:
        console.print(Panel.fit(str(exc), title="BENCH SAFETY", style="red"))
        raise typer.Exit(2)

    # ── 2 · capture ─────────────────────────────────────────────────────
    nvidia = capture.capture_nvidia_smi()
    lspci_gpu = capture.capture_lspci_gpu()
    lscpu_data = capture.capture_lscpu()
    meminfo = capture.capture_meminfo()
    storage = capture.capture_lsblk()
    network = capture.capture_ip_link()
    dmi = capture.capture_dmidecode_system()
    runtime_env = capture.capture_runtime_versions()
    inference = capture.infer_asset(nvidia, lspci_gpu, lscpu_data)

    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── 3 · assemble bundle files ───────────────────────────────────────

    # asset_identity.json · public-safe identity only
    asset_identity = {
        "run_id": run_id,
        "asset_class": inference.asset_class,
        "asset_tier": inference.asset_tier,
        "manufacturer": (
            "NVIDIA" if nvidia and (nvidia.get("gpus") or []) else None
        ),
        "model": inference.primary_model,
        "vram_gb": inference.vram_gb,
        "form_factor": inference.form_factor,
        "host_role": (
            "INSTITUTIONAL_WORKSTATION" if inference.asset_tier in {"E5", "E6", "E7"} else "EDGE_OR_DESKTOP"
        ),
        "identity_confidence_grade": (
            "C · MODEL_SELF_REPORTED_ONLY"
            if not dmi or dmi.get("status") != "AVAILABLE"
            else "B · SYSTEM_IDENTITY_CAPTURED_NO_PRIVATE_SERIAL"
        ),
        "identity_capture_method": [
            tool for tool, data in [
                ("nvidia-smi", nvidia),
                ("lspci", lspci_gpu),
                ("lscpu", lscpu_data),
                ("dmidecode", dmi),
            ] if data and data.get("status") == "AVAILABLE"
        ],
        "captured_at": captured_at,
        "tier_inference_reasoning": inference.reasoning,
    }
    _write_json(run_dir / "asset_identity.json", asset_identity)

    # private_identity_reference.json · PRIVATE_EVIDENCE
    private_ref = {
        "run_id": run_id,
        "host_machine_hostname": runtime_env["platform"]["node"],
        "nvidia_gpus_private": (nvidia.get("gpus") if nvidia else []),
        "dmi_system_private": (dmi if dmi else {"status": "UNAVAILABLE"}),
        "captured_at": captured_at,
        "capture_environment": "operator-attested",
    }
    _write_json(run_dir / "private_identity_reference.json", private_ref)

    # system_manifest.json
    system_manifest = {
        "host": {
            "platform": runtime_env["platform"]["system"],
            "kernel": runtime_env["platform"]["release"],
            "machine": runtime_env["platform"]["machine"],
            "os": runtime_env["os_release"],
            "cpu": lscpu_data,
            "memory": meminfo,
            "storage_devices": (storage.get("devices") if storage else []),
            "network_interfaces": (network.get("interfaces") if network else []),
        },
        "accelerators": (nvidia.get("gpus") if nvidia and nvidia.get("status") == "AVAILABLE" else []),
        "lspci_devices": (lspci_gpu.get("device_lines") if lspci_gpu else []),
        "captured_at": captured_at,
    }
    _write_json(run_dir / "system_manifest.json", system_manifest)

    # runtime_environment.json · public-safe
    _write_json(run_dir / "runtime_environment.json", runtime_env)

    # health_diagnostic.json · idle snapshot only (Phase A · no diag run)
    health = {
        "health_grade": "PASS_WITH_OBSERVATIONS" if (nvidia and nvidia.get("status") == "MALFUNCTIONING") else "PASS_WITH_OBSERVATIONS",
        "diagnostic_method": ["nvidia-smi --query (idle snapshot only · no DCGM diag in Phase A)"],
        "runtime_seconds": 0,
        "phase": "A",
        "phase_a_note": (
            "Phase A captures identity + runtime + idle telemetry only. "
            "No diagnostic test was executed. Health grade reflects "
            "idle-snapshot status only."
        ),
        "nvidia_smi_status": (nvidia.get("status") if nvidia else "ABSENT"),
        "limitations": [
            "No DCGM diag run · install dcgmi for Health Grade A inputs",
            "No sustained-load test · workload utility not measured",
        ],
        "captured_at": captured_at,
    }
    _write_json(run_dir / "health_diagnostic.json", health)

    # benchmark_plan.json · Phase A · documents what WOULD run
    plan = {
        "phase": "A",
        "profile": f"{inference.asset_tier.lower()}-auto",
        "test_scope": scope,
        "workloads_planned": [],
        "phase_a_note": (
            "Phase A executed no workloads. The profile listed here is the "
            "profile that would run in Phase B/C for this asset tier · see "
            "docs/COMPUTE_BENCH_PROFILE_MATRIX.md"
        ),
        "stress_intent": "none",
        "safety_acknowledgments": [
            "not_on_rented_workload" if not occupied else "operator-override-active",
            "operator_owned",
        ],
        "captured_at": captured_at,
    }
    _write_json(run_dir / "benchmark_plan.json", plan)

    # benchmark_results.json · empty in Phase A
    results = {
        "phase": "A",
        "workload_results": [],
        "anomalies": [],
        "test_version": "compute-bench-0.1.0",
        "phase_a_note": "No workload was run. Phase B/C produces real results.",
    }
    _write_json(run_dir / "benchmark_results.json", results)

    # workload_compatibility.json · public-safe
    workload_compat = {
        "phase": "A",
        "demonstrated": [],
        "not_tested": [
            "All workloads · Phase A is identity + system capture only",
        ],
        "phase_a_note": (
            "Workload compatibility requires Phase B/C tests. The grades "
            "below reflect capture-only status."
        ),
    }
    _write_json(run_dir / "workload_compatibility.json", workload_compat)

    # validator_flags.json
    flags = []
    if nvidia and nvidia.get("status") == "MALFUNCTIONING":
        flags.append({
            "severity": "warn",
            "id": "NVIDIA_DRIVER_MALFUNCTION",
            "detail": nvidia.get("reason", "")[:300],
        })
    if not capture._has("dcgmi"):
        flags.append({
            "severity": "info",
            "id": "DCGM_NOT_AVAILABLE",
            "detail": "dcgmi not installed · Health Grade A diagnostic skipped",
        })
    if not capture._has("nvcc"):
        flags.append({
            "severity": "info",
            "id": "CUDA_TOOLKIT_NOT_AVAILABLE",
            "detail": "nvcc not installed · CUDA sample tests skipped",
        })
    for note in inference.notes:
        flags.append({"severity": "info", "id": "INFERENCE_NOTE", "detail": note})
    _write_json(run_dir / "validator_flags.json", {"flags": flags})

    # best_next_use_inputs.json · placeholders for operator-attested fields
    bnui = {
        "owner_objective": None,
        "deployment_context": None,
        "operating_cost_usd_per_month_estimate": None,
        "current_workload": (
            f"GPU {occupied[0].gpu_index} is occupied by PID {occupied[0].pid} ({occupied[0].process_name})"
            if occupied else None
        ),
        "rental_intent": None,
        "captured_owner_attestations": [
            "Phase A · operator should fill in deployment context + objective before BNUD issues",
        ],
    }
    _write_json(run_dir / "best_next_use_inputs.json", bnui)

    # evidence_classification.json
    ec = classify.evidence_classification_doc(run_dir)
    _write_json(run_dir / "evidence_classification.json", ec)

    # ── 4 · bundle manifest FIRST · covers all bundle files except
    #     manifest.sha256 + public_safe_attestation.json (which embeds
    #     the manifest hash and so must be written AFTER)
    bundle_manifest = manifest.write_manifest(run_dir)

    # ── 5 · public-safe attestation · references the manifest hash ─────
    grades = {
        "identity_confidence": asset_identity["identity_confidence_grade"],
        "health": "PASS_WITH_OBSERVATIONS (idle snapshot · Phase A)",
        "utility": "UTILITY_NOT_YET_MEASURED",
        "evidence": "C · IDENTITY_AND_RUNTIME_ONLY (Phase A · no workload receipts)",
    }
    limitations = [
        "Phase A capture only · no workload utility measured",
        "No DCGM diag run · install dcgmi for Health Grade A inputs",
        "Buyer-side re-attestation required for transfer assurance",
    ]
    public_safe = classify.public_export_or_refuse(
        asset_identity=asset_identity,
        runtime_env=runtime_env,
        grades=grades,
        benchmark_plan=plan,
        workload_compat=workload_compat,
        bundle_manifest=bundle_manifest,
        captured_by=captured_by,
        limitations=limitations,
        re_attestation_trigger="OWNERSHIP_TRANSFER · HARDWARE_RELOCATION · DRIVER_MAJOR_UPGRADE",
    )
    _write_json(run_dir / "public_safe_attestation.json", public_safe)

    # ── 6 · summary ─────────────────────────────────────────────────────
    table = Table(title=f"defendable-compute inspect · {run_id}")
    table.add_column("field")
    table.add_column("value")
    table.add_row("Asset class", asset_identity["asset_class"])
    table.add_row("Asset tier", asset_identity["asset_tier"])
    table.add_row("Model", str(asset_identity.get("model") or "—"))
    table.add_row("VRAM (GB)", str(asset_identity.get("vram_gb") or "—"))
    table.add_row(
        "Host",
        f'{runtime_env["platform"]["node"]} · {(lscpu_data or {}).get("model_name", "")[:60]}',
    )
    table.add_row(
        "Driver / CUDA",
        f'{runtime_env["tool_versions"].get("nvidia-smi") or "—"} · '
        f'{runtime_env["tool_versions"].get("nvcc") or "—"}',
    )
    console.print(table)

    grade_table = Table(show_header=False, box=None)
    grade_table.add_column("g", style="bold")
    grade_table.add_column("v")
    grade_table.add_row("IDENTITY", grades["identity_confidence"])
    grade_table.add_row("HEALTH", grades["health"])
    grade_table.add_row("UTILITY", grades["utility"])
    grade_table.add_row("EVIDENCE", grades["evidence"])
    console.print(grade_table)

    console.print(f"\n  Bundle      [bold]{run_dir}[/bold]/")
    console.print(f"  Manifest    sha256:{bundle_manifest['bundle_sha256']}")
    console.print(f"  Public safe {run_dir / 'public_safe_attestation.json'}")
    console.print(
        "\n  [yellow]⚠[/yellow]  Phase A · UTILITY grade requires Phase B/C "
        "workload tests."
    )
    console.print(
        "      This bundle is an identity + runtime + idle-health snapshot only."
    )


# ── Phase B/C stubs · documented so operators see the surface ──────────────


def _phase_bc_stub(name: str, doc: str) -> None:
    console.print(
        Panel.fit(
            f"`{name}` is documented in {doc} but NOT implemented in Phase A.\n\n"
            f"Phase A scope: identity + system + runtime capture only.\n"
            f"Phase B adds diagnostics (DCGM, smartctl, fio).\n"
            f"Phase C adds workload tests per E0-E7 profile.\n\n"
            f"Run [bold]defendable-compute inspect[/bold] for Phase A today.",
            title=f"{name} · phase B/C",
            style="cyan",
        )
    )
    raise typer.Exit(0)


@app.command()
def diagnose(asset: str = typer.Option(..., help="DefendableOS asset id"), level: str = typer.Option("quick")) -> None:
    """Diagnostic test adapter · Phase B."""
    _phase_bc_stub("diagnose", "docs/COMPUTE_BENCH_PROFILE_MATRIX.md")


@app.command()
def benchmark(
    asset: str = typer.Option(..., help="DefendableOS asset id"),
    profile: str = typer.Option(..., help="Profile id from docs/COMPUTE_BENCH_PROFILE_MATRIX.md"),
) -> None:
    """Workload utility benchmark · Phase C."""
    _phase_bc_stub("benchmark", "docs/COMPUTE_BENCH_PROFILE_MATRIX.md")


@app.command()
def attest(run: str = typer.Option(..., help="run_id")) -> None:
    """Promote a complete run to BENCHMARK_ATTESTED · Phase B."""
    _phase_bc_stub("attest", "docs/DEFENDABLE_COMPUTE_BENCH.md")


@app.command()
def validate(run: str = typer.Option(..., help="run_id")) -> None:
    """Run validator chain over a bundle · Phase B."""
    _phase_bc_stub("validate", "docs/DEFENDABLE_COMPUTE_BENCH.md")


@app.command("export-public-safe")
def export_public_safe(run: str = typer.Option(..., help="run_id")) -> None:
    """Re-derive public_safe_attestation.json from a bundle · Phase B.

    Phase A writes public_safe_attestation.json at inspect time.
    """
    _phase_bc_stub("export-public-safe", "docs/COMPUTE_BENCH_RECEIPT_SCHEMA.md")


@app.command("best-next-use")
def best_next_use(
    asset: str = typer.Option(..., help="DefendableOS asset id"),
    run: str = typer.Option(..., help="run_id"),
) -> None:
    """Generate Best Next Use Decision record · Phase B."""
    _phase_bc_stub("best-next-use", "docs/BEST_NEXT_USE_DECISION_SCHEMA.md")


if __name__ == "__main__":
    app()
