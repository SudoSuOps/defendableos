# data/compliance/ · regulatory artifact store (local-driver)

LocalDriver root for the compliance store in dev. **Gitignored** — raw
notification bodies are regulator-scope data and never enter source
control.

Layout (mirrors `s3://<private_evidence_bucket>/compliance/...` in prod):

```
compliance/
└── ebay/
    └── account-deletion/
        ├── raw-notifications/   · raw POST bodies · immutable
        ├── receipts/            · SHA-256 receipts per artifact
        ├── review-queue/        · per-event review record · lifecycle status
        ├── completed-actions/   · post-deletion/anonymization records
        ├── events/              · append-only event log
        └── idempotency/         · dedupe markers keyed by event_id
```

Reset for dev:
```bash
rm -rf data/compliance && mkdir -p data/compliance
```

Production driver:
```bash
flyctl secrets set COMPLIANCE_STORAGE_DRIVER=s3 --app defendableos-api
```
(reuses the existing `s3_private_evidence_bucket` · no new credentials).
