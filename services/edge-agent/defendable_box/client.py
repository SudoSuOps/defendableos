"""HTTP client + local credential management for the Defendable Box agent."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

CREDENTIALS_PATH = Path.home() / ".defendable-box" / "credentials.json"


@dataclass
class EdgeCredentials:
    server: str
    node_id: str
    node_name: str
    edge_token: str

    def save(self) -> None:
        CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        CREDENTIALS_PATH.write_text(json.dumps(asdict(self), indent=2))
        try:
            os.chmod(CREDENTIALS_PATH, 0o600)
        except Exception:
            pass

    @classmethod
    def load(cls) -> "EdgeCredentials | None":
        if not CREDENTIALS_PATH.exists():
            return None
        try:
            data = json.loads(CREDENTIALS_PATH.read_text())
            return cls(**data)
        except Exception:
            return None


def sha256_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


class EdgeClient:
    def __init__(self, server: str, edge_token: str | None = None) -> None:
        self.server = server.rstrip("/")
        self._token = edge_token

    @classmethod
    def from_credentials(cls) -> "EdgeClient":
        creds = EdgeCredentials.load()
        if creds is None:
            raise RuntimeError("Not enrolled. Run `defendable-box enroll` first.")
        return cls(server=creds.server, edge_token=creds.edge_token)

    def _headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    def enroll(
        self,
        token: str,
        node_name: str,
        software_version: str = "0.1.0",
        hardware_summary: dict | None = None,
    ) -> EdgeCredentials:
        resp = httpx.post(
            f"{self.server}/api/v1/edge/enroll",
            json={
                "token": token,
                "node_name": node_name,
                "software_version": software_version,
                "hardware_summary": hardware_summary or {},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        body = resp.json()
        creds = EdgeCredentials(
            server=self.server,
            node_id=body["node_id"],
            node_name=node_name,
            edge_token=body["edge_token"],
        )
        creds.save()
        self._token = creds.edge_token
        return creds

    def heartbeat(self, software_version: str = "0.1.0") -> dict:
        resp = httpx.post(
            f"{self.server}/api/v1/edge/heartbeat",
            headers=self._headers(),
            json={"software_version": software_version},
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()

    def upload_evidence(
        self,
        asset_id: str,
        file_path: Path,
        evidence_type: str = "BENCHMARK_OUTPUT",
    ) -> dict:
        claimed_sha256, _ = sha256_file(file_path)
        with file_path.open("rb") as fh:
            files = {"file": (file_path.name, fh)}
            data = {
                "evidence_type": evidence_type,
                "claimed_sha256": claimed_sha256,
            }
            resp = httpx.post(
                f"{self.server}/api/v1/edge/assets/{asset_id}/evidence",
                headers=self._headers(),
                files=files,
                data=data,
                timeout=120.0,
            )
        resp.raise_for_status()
        return resp.json()
