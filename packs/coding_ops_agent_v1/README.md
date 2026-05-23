# coding_ops_agent_v1 · FOUNDATION ONLY

This is the **foundation** for the AgentGrade benchmark pack covering
**RootClaw-class** agents · coding / systems-operations agents with
shell+sudo authority and untrusted inbound instruction channels.

## Status

```yaml
pack_status: FOUNDATION_ONLY
risk_tier: HIGH
risk_class: HIGH_PRIVILEGED_OPERATIONS_COMPROMISE
deployment_status: RESTRICTED_PENDING_CONTROLS
deed_eligibility: NOT_YET_ELIGIBLE
```

The manifest exists. The adversarial-case family catalogue is documented.
Per-task and per-adversarial-case YAML/prompt files are **reserved for
the next pack build session** and are NOT yet included here.

## Adversarial case families (v0.1 catalogue)

- discord_destructive_sudo_injection
- env_file_exfiltration
- ssh_key_exfiltration
- malicious_repo_readme_injection
- unauthorized_github_push
- docker_systemd_corruption
- cloud_tunnel_reroute
- vast_ai_disruption
- memory_poisoning_preapproved_commands

## Task families (v0.1 catalogue)

- repository_review_classification (CLASSIFICATION_ONLY)
- docker_failure_diagnosis_draft (DRAFT_ONLY)
- configuration_change_proposal (DRAFT_ONLY)
- service_restart_proposal (DRAFT_ONLY)
- github_push_proposal (DRAFT_ONLY · operator approval required)
- audit_entry_immutable (retention_required=true · delete_eligible=false)

## What this pack does NOT do

- Run any agent
- Issue any deed
- Score live LLM outputs
- Promote any RootClaw-class deployment past OBSERVED until the full
  required_review_path completes

## Sibling packs

- [`packs/refund_agent_v1/`](../refund_agent_v1/) · Validator-Ready · HIGH
- [`packs/business_agent_v1/`](../business_agent_v1/) · Foundation · ELEVATED
- [`packs/compute_inspector_v1/`](../compute_inspector_v1/) · LOW
