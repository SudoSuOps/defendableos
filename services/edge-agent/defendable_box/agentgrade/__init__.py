"""Defendable AgentGrade · benchmark + Tribunal + receipt assembly.

Implements the doctrine defined in:
  · docs/DEFENDABLE_AGENT_GRADE.md
  · docs/AGENT_GRADE_RECEIPT_SCHEMA.md
  · docs/AGENT_GRADE_SCORING_STANDARD.md
  · docs/TRIBUNAL_GRADING_DOCTRINE.md
  · docs/AGENT_BENCHMARK_PACK_MATRIX.md

MVP scope (this turn):
  · Tribunal rule layer complete · judge layer stub (NEUTRAL · disclosed)
  · Pack loader + executor
  · Mock agent adapter as first reference (structured-stub)
  · Receipt bundle + manifest + public-safe export
  · 5-grade scorecard computation

Doctrine guarantees enforced:
  · Rule layer can ONLY downgrade · never upgrade
  · Critical failures = PROPOLIS regardless of judge confidence
  · No composite published without all 5 component grades
  · Per-grade floors gate the deployment tier
  · public_export_or_refuse() builds the public-safe attestation
"""
