# Product Integration Recommendations — Ranked Build Queue

Only promoted findings (DIRECT_EVIDENCE / HONEY) drive ranking. JELLY items are built as hypotheses-to-test, not as claims.

| # | build | evidence | grade | business reason | required output | effort | dependencies | claim boundary | Tribunal gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | DCPR v0.1 schema + CLI contract | smash + schemas exist | DIRECT_EVIDENCE | the product itself | finalize CLI lint (ban-list enforce) | S | none | condition-only | exists; confirm lint |
| 2 | smash RTX 5090 example receipt | smash telemetry | DIRECT_EVIDENCE | canonical demo | published example JSON+MD | S | #1 | timestamp-scoped | exists |
| 3 | GPU identity + benchmark evidence collector spec | smash + Vast | DIRECT_EVIDENCE | repeatable capture | collector spec | M | #1 | record not determine | review |
| 4 | Verified ITAD/GPU target registry | official pages | HONEY | outreach prep | registry (this audit) | S | this audit | 6 verified; GPU adjacent | done here |
| 5 | Compute comps source registry w/ quality flags | secondary comps | JELLY | future market layer | registry w/ provenance flags | M | #1 | no value output | gate before any value use |
| 6 | Object-storage layout streetledger/compute/assets/{asset_id}/ | product integrations | HONEY | books-and-records | layout (exists in v0.1) | S | #1,#2 | hash-anchored | exists |
| 7 | Public capability statement (federal-safe) | DIRECT_EVIDENCE only | HONEY | federal lane | draft using allowed vocab only | M | federal boundary doc | no JELLY/PROPOLIS | gate before publish |
| 8 | Pilot intake questionnaire (hosts/ITADs) | Stage 1/2 plan | HONEY | validation | questionnaire | S | #4 | hypothesis framing | review |
| 9 | AIOV future integration gate (condition vs value) | doctrine | HONEY | separate evidence from opinion | gate doc (exists in v0.1) | S | #1,#5 | hard separation | exists |
| 10 | Claim-verification dashboard/ledger | this audit | HONEY | track promotions | ledger of claim→class→source | M | this audit | internal | review |

## Top recommendation to Swarm
Build **#1–#4 now** (all DIRECT_EVIDENCE / HONEY, low-medium effort, no external claims). Treat **#5, #7, #8, #10** as the next wave gated on Stage-1 pilot evidence. **Do not build toward the lender lane (#Stage-3) yet** — its inputs are JELLY/PROPOLIS.
