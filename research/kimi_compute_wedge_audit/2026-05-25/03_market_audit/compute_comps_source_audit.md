# Compute Comps Source Audit

## Verdict
The secondary-market pricing signals are **directionally useful but all secondary-sourced**. None is a primary transaction feed. Every comp/pricing figure is **JELLY**. The product's "market comp" layer must be built as a **source-quality-flagged registry**, never as a "validated pricing index."

## Sources cited by Kimi (as captured in landscape.md)
| source | type | what it provides | quality for our use |
| --- | --- | --- | --- |
| HashrateIndex | secondary index/blog | B2B secondary GPU market coverage | secondary |
| SemiAnalysis | secondary research | rental price indices, neocloud tracking | secondary |
| oplexa.com | blog | H100 resale pricing analysis | weak/secondary |
| BigDataSupply | reseller | quote tools, buy/sell | company self-listing |
| eBay sold listings | marketplace | consumer GPU pricing signal | weak (consumer, not enterprise) |
| Reddit r/hardwareswap | forum | consumer pricing signal | weak |
| EquipmentWatch | comps/appraisal data vendor | equipment prices, serial search, APIs | secondary — **but heavy-equipment vertical, not GPUs** |

## Key findings
- **No primary transaction feed** for enterprise GPU prices was located. Asking prices (Alibaba, reseller listings) are not sold prices.
- Specific figures ($7,800 A100-40GB; $18,900 A100-80GB; H100 $25K–$40K; refurb 15–25% premium; 60–80% retention) are **JELLY** — secondary, time-sensitive, and uncorroborated against primary data.
- EquipmentWatch is a real comps/appraisal-data company but serves construction/heavy equipment; its existence does not establish a GPU comps feed.

## Product implication
Build `compute comps source registry` with an explicit `source_quality` flag per observation (primary / authoritative_secondary / secondary / self_listed / consumer). The receipt **attaches** market signals with provenance; it must **never** emit an automatic value conclusion or call itself an "index." (Consistent with product doctrine ban on "valuation"/"appraisal".)
