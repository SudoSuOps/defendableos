"""Compliance · regulatory-grade artifact store + notification handlers.

Distinct from claw-bakery storage in doctrine:
  · bakery artifacts are AgentGrade/ClawCheck evidence (operational)
  · compliance artifacts are regulator-required records (eBay Marketplace
    Account Deletion · future GDPR/CCPA SAR + delete pipelines)

Storage prefix `compliance/` is separate from `claw-bakery/` so the two
audit trails never co-mingle and so a regulator audit can scope to
compliance/ only.
"""
