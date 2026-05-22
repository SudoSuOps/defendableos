"""Defendable Box CLI · enroll / status / heartbeat / hash / upload."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from defendable_box.client import EdgeClient, EdgeCredentials, sha256_file

app = typer.Typer(add_completion=False, help="Defendable Box · local capture · verified receipts.")
console = Console()


@app.command()
def enroll(
    server: str = typer.Option(..., help="DefendableOS API base URL"),
    token: str = typer.Option(..., help="One-time enrollment token"),
    node_name: str = typer.Option("box-01", help="Friendly name for this box"),
    software_version: str = typer.Option("0.1.0", help="Agent version"),
) -> None:
    """Exchange an enrollment token for persistent edge credentials."""
    client = EdgeClient(server=server)
    creds = client.enroll(token=token, node_name=node_name, software_version=software_version)
    console.print(f"[green]✓[/green] enrolled as [bold]{creds.node_name}[/bold] ({creds.node_id})")
    console.print(f"  credentials saved to {creds.__class__.__module__}.CREDENTIALS_PATH")


@app.command()
def status() -> None:
    """Print local credential summary (no secrets shown in full)."""
    creds = EdgeCredentials.load()
    if creds is None:
        console.print("[yellow]not enrolled[/yellow]")
        raise typer.Exit(1)
    table = Table(title="Defendable Box")
    table.add_column("field")
    table.add_column("value")
    table.add_row("server", creds.server)
    table.add_row("node_name", creds.node_name)
    table.add_row("node_id", creds.node_id)
    table.add_row("edge_token", creds.edge_token[:12] + "…")
    console.print(table)


@app.command()
def heartbeat() -> None:
    """Send a heartbeat to the platform."""
    client = EdgeClient.from_credentials()
    out = client.heartbeat()
    console.print_json(json.dumps(out))


@app.command("hash-file")
def hash_file_cmd(path: Path) -> None:
    """Compute the SHA-256 of a local file without uploading."""
    digest, size = sha256_file(path)
    # Use plain print() not console.print(): Rich wraps long lines, which
    # breaks `awk '{print $1}'` and similar pipelines used in scripts/CI.
    print(f"{digest}  {size} bytes  {path}")


@app.command("upload-evidence")
def upload_evidence_cmd(
    asset_id: str = typer.Option(..., help="DefendableOS asset UUID"),
    type: str = typer.Option("BENCHMARK_OUTPUT", help="EvidenceType enum value"),
    file: Path = typer.Option(..., exists=True, readable=True, help="Path to evidence file"),
) -> None:
    """Hash + upload an evidence file with the precomputed SHA-256."""
    client = EdgeClient.from_credentials()
    out = client.upload_evidence(asset_id=asset_id, file_path=file, evidence_type=type)
    console.print_json(json.dumps(out))


@app.command("upload-benchmark")
def upload_benchmark_cmd(
    asset_id: str = typer.Option(..., help="DefendableOS asset UUID"),
    file: Path = typer.Option(..., exists=True, readable=True, help="Path to benchmark JSON"),
) -> None:
    """Alias for upload-evidence with evidence_type=BENCHMARK_OUTPUT."""
    client = EdgeClient.from_credentials()
    out = client.upload_evidence(asset_id=asset_id, file_path=file, evidence_type="BENCHMARK_OUTPUT")
    console.print_json(json.dumps(out))


if __name__ == "__main__":
    app()
