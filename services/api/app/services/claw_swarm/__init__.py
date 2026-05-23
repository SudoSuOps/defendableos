"""Defendable Claw Agent Swarm · the team-of-agents inside the platform.

Six agent roles defined in roles.py:
  Intake      · conversational ClawCheck front door
  Inspector   · routes to Compute Bench inspect for hardware
  Benchmarker · routes to AgentGrade run for agent benchmarking
  Tribunal    · per-output verdict classifier (HONEY/JELLY/PROPOLIS)
  Validator   · 12-check chain over draft records
  Deedmaker   · bundle assembly · SHA-256 · public-safe export · ENS draft

V1 ships Intake live (talks to public API) · the rest are scaffolded
with typed tool contracts and refusal-by-default behavior · validator
chain runs before any deed-draft response · per
docs/DEFENDABLE_AGENT_GRADE.md + docs/TRIBUNAL_GRADING_DOCTRINE.md.

Hard rules:
  · Every agent has a focused system prompt + typed tool contract
  · NO agent calls an external system without operator confirmation
  · NO deed draft surfaces without Validator approval
  · ALL outputs route through public_export_or_refuse()
"""
