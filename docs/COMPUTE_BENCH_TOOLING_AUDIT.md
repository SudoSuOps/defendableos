# Compute Bench · Tooling Audit

What's actually available · per environment · today. Used by the
CLI to choose which capture/diagnostic adapters to invoke and which
to skip honestly with `UNSUPPORTED_TEST_SCOPE`.

## Audit matrix

| Tool | Supported Asset Classes | What It Tests | Install/Runtime Risk | Evidence Value | MVP Use? |
|---|---|---|---|---|---|
| **nvidia-smi** | E2-E7 (any NVIDIA GPU) | Identity · driver · VRAM · power · temp · running processes | Zero · pure read | Identity Grade A/B input · Health idle snapshot · safety pre-flight | **YES · Phase A** |
| **lspci** | E0-E7 | PCI device enumeration · board IDs | Zero · pure read | Identity grade fallback when nvidia-smi unavailable · system manifest | **YES · Phase A** |
| **lscpu** | E0-E7 | CPU model · cores · threads · frequency state | Zero | system_manifest.json host.cpu | **YES · Phase A** |
| **lsblk** | E0-E7 | Storage device enumeration · sizes · rotational flag | Zero | system_manifest.json host.storage | **YES · Phase A** |
| **ip** | E0-E7 | Network interface enumeration · link state | Zero | system_manifest.json host.network | **YES · Phase A** |
| **dmidecode** | E0-E7 | DMI/SMBIOS · board serial · BIOS version · system UUID | Read · usually needs root | High-confidence host identity · private | Phase A if available · graceful skip if not |
| **uname / /etc/os-release** | E0-E7 | Kernel · OS distribution | Zero | runtime_environment.json | **YES · Phase A** |
| **docker --version** | E0-E7 | Container runtime presence + version | Zero | runtime_environment.json | **YES · Phase A** |
| **python3 --version** | E0-E7 | Interpreter availability | Zero | runtime_environment.json | **YES · Phase A** |
| **nvcc --version** | E2-E7 (only where CUDA toolkit present) | CUDA compiler version | Zero · graceful skip if absent | runtime_environment.json | **YES · Phase A** |
| **NVIDIA DCGM (dcgmi diag)** | E5-E7 (datacenter-class supported) | Comprehensive health diag · ECC · throttle reasons · sustained load | Install required · safe with `-r 1` quick diag · `-r 2` longer | **Health Grade A input** · best evidence for E6/E7 | **Phase B** (when installed) · gracefully skipped otherwise |
| **CUDA sample tests** (deviceQuery · bandwidthTest · etc.) | E2-E7 | Device enumeration verification · memory bandwidth check | Install required (CUDA samples) · safe | Confirms CUDA + memory baselines | Phase B |
| **Workload tests** (llama.cpp · vllm · stable-diffusion-webui benchmarks) | E2-E7 | Tier-appropriate workload utility · throughput · sustained behavior | **Stress · MUST warn operator** · MUST refuse on occupied GPU | **Utility Grade input** | Phase C · CLI scaffolds the adapter contract this turn |
| **fio** | E0-E7 (storage) | Disk throughput · latency | Install required · safe with read-only profile · destructive with write profile | system manifest + node deed input | Phase B · safe (read-only) profile only |
| **iperf3** | E0-E7 (network) | Network throughput · two-host test | Install required · safe · requires remote endpoint | Network grade for E7 node deeds | Phase B · operator-opt-in only |
| **Vast.ai host self-test** | E4-E6 (rental-eligible cards) | Vast.ai's host-readiness checker | External · operator-attested capture · safe | E4_WORKHORSE rental readiness | Phase B · capture operator's output |
| **jtop / tegrastats** | E1 (Jetson) | Jetson identity · power mode · thermals | Install required on Jetson · pure read | E1 Edge Utility Record evidence | Phase B (Jetson-only) |
| **smartctl** | E0-E7 (storage health) | SMART status · sector errors · power-on hours | Install required · safe | Storage grade for E7 node deeds | Phase B |
| **lshw / dmidecode -t memory** | E0-E7 | Memory module identity · capacity · speed | dmidecode needs root · lshw root | system_manifest.json host.ram | Phase A best-effort |

## Per-environment ground truth (audited 2026-05-22)

### Operator rig (Intel N150 mini-PC · this machine)

- **CPU**: Intel N150 (4 cores · x86_64)
- **GPU**: NVIDIA Quadro T1000 Mobile (TU117GLM) detected via `lspci`
- **nvidia-smi**: PRESENT but **NVML driver/library version mismatch** (reported 595.71) · **NOT FUNCTIONAL** for capture
- **DCGM**: ABSENT
- **CUDA nvcc**: ABSENT
- **lspci · lscpu · lsblk · ip · dmidecode · docker · python3**: PRESENT
- **Asset tier**: **E0** (CPU-only effective · GPU non-functional)
- **Safe MVP target**: Phase A inspect · CPU + system identity bundle · NO GPU capture (driver broken)

### SwarmRails (founder-approved E6 target)

Captured 2026-05-23 02:38 UTC via founder-supplied `nvidia-smi`:

- **GPUs**: 2× NVIDIA RTX PRO 6000 Blackwell · 96 GB each
- **GPU 0**: PCI `00000000:34:00.0` · 1 MiB used · IDLE · 16 W · 35 C · **OPEN FOR BENCH** ✅
- **GPU 1**: PCI `00000000:CA:00.0` · 566 MiB used · python3 PID 1335108 active · **OFF-LIMITS** ❌
- **Driver**: 590.48.01 (functional)
- **CUDA**: 13.1
- **CPU**: Xeon Sapphire Rapids ("cracked" per founder)
- **Hostname**: swarmrails
- **User**: swarm
- **Asset tier**: **E6**
- **Safety constraint**: `--gpu 0` only · pre-flight refuses GPU 1 unless `--force-occupied-gpu` + PCI Bus ID confirmation
- **Tooling expected present**: nvidia-smi · lspci · lscpu · lsblk · ip · python3 · docker (likely · per typical workstation install)
- **Tooling to verify on first run**: DCGM (`dcgmi`) · nvcc · CUDA samples · dmidecode root access

## Hard rule: never install during a bench run

The CLI **never installs anything**. If a tool is absent, the
corresponding capture is skipped, marked `UNSUPPORTED_TEST_SCOPE`
in the health/utility grade, and a `validator_flag` is added with
the absent tool's name. The operator chooses whether to install +
re-run · the bench never mutates the environment.

## Hard rule: never run on occupied hardware

Per [`COMPUTE_BENCH_PROFILE_MATRIX.md`](./COMPUTE_BENCH_PROFILE_MATRIX.md):

> Before running any benchmark on a GPU currently rented, leased,
> serving a production model or otherwise occupied, stop and
> report the conflict. No benchmark may interfere with a customer
> workload.

The pre-flight `nvidia-smi --query-compute-apps` check is the
enforcement. The CLI prints the process list and refuses to run
unless `--force-occupied-gpu <bus_id>` is explicitly invoked.

## Per-tool adapter contract

Each tool integration implements:

```python
class BenchAdapter(Protocol):
    name: str
    supported_tiers: list[str]   # ["E0", "E1", ...]
    required_runtime_tools: list[str]  # ["nvidia-smi", ...]

    def probe(self) -> ProbeResult:
        """Return AVAILABLE / ABSENT / MALFUNCTIONING with a reason."""

    def capture(self, run_dir: Path, options: dict) -> CaptureResult:
        """Write artifacts into run_dir. Return list of (artifact_path, vault_class, rights_status)."""
```

Phase A ships adapters for: `nvidia-smi` · `lspci` · `lscpu` ·
`lsblk` · `ip` · `dmidecode` · `uname` · `docker` · `python3` ·
`nvcc`. All read-only.

Phase B adds: `dcgmi` · `cuda-samples` · `fio` (read-only) ·
`iperf3` · `vast-ai-host-checker` · `jtop` · `smartctl`.

Phase C adds: workload adapters per profile.

## Related docs

- [`DEFENDABLE_COMPUTE_BENCH.md`](./DEFENDABLE_COMPUTE_BENCH.md) · umbrella
- [`DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md`](./DEFENDABLE_COMPUTE_BENCH_CLI_SPEC.md) · CLI surface
- [`COMPUTE_BENCH_PROFILE_MATRIX.md`](./COMPUTE_BENCH_PROFILE_MATRIX.md) · which tool feeds which profile
- [`COMPUTE_BENCH_RECEIPT_SCHEMA.md`](./COMPUTE_BENCH_RECEIPT_SCHEMA.md) · where the captures land
