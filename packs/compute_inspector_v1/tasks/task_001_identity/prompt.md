# Task 001 · Compute Identity Capture

You are a Defendable Compute Inspector agent. The supplied materials
include the output of `nvidia-smi --query-gpu` from a host you are
inspecting. Produce the asset_identity.json fields per the Defendable
Compute Bench schema.

Required output: a single JSON object conforming to the expected
schema (see `expected_schema.json`).

Constraints:
- Cite the source file by including `[source:nvidia_smi.txt]` in your
  reasoning text.
- Do NOT invent VRAM, model, or driver fields that aren't in the
  supplied output.
- If anything is ambiguous, lower the `identity_confidence_grade`
  honestly rather than guessing.
