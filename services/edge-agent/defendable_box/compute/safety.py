"""Bench safety guards · refuses to run on occupied GPUs.

Per docs/COMPUTE_BENCH_PROFILE_MATRIX.md hard rule:
  No benchmark may interfere with a customer workload.

The pre-flight uses `nvidia-smi --query-compute-apps` to detect any
active compute process and refuses to target an occupied GPU unless
the operator types the GPU's PCI Bus ID as explicit confirmation
(--force-occupied-gpu).
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass


class BenchSafetyError(RuntimeError):
    """Raised when the bench would interfere with an active workload."""


@dataclass(frozen=True)
class GpuProcess:
    gpu_index: int
    gpu_uuid: str
    pci_bus_id: str
    pid: int
    process_name: str
    used_memory_mib: int


def list_compute_processes() -> list[GpuProcess]:
    """Return every active compute process per GPU.

    Returns an empty list when nvidia-smi is unavailable, when no GPU
    is present, or when nvidia-smi errors out (driver mismatch etc.).
    Callers must NOT treat an empty list as "GPU is safe" without
    independently confirming nvidia-smi worked.
    """
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=gpu_uuid,gpu_bus_id,pid,process_name,used_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if proc.returncode != 0:
        return []

    # We also need a uuid → index map. Best-effort second call.
    index_map: dict[str, int] = {}
    try:
        idx_proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,gpu_uuid", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if idx_proc.returncode == 0:
            for line in idx_proc.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2 and parts[0].isdigit():
                    index_map[parts[1]] = int(parts[0])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    out: list[GpuProcess] = []
    for line in proc.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue
        gpu_uuid, bus_id, pid_str, name, mem_str = parts[:5]
        if not pid_str.isdigit():
            continue
        try:
            mem = int(mem_str) if mem_str.isdigit() else 0
        except ValueError:
            mem = 0
        out.append(
            GpuProcess(
                gpu_index=index_map.get(gpu_uuid, -1),
                gpu_uuid=gpu_uuid,
                pci_bus_id=bus_id,
                pid=int(pid_str),
                process_name=name,
                used_memory_mib=mem,
            )
        )
    return out


def assert_gpu_safe_to_bench(
    gpu_index: int,
    *,
    force_occupied_pci_bus_id: str | None = None,
) -> list[GpuProcess]:
    """Raise BenchSafetyError if the GPU has active compute processes.

    The caller passes `force_occupied_pci_bus_id` only when the
    operator has explicitly retyped the PCI Bus ID of the occupied
    GPU as confirmation of intent. Phase A is read-only so even
    forced runs do not actually stress the GPU · this safety guard
    is doctrine + defense-in-depth for Phase B/C.
    """
    procs = list_compute_processes()
    on_gpu = [p for p in procs if p.gpu_index == gpu_index]
    if not on_gpu:
        return []

    if force_occupied_pci_bus_id is None:
        raise BenchSafetyError(
            f"GPU {gpu_index} has {len(on_gpu)} active compute process(es). "
            f"Bench refuses to run on an occupied GPU. "
            f"To force (read-only Phase A only): "
            f"--force-occupied-gpu {on_gpu[0].pci_bus_id}"
        )

    if force_occupied_pci_bus_id.strip().lower() not in {
        on_gpu[0].pci_bus_id.strip().lower(),
        f"0000{on_gpu[0].pci_bus_id.strip().lower()}",
    }:
        raise BenchSafetyError(
            f"--force-occupied-gpu PCI Bus ID mismatch. "
            f"Expected '{on_gpu[0].pci_bus_id}', got '{force_occupied_pci_bus_id}'."
        )

    return on_gpu
