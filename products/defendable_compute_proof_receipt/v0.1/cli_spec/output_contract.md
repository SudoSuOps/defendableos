# CLI Output Contract · v0.1

> What the operator can rely on the CLI emitting, and in what format.

## JSON output

Every subcommand's primary structured output is a JSON object validated
against the matching schema in `schemas/`. JSON output is:

- UTF-8 encoded
- `sort_keys=True` for diff stability
- `indent=2`
- LF line endings
- Trailing newline

## Markdown output

The `receipt --format md` / `receipt --format both` paths emit a
human-readable markdown twin of the receipt JSON. Markdown output:

- Has H1 receipt title
- Uses tables for tabular fields (asset identity, service state, benchmark results)
- Quotes the verdict rationale verbatim from the JSON
- Lists every `establishes` and `does_not_establish` item under a "Claim boundaries" H2
- Reproduces every artifact hash under an "Artifact hashes" H2
- Does not contain banned vocabulary (the linter runs against both formats)

## Stdout vs files

- **Stdout** is a terse progress trace: one line per phase, status, and any
  finding code. Default verbosity. `--verbose` adds command lines.
- **Files** are the canonical record. The operator may discard stdout
  freely.

## Exit-code semantics

Documented in `defendable_compute_cli_spec.md` §"Exit codes".

In CI:
- Exit 0 → publishable receipt produced (HONEY or operator-overridden JELLY)
- Exit 2 → asset failed the operating-baseline policy; not rental-ready
- Exit 3 → linter blocked the receipt; operator must fix before publish
- Exit 4 → drift detected; previously-issued receipt is now invalid
- Exit 5 → CI ran in non-interactive mode without `--confirm`; operator must
  re-run interactively or supply confirmation tokens

## Format stability

v0.1 commits to the schema definitions in `schemas/v0.1/*.schema.json`.
Field additions in v0.2 are permitted; field removals or renames require a
new schema version (`v0.2`, `v1.0`, etc.) and the receipt MUST carry a
`schema_version` field naming the version it was produced under.

Consumers that pin to v0.1 are guaranteed:
- All required v0.1 fields remain present.
- All v0.1 enums remain valid (new enum values may be added in later
  versions; consumers must accept-and-ignore-unknown).
- Hash-manifest format is stable.

## Non-output guarantees

The CLI will NOT:

- Print API keys, tokens, salts, or hardware UUIDs to stdout.
- Write API keys or secrets into any receipt or evidence file.
- Write to `/etc`, `/var/lib/docker`, `/dev/nvidia*`, or any system path
  outside the receipt directory.
- Modify systemd unit files.
- Modify `nvidia-smi` settings (power cap, persistence) without
  `--allow-baseline-restore` and per-change operator confirmation.

## Telemetry

v0.1 emits **no telemetry**. The CLI does not phone home. Receipts are
local files until the operator explicitly publishes them to DefendableLedger.
