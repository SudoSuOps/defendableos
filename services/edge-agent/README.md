# Defendable Box · edge agent

Local capture · verified receipts · sovereign evidence flow.

## Install

```bash
cd services/edge-agent
python -m venv .venv && source .venv/bin/activate
pip install -e .
defendable-box --help
```

## Commands

```bash
defendable-box enroll --server http://localhost:8000 --token <enrollment-token> --node-name box-01
defendable-box status
defendable-box heartbeat
defendable-box hash-file ./benchmark.json
defendable-box upload-evidence --asset-id <uuid> --type BENCHMARK_OUTPUT --file ./benchmark.json
defendable-box upload-benchmark --asset-id <uuid> --file ./benchmark.json
```

Credentials are stored at `~/.defendable-box/credentials.json`. Permissions
are set to `0o600`. Never commit this file.
