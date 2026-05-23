# business_agent_v1 · FOUNDATION ONLY

Foundation for the AgentGrade benchmark pack covering **SwarmScout-class**
agents · business assistants with customer data + memory + drafting
under human approval.

## Status

```yaml
pack_status: FOUNDATION_ONLY
risk_tier: ELEVATED
risk_class: ELEVATED_BUSINESS_DATA_AND_DRAFTING_EXPOSURE
deployment_status: TESTING_REQUIRED
deed_eligibility: ELIGIBLE_AFTER_REVIEW
```

## Adversarial case families (v0.1 catalogue)

- discord_intake_data_exfiltration
- uploaded_pdf_prompt_injection
- customer_email_summarization_pivot_attack
- browser_search_visit_injection
- crm_read_then_leak_to_wrong_recipient

## Task families (v0.1 catalogue)

- lead_classification (CLASSIFICATION_ONLY)
- lead_acknowledgment_draft (DRAFT_ONLY)
- document_summary (DRAFT_ONLY)
- crm_read_only_query_draft (DRAFT_ONLY)
- audit_entry_immutable

## Sibling packs

- [`packs/refund_agent_v1/`](../refund_agent_v1/) · Validator-Ready · HIGH
- [`packs/coding_ops_agent_v1/`](../coding_ops_agent_v1/) · Foundation · HIGH
- [`packs/compute_inspector_v1/`](../compute_inspector_v1/) · LOW
