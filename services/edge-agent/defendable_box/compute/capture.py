"""Phase A read-only capture · identity · system · runtime · health idle.

All capture functions degrade gracefully when a tool is absent
(returns None or marks UNSUPPORTED). The bench never installs
anything and never fails the whole run because one tool is missing.

Per docs/DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md:
  · read-only (no clocks, no power limits, no config changes)
  · no workload tests in Phase A
  · always captures tool versions
  · always records "UNSUPPORTED" with a reason when a tool is absent
"""
from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ─── helpers ───────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(args: list[str], *, timeout: int = 10) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, check=False
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return -1, "", str(exc)


def _has(tool: str) -> bool:
    return shutil.which(tool) is not None


# ─── per-tool capture ──────────────────────────────────────────────────────


def capture_nvidia_smi() -> dict[str, Any] | None:
    """Identity + idle telemetry per GPU. Returns None if nvidia-smi absent
    or driver mismatched.
    """
    if not _has("nvidia-smi"):
        return None
    rc, out, err = _run(
        [
            "nvidia-smi",
            "--query-gpu="
            "index,name,uuid,pci.bus_id,memory.total,memory.used,"
            "driver_version,vbios_version,temperature.gpu,"
            "power.draw,power.max_limit,utilization.gpu,"
            "ecc.mode.current,persistence_mode",
            "--format=csv,noheader,nounits",
        ]
    )
    if rc != 0 or not out.strip():
        return {
            "status": "MALFUNCTIONING",
            "reason": (err or out).strip()[:500],
            "captured_at": _now_iso(),
        }
    gpus: list[dict[str, Any]] = []
    headers = [
        "index", "name", "uuid", "pci_bus_id", "memory_total_mib",
        "memory_used_mib", "driver_version", "vbios_version",
        "temperature_c", "power_draw_w", "power_max_w",
        "gpu_utilization_pct", "ecc_mode", "persistence_mode",
    ]
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != len(headers):
            continue
        gpus.append(dict(zip(headers, parts)))
    return {
        "status": "AVAILABLE",
        "gpu_count": len(gpus),
        "gpus": gpus,
        "captured_at": _now_iso(),
    }


def capture_lspci_gpu() -> dict[str, Any] | None:
    """PCI enumeration of GPU/3D/Display devices."""
    if not _has("lspci"):
        return None
    rc, out, _ = _run(["lspci", "-nn"])
    if rc != 0:
        return None
    matched = [
        ln.strip()
        for ln in out.splitlines()
        if re.search(r"(VGA|3D|Display|Audio device.*HD Audio)", ln)
        and re.search(r"(NVIDIA|AMD|Intel)", ln, re.IGNORECASE)
    ]
    return {
        "status": "AVAILABLE",
        "device_lines": matched,
        "captured_at": _now_iso(),
    }


def capture_lscpu() -> dict[str, Any] | None:
    if not _has("lscpu"):
        return None
    rc, out, _ = _run(["lscpu"])
    if rc != 0:
        return None
    fields: dict[str, str] = {}
    for line in out.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return {
        "status": "AVAILABLE",
        "model_name": fields.get("Model name"),
        "vendor_id": fields.get("Vendor ID"),
        "cpu_count_logical": fields.get("CPU(s)"),
        "threads_per_core": fields.get("Thread(s) per core"),
        "cores_per_socket": fields.get("Core(s) per socket"),
        "sockets": fields.get("Socket(s)"),
        "architecture": fields.get("Architecture"),
        "byte_order": fields.get("Byte Order"),
        "cpu_max_mhz": fields.get("CPU max MHz"),
        "cpu_min_mhz": fields.get("CPU min MHz"),
        "address_sizes": fields.get("Address sizes"),
        "captured_at": _now_iso(),
    }


def capture_meminfo() -> dict[str, Any] | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    text = meminfo.read_text()
    out: dict[str, Any] = {"status": "AVAILABLE", "captured_at": _now_iso()}
    for key in ("MemTotal", "MemAvailable", "SwapTotal"):
        match = re.search(rf"^{key}:\s+(\d+)\s+kB", text, re.MULTILINE)
        if match:
            out[f"{key.lower()}_kb"] = int(match.group(1))
    return out


def capture_lsblk() -> dict[str, Any] | None:
    if not _has("lsblk"):
        return None
    rc, out, _ = _run(
        ["lsblk", "-d", "-J", "-o", "NAME,SIZE,MODEL,TYPE,ROTA,SERIAL"]
    )
    if rc != 0:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"status": "PARSE_ERROR", "raw": out[:500]}
    devices = [
        {
            "name": d.get("name"),
            "size": d.get("size"),
            "model": d.get("model"),
            "type": d.get("type"),
            "rotational": d.get("rota"),
            # serial intentionally NOT exposed at top-level public surface
            # but kept here for the PRIVATE bundle
            "serial_private": d.get("serial"),
        }
        for d in data.get("blockdevices", [])
        if d.get("type") in {"disk", "loop", "mmc"}
    ]
    return {
        "status": "AVAILABLE",
        "devices": devices,
        "captured_at": _now_iso(),
    }


def capture_ip_link() -> dict[str, Any] | None:
    if not _has("ip"):
        return None
    rc, out, _ = _run(["ip", "-br", "link"])
    if rc != 0:
        return None
    interfaces: list[dict[str, str]] = []
    for line in out.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2:
            interfaces.append({"name": parts[0], "state": parts[1]})
    return {
        "status": "AVAILABLE",
        "interfaces": interfaces,
        "captured_at": _now_iso(),
    }


def capture_dmidecode_system() -> dict[str, Any] | None:
    """Best-effort BIOS/SMBIOS read. Often requires root · skips
    gracefully without root."""
    if not _has("dmidecode"):
        return None
    rc, out, err = _run(["dmidecode", "-t", "system"])
    if rc != 0:
        return {
            "status": "UNSUPPORTED",
            "reason": err.strip()[:200] or "non-zero exit (often needs root)",
        }
    fields: dict[str, str] = {}
    for line in out.splitlines():
        if ":" in line and line.startswith("\t"):
            k, _, v = line.strip().partition(":")
            fields[k.strip()] = v.strip()
    return {
        "status": "AVAILABLE",
        "manufacturer_private": fields.get("Manufacturer"),
        "product_name_private": fields.get("Product Name"),
        "serial_number_private": fields.get("Serial Number"),
        "uuid_private": fields.get("UUID"),
        "captured_at": _now_iso(),
    }


def capture_runtime_versions() -> dict[str, Any]:
    versions: dict[str, str | None] = {}
    for tool, args in [
        ("python3", ["python3", "--version"]),
        ("docker", ["docker", "--version"]),
        ("nvcc", ["nvcc", "--version"]),
        ("nvidia-smi", ["nvidia-smi", "--version"]),
        ("dcgmi", ["dcgmi", "--version"]),
        ("uname", ["uname", "-srm"]),
    ]:
        if _has(tool):
            rc, out, err = _run(args, timeout=5)
            versions[tool] = (out or err).strip().splitlines()[0] if (out or err).strip() else None
        else:
            versions[tool] = None
    # OS release
    os_release: dict[str, str] = {}
    osr = Path("/etc/os-release")
    if osr.exists():
        for line in osr.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                os_release[k.strip()] = v.strip().strip('"')
    return {
        "captured_at": _now_iso(),
        "tool_versions": versions,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "node": platform.node(),
        },
        "os_release": {
            "id": os_release.get("ID"),
            "version_id": os_release.get("VERSION_ID"),
            "pretty_name": os_release.get("PRETTY_NAME"),
        },
    }


# ─── tier inference ────────────────────────────────────────────────────────


@dataclass
class AssetInference:
    asset_tier: str
    asset_class: str
    primary_model: str | None
    vram_gb: int | None
    form_factor: str
    reasoning: str
    notes: list[str] = field(default_factory=list)


def infer_asset(nvidia: dict[str, Any] | None, lspci: dict[str, Any] | None, lscpu: dict[str, Any] | None) -> AssetInference:
    """Place this host on the E0-E7 ladder from captured evidence.

    Conservative: when GPU is non-functional, this is E0. When GPU
    is present and functional, tier is inferred from VRAM + model name.
    Operators can always override the result.
    """
    notes: list[str] = []

    # No NVIDIA OR malfunctioning driver → E0 CPU node
    if nvidia is None or nvidia.get("status") == "MALFUNCTIONING":
        if nvidia and nvidia.get("status") == "MALFUNCTIONING":
            notes.append(f"nvidia-smi malfunctioning: {nvidia.get('reason', '')[:100]}")
        # See if there's a GPU per lspci that we just can't drive
        if lspci and any("NVIDIA" in line for line in lspci.get("device_lines", [])):
            notes.append("NVIDIA hardware detected via lspci but driver not functional · treated as E0")
        cpu_model = (lscpu or {}).get("model_name") or "Unknown CPU"
        return AssetInference(
            asset_tier="E0",
            asset_class="COMPUTE_HARDWARE",
            primary_model=cpu_model,
            vram_gb=None,
            form_factor="CPU_NODE",
            reasoning="No functional accelerator detected · CPU/orchestration node",
            notes=notes,
        )

    gpus = nvidia.get("gpus", [])
    if not gpus:
        return AssetInference(
            asset_tier="E0",
            asset_class="COMPUTE_HARDWARE",
            primary_model=None,
            vram_gb=None,
            form_factor="CPU_NODE",
            reasoning="nvidia-smi available but no GPUs reported",
            notes=notes,
        )

    primary = gpus[0]
    name = primary.get("name", "")
    try:
        vram_mib = int(primary.get("memory_total_mib", "0"))
    except (TypeError, ValueError):
        vram_mib = 0
    vram_gb = vram_mib // 1024

    # Tier inference rules
    name_upper = name.upper()
    if "JETSON" in name_upper or "ORIN" in name_upper or "XAVIER" in name_upper:
        tier = "E1"
        reasoning = "Jetson-class edge accelerator"
        form_factor = "SOM_WITH_CARRIER"
    elif "PRO 6000" in name_upper or "H100" in name_upper or "H200" in name_upper or "A100" in name_upper:
        tier = "E6"
        reasoning = f"Institutional-class accelerator ({name})"
        form_factor = "DISCRETE_CARD"
    elif "5090" in name_upper or "RTX 4500" in name_upper or "A6000" in name_upper or "A5000" in name_upper:
        tier = "E5"
        reasoning = f"Premium workstation accelerator ({name})"
        form_factor = "DISCRETE_CARD"
    elif "3090" in name_upper or "4090" in name_upper or "TITAN" in name_upper:
        tier = "E4"
        reasoning = f"Workhorse rental-class GPU ({name})"
        form_factor = "DISCRETE_CARD"
    elif vram_gb >= 24:
        tier = "E4"
        reasoning = f"24GB+ VRAM workhorse class ({name})"
        form_factor = "DISCRETE_CARD"
    elif vram_gb >= 12:
        tier = "E3"
        reasoning = f"Efficient inference class ({name})"
        form_factor = "DISCRETE_CARD"
    elif vram_gb >= 6:
        tier = "E2"
        reasoning = f"Entry local GPU ({name})"
        form_factor = "DISCRETE_CARD"
    else:
        tier = "E2"
        reasoning = f"Small GPU · classified at E2 default ({name})"
        form_factor = "DISCRETE_CARD"

    if len(gpus) > 1:
        notes.append(f"Multi-GPU host: {len(gpus)} accelerators detected. Bench targets one GPU at a time.")

    return AssetInference(
        asset_tier=tier,
        asset_class="COMPUTE_HARDWARE",
        primary_model=name,
        vram_gb=vram_gb,
        form_factor=form_factor,
        reasoning=reasoning,
        notes=notes,
    )
