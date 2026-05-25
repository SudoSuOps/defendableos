# Extraction Log

All reads of the Kimi package were **read-only** (`python3 zipfile`); no original was modified or relocated. No bulk extraction of executable content.

## Read this audit (read-only, from the zip)
| member | how read | purpose |
| --- | --- | --- |
| `research/defendableos_insight.md` | zipfile.read → stdout | cross-dimension material claims (Insights 1-10) |
| `research/defendableos_landscape.md` | zipfile.read → stdout | market-size / pricing / rental signals + source list |

## Local evidence used (created by prior pass, not modified)
- `03_market_audit/_fetched_pages/*.html` (15 pages) — official pages for Barkr, Barker(shell), CoreWeave, and the target/competitor set. Used to verify entity existence + relevance.
- `03_market_audit/_target_probe_raw.txt` — domain-resolution probe results (HTTP status per candidate domain).
- `02_claim_audit/material_claim_registry.extraction_raw.jsonl` — prior raw extraction (590 chunks), preserved.

## Derived artifacts (this audit)
- Adjudicated `material_claim_registry.jsonl` (25 graded claims), trace matrix, weak-claims, entity-conflicts.
- Verified target registry, lane audits, product-promotion docs, tribunal verdicts, master report.
- Product `market_validation/` crosswalk; federal capability-boundary memo.

No data was written into any source directory. Cross-references use absolute/relative source paths so any claim can be re-verified against the original.
