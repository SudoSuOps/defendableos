# Claim → Source Trace Matrix

Doctrine: a citation in the Kimi report is **not** proof until the cited source is located and shown to support the exact claim. This matrix records the trace result for each adjudicated material claim.

| claim | category | cited by Kimi | source quality | primary located | supports exact claim | class | external-use safe |
| --- | --- | --- | --- | :-: | :-: | --- | --- |
| 0001 | product | mission spec + Dim5 | primary | ✅ | ✅ | DIRECT_EVIDENCE | ✅ |
| 0002 | product | smash telemetry | primary | ✅ | ✅ | DIRECT_EVIDENCE | ✅ |
| 0003 | product | smash telemetry | primary | ✅ | ✅ | DIRECT_EVIDENCE | ✅ |
| 0004 | product | smash+Vast telemetry | primary | ✅ | ✅ | DIRECT_EVIDENCE | ✅ |
| 0005 | neocloud | Dim5/8 + vast.ai page | primary | ✅ | ✅ | HONEY | build/outreach-prep |
| 0006 | target (Barkr) | barkr.ai page | primary | ✅ | ✅ | HONEY | build/outreach-prep |
| 0007 | competitor | blancco/spherity/equipmentwatch pages | primary | ✅ | ✅ | HONEY | internal positioning |
| 0008 | itad | official ITAD homepages | primary | ✅ | ✅ | HONEY | outreach-prep only |
| 0009 | itad (GPU-specific) | ITAD homepages — **GPU term = 0** | self-description | ✅ | ❌ | JELLY | ❌ |
| 0010 | lending ($20B) | Dim11 secondary | secondary | ❌ | ❌ | JELLY | ❌ |
| 0011 | lending ($4M gap) | single analyst | weak | ❌ | ❌ | JELLY | ❌ |
| 0012 | lending (Munich Re) | no primary | not found | ❌ | ❌ | **PROPOLIS** | ❌ |
| 0013 | lending (OCC/quarterly) | Dim11 inference | secondary | ❌ | ❌ | JELLY | ❌ |
| 0014 | market_size (ITAD $11.7B) | GM Insights/Mordor | secondary | ❌ | ❌ | JELLY | ❌ |
| 0015 | market_size (decommission) | market-research | secondary | ❌ | ❌ | JELLY | ❌ |
| 0016 | pricing (15-25% premium) | HashrateIndex/oplexa | secondary | ❌ | ❌ | JELLY | ❌ |
| 0017 | market_size (rental +40%) | SemiAnalysis | secondary | ❌ | ❌ | JELLY | ❌ |
| 0018 | customer_demand ($50-150) | inference | weak | ❌ | ❌ | JELLY | ❌ |
| 0019 | regulatory (EU DPP) | Dim6/9 ESPR | secondary | ❌ | ❌ | JELLY | ❌ |
| 0020 | compliance (HIPAA) | NPRM (proposed) | secondary | ❌ | ❌ | JELLY | ❌ |
| 0021 | compliance (ECCN) | Dim9 BIS | secondary | ❌ | ❌ | JELLY | ❌ |
| 0022 | competitor ("no competitor") | Dim6 scan | weak | ❌ | ❌ | **PROPOLIS** | ❌ |
| 0023 | target (Slyd/STS/Maxicom) | Dim7 — **domains dead** | not found | ❌ | ❌ | **PROPOLIS** | ❌ |
| 0024 | sales_strategy (sequence) | Insight10 cross-ref | auth. secondary | ❌ | ❌ | JELLY | internal only |
| 0025 | market_size ($176B Burry) | commentary | weak | ❌ | ❌ | JELLY | ❌ |

## Method note

- "Primary located" means a primary or authoritative-primary document (SEC filing, credit-agreement exhibit, regulator text, or the company's own official page) was located in this audit and read.
- For entities, the official website page was fetched and is stored under `03_market_audit/_fetched_pages/`. For dollar/market claims, no primary filing was located within scope — they trace only to secondary market-research firms or single analysts, so they remain JELLY.
- This audit had local fetched-page evidence + domain-resolution probes. It did **not** reach SEC EDGAR credit-agreement exhibits or OCC GPU-specific guidance; those remain in `verification_queue.jsonl`.
