# Defendable Compute · 30-Day Commercial Beachhead

The first revenue lane. Lowest activation energy because the
operator already owns the asset class · ships with 5 deeded
exemplars and the AIOV/Validator chain is live on
api.defendableos.com today.

## The edge-to-rack ladder · the surface area we sell into

Defendable Compute is not a flagship-GPU-only product. It is a
ladder of useful AI compute from CPU-only nodes through rack-scale
clusters. The full ladder (E0-E7) is defined in
`COMPUTE_ASSET_TAXONOMY.md`. Summary for the beachhead:

| Tier | Asset class | First-30-day status |
|---|---|---|
| **E0** · CPU-only utility node | ZimaBoard · NAS · mini-PC · agent host | EVIDENCE_PARTIAL · ZimaBoard agent role attested · 1 candidate record |
| **E1** · Edge AI accelerator | Jetson Orin Nano / NX · Coral TPU | EVIDENCE_RICH · sigedge benchmark + uptime captured · 1 candidate record |
| **E2** · Premium edge / mobile workstation | Jetson AGX · SFF + small GPU | PROPOSED_PROOF_CASE |
| **E3** · Small-GPU workstation | RTX 3050-4060 · A2000 | PROPOSED_PROOF_CASE |
| **E4** · Workhorse GPU rig | RTX 3090 · 4090 · 5090 | DEEDED · 3090 + 5090 live |
| **E5** · Workstation Blackwell | RTX 4500 Blackwell · A6000 | PROPOSED_PROOF_CASE (4-card swarmrig-01) |
| **E6** · Institutional workstation | RTX PRO 6000 Blackwell | DEEDED · live |
| **E7** · Rack / cluster | H100/H200 SXM · multi-node | PROPOSED_PROOF_CASE · awaiting first institutional intake |

This means the beachhead has **8 product surfaces**, not 1. The
first 30 days focuses on E4-E6 because that's where deeds already
exist · but E0-E1 receipts and E2-E3 proof cases get captured in
parallel because they are cheap to produce and they expand the
visible category in market conversations.

## Why Compute first

- 3 founder-owned compute deeds already live with operator-asking
  prices (PRO 6000 $9,850 · 5090 $3,900 · 3090 $950)
- AIOV ran with live Kimi K2.6 · Brave returned real market context
  · Validator passed every check
- Receipts are SHA-256-anchored and resolvable via
  `ledger.defendableos.com`
- Same pipeline scales to 10× the catalog without schema work

## Initial customer profiles (ranked by activation cost)

### Profile 1 · GPU owners considering selling (LOWEST FRICTION)
- Solo operator with 1–4 high-end GPUs (3090 / 4090 / 5090 / RTX PRO 6000)
- Sells on r/hardwareswap · eBay · Jawa · local
- Pain: pricing is guesswork · no way to prove condition
- Offer: free Opinion of Value → paid Deed → optional sell-side package
- Estimated reachable count: thousands · find via r/hardwareswap, GPU Discord servers, Reddit r/HomeServer

### Profile 2 · AI labs / builders buying used compute
- Researchers · indie ML teams · agentic-AI startups
- Pain: don't trust eBay seller representations of GPU condition
- Offer: a Defendable Deed travels with the GPU · buyer can verify
  serial + benchmark + condition at `/verify/{slug}`
- Estimated reachable count: hundreds-low-thousands

### Profile 3 · ITAD and remarketing firms (HIGHEST DEAL SIZE)
- 8 already seeded as `OUTREACH_READY` (Alta · exIT · GreenTek · etc.)
- Pain: enterprise GPU resale needs configuration + condition + testing
  evidence that marketplace listings can't carry
- Offer: ITAD provides permissioned anonymized comps; Defendable
  provides remarketing-ready proof pages for their inventory
- Estimated reachable count: tens of firms (already enumerated)

### Profile 4 · GPU rental operators
- vast.ai · runpod · salad.com sublessor operators
- Pain: rental yield needs market context · resale value gates capex
- Offer: rental yield + market demand snapshot bundled with the asset deed
- Estimated reachable count: hundreds

### Profile 5 · Enterprise owners decommissioning AI hardware
- Companies replacing A100s with H100/H200/B200
- Companies sunsetting older workstation fleets
- Pain: book value vs market value mismatch · finance team needs
  a paperable opinion
- Offer: bulk Opinion of Value across the disposition lot ·
  Defendable Deeds support the asset transfer to a buyer
- Estimated reachable count: low-hundreds (longer cycle)

## 6 expanded product tiers · how the ladder becomes revenue

The original first-product section below remains valid for E4-E6
flagship deeds. Layered on top · the full product ladder spans 6
tiers · one per use case rather than one per asset class:

### Tier 1 · Defendable Edge Utility Record (E0-E2)
- For: edge / CPU / small-GPU asset owners
- Anchor doc: `EDGE_AI_COMPUTE_LANE.md` · `CPU_AND_SMALL_GPU_UTILITY_LANE.md`
- Score family: `CUS_EDGE_v1`
- Includes: workload-test receipt · power envelope · deployment
  attestation · privacy/offline benefit documentation
- Deliverable: signed JSON + PDF · embeds in the asset's deed
- Price: $99 single device · $49/device for fleets of 5+
- Activation: ZimaBoard agent (E0) + Jetson sigedge (E1) become the
  founder-owned proof cases within 7 days

### Tier 2 · Defendable Workhorse Utility Record (E4-E5)
- For: 3090/4090 owners considering hold/rent/sell · workstation
  GPU operators
- Anchor doc: `SECOND_LIFE_COMPUTE_STRATEGY.md` ·
  `VAST_AI_UTILIZATION_SIGNAL_RAIL.md`
- Score family: `CUS_WORKHORSE_v1`
- Includes: Vast.ai public-listing rate snapshots · founder rental
  receipts when uploaded · local-AI capability evidence · hold/rent/
  sell/redeploy/part-out recommendation
- Deliverable: signed JSON + PDF · linked to the asset's deed
- Price: $199-$299
- Activation: RTX 3090 (DDEED-DOV-COMPUTE-000003) becomes flagship

### Tier 3 · Defendable Compute Proof of Value (E4-E6)
- For: anyone selling a high-value GPU asset
- Includes: AIOV (Kimi K2.6 + Brave) · Validator 12-check ·
  OPERATOR_ASK price band · comp set when captured · deed
- Deliverable: deed + public verify URL
- Price: $199 (basic) · $499 (with sell-side package)
- Already live · 3 founder records deeded

### Tier 4 · Defendable Trade-Up Record (any E-class transition)
- For: operators upgrading · ITAD partners ingesting refresh-cycle lots
- Anchor doc: `COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md`
- Includes: outbound asset recommendation matrix · linked PoV or
  Workhorse record · operator-attested decision inputs
- Deliverable: structured Trade-Up JSON + PDF
- Price: $149-$249 standalone · $349-$799 bundled
- Activation: founder upgrading any rig becomes the first record

### Tier 5 · Defendable Complete Node Package (E5-E7)
- For: institutional buyers · ITAD partners moving complete nodes
- Includes: GPU + CPU + RAM + storage + network configuration record
  · operational test receipts · workload-class evidence · deed
- Deliverable: complete-node deed + buyer booklet + spec PDF
- Price: $499-$1,499 per node · enterprise tier for ITAD bulk
- Activation: PROPOSED_PROOF_CASE until first complete-node intake

### Tier 6 · Defendable Compute Utility Index (forthcoming)
- For: market participants needing category-level intelligence
- Anchor doc: `COMPUTE_UTILIZATION_INDEX_SPEC.md`
- Includes: per-asset-class observation cards · honest framing of
  what's captured vs missing
- Deliverable: internal report today · public index when evidence
  thresholds met
- Price: subscription tier for ITAD partners · free public surface
  once thresholds met

## 5 flagship records roadmap · what we ship next

| Record ID | Tier | Asset | Status | Target |
|---|---|---|---|---|
| DDEED-DOV-COMPUTE-EDGE-ZIMA-001 | E0 | ZimaBoard 2 832 agent | PROPOSED | Day 7 |
| DDEED-DOV-COMPUTE-EDGE-JETSON-001 | E1 | Jetson Orin Nano Super 8GB (sigedge) | PROPOSED | Day 7 |
| DDEED-DOV-COMPUTE-3090-WORKHORSE-001 | E4 | RTX 3090 Founders · Workhorse Utility | PROPOSED | Day 14 |
| DDEED-DOV-COMPUTE-RIG-4500X4-001 | E5 | swarmrig-01 · 4× RTX 4500 Blackwell · Complete Node | PROPOSED | Day 21 |
| DDEED-DOV-COMPUTE-CLUSTER-PROPOSAL-001 | E7 | proposed multi-node H100/H200 cluster | PROPOSED_PROOF_CASE | Day 30 (intake-form-only) |

The intent: by Day 30 the public catalog covers E0, E1, E4, E5, E6,
and a PROPOSED_PROOF_CASE for E7 · the full ladder is visible.

## First paid product · structured deliverable

### 1. Defendable Compute Opinion of Value (AIOV)
- AI-assisted opinion using live Kimi K2.6 narrative
- Brave-grounded market context
- Validator 12-check protocol
- Doctrine-correct draft language · withholds final value until
  human approval
- Deliverable: signed JSON + PDF · embedded in customer email or
  attached to the deed

### 2. Verified comp package
- Comp Foundry pulls listing observations (eBay Browse · when
  approved) + first-party transactions (when uploaded)
- Grade A/B comps when confirmed-sale evidence exists
- Grade C ceiling for asking-market context
- Deliverable: comp set JSON + receipt SHA-256

### 3. Rental yield / market demand snapshot
- For Profile 4 customers (rental operators)
- Brave context on demand · ProductRadar score on the GPU SKU
- Manual analyst review · written summary
- Deliverable: short PDF report

### 4. Asset condition and specification record
- Operator uploads photos · benchmarks · driver version · serial
  (private)
- Evidence manifest hashed
- Deliverable: machine-readable spec + condition record embedded
  in the deed

### 5. Defendable Deed deliverable
- The asset's permanent SHA-256-anchored record
- Public `/verify/{slug}` page with doctrine-correct lifecycle
- Resolvable forever via ledger search
- Deliverable: deed reference + public URL + integrity hash

### 6. Optional sell-side go-to-market package
- 3D showcase page (existing infrastructure)
- Buyer booklet / spec sheet PDF
- Outreach email template to typical buyer pools
- Listing copy that flows through `ApprovedClaim` permissions
- Deliverable: branded asset page + marketing assets

## Proposed pricing

| Tier | Audience | Includes | Price |
|---|---|---|---|
| **Free intake** | Anyone | Asset identity record · category classification · canonical good link · NOT a deed | $0 |
| **Paid Opinion of Value** | GPU owners + AI labs | AIOV draft · Validator receipt · 1 comp set · DRAFT deed | **$199** |
| **Sell-side package** | Owners actively selling | Above + 3D showcase page · spec sheet · buyer outreach copy · listing-ready exports | **$499** |
| **Enterprise / partner tier** | ITAD firms · decommissioning lots | Bulk processing · 10–100 deeds · API access · branded remarketing assets | **From $2,500/mo** |

Pricing rationale: $199 is below the friction threshold for a $3K–$10K asset · same logic Jawa charges sellers. $499 captures the moment of actual sale intent. $2,500 enterprise is below the cost of one in-house ops headcount for a remarketing partner.

## Data sources · available today vs blocked

### Available today
- Brave LLM Context (live · pulls real market sources for GPU pricing queries)
- Kimi K2.6 AIOV narrative (live)
- OpenAI gpt-4o secondary completion (live)
- First-party transaction uploads (CLIENT_UPLOAD connector is READY)
- Founder-owned transaction evidence (FIRST_PARTY_TRANSACTION connector is READY)
- Manual condition photos · serial captures · benchmark JSON

### Blocked (waiting on external)
- eBay Browse active-listing observations · awaits production approval
  (`EBAY_BROWSE` connector currently `NOT_CONFIGURED`)
- eBay Product Research analyst-reviewed sold data · awaits seller-account
  workflow
- Semrush demand intelligence · awaits plan signup + per-endpoint enables
- ITAD partner transaction feeds · awaits signed pilot agreements
- eBay Inventory outbound publication · awaits biz approval AND `EBAY_OUTBOUND_LISTING_ENABLED=true`

**Implication:** every paid product on the table TODAY can be delivered with Brave + Kimi + OpenAI + first-party uploads. eBay Browse adds polish; ITAD partners unlock Grade A comps; nothing blocks the first $199 sale.

## The owned hardware becomes the flagship proof case

- **NVIDIA RTX PRO 6000 Blackwell** · DDEED-DOV-COMPUTE-000001-v3 · $9,850 ask
  - Live verify page: `defendableos.com/verify/ddeed-dov-compute-000001-v3`
  - Cinematic showcase: `defendableos.com/showcase/ddeed-dov-compute-000001-v3`
  - Brass plaque etched with the deed reference + SHA-256 prefix
  - Operating history in Swarm fleet (Tier 1 Cook)
- **NVIDIA RTX 5090 ROG ASTRAL** · DDEED-DOV-COMPUTE-000002-v3 · $3,900 ask
  - Tier 2 Serve · operating in Threadripper 9970X rigs
  - 8 units in operator's inventory (per memory: $46,800 wave / 12 units)
- **NVIDIA RTX 3090 Founders Edition** · DDEED-DOV-COMPUTE-000003-v3 · $950 ask
  - Mint-condition operator-owned single unit

The pitch becomes: *"This is the deed we'd produce for your GPU. We made it for our own first."*

The 3 records are the live demo · open them in front of any prospect.

## 30-day execution calendar (revenue + comp acquisition only)

### Week 1 · Outreach + first paid sale
- **Day 1 (tomorrow)** · Send 8 ITAD outreach emails · advance contact_status
- **Day 2** · Post the RTX PRO 6000 deed link in 3 GPU-buyer communities
  (r/hardwareswap · r/HomeServer · GPU Discord)
- **Day 3** · Launch a `/get-deed` flow link from defendableos.com header ·
  one-pager landing inviting paid Opinion of Value purchases
- **Day 4** · First paid Compute OoV processed end-to-end on a customer
  GPU · validate the workflow timing (target: same-day turnaround)
- **Day 5** · First ITAD partner reply expected (response rate target: 30%)
- **Day 6–7** · Iterate the customer email template based on first sale

### Week 2 · Repeatability + comp acquisition
- **Day 8** · 3 paid OoVs delivered · log learnings
- **Day 9** · Schedule pilot agreement call with first responding ITAD partner
- **Day 10** · Walk a second customer-uploaded GPU through the pipeline ·
  capture timing for the $199 product margin model
- **Day 11–14** · Add 5 more deeds to the public catalog · sitemap auto-grows

### Week 3 · Sell-side upgrade + partner pilot
- **Day 15** · First customer pays for $499 sell-side package · uses the
  3D showcase page + buyer booklet
- **Day 16–17** · Sign first ITAD pilot data-share agreement (NDA at minimum)
- **Day 18** · First permissioned ITAD comp ingested as Grade B
- **Day 19–21** · Bulk-process first enterprise lot (10 GPUs from a single
  decommissioning source if accessible)

### Week 4 · Scale signals + close metrics loop
- **Day 22–25** · 10 paid OoVs in the rearview · derive average per-deed
  margin · refine the offer
- **Day 26–28** · ProductRadar pilot on 1 brand category from the watchlist
  (likely portable energy / EcoFlow given SwarmEnergy adjacency)
- **Day 29** · Founder review of all 5 top metrics from
  `FOUNDER_MORNING_BRIEF_2026-05-23.md`
- **Day 30** · Decide on Q3 priorities: deeper compute · CRE STNL outreach
  · or ProductRadar admin UI

## Single-sentence success criterion for Day 30

> **3 paying customers + 1 signed ITAD pilot agreement + 1 ProductRadar opportunity scored end-to-end.**

Anything less means the rails work but the offer hasn't landed.
Anything more means we're underpricing.

## Related docs

- `FOUNDER_MORNING_BRIEF_2026-05-23.md` · the 90-second exec brief
- `ITAD_OUTREACH_EXECUTION_PACK.md` · the 8 partner emails
- `PRODUCTRADAR_SIGNAL_SCORECARD.md` · the demand-side product
- `PRODUCTION_RECEIPT_INDEX_2026-05-22.md` · receipts for every claim above
- `COMPUTE_ASSET_TAXONOMY.md` · the E0-E7 ladder this beachhead spans
- `EDGE_AI_COMPUTE_LANE.md` · E1-E2 product surface
- `CPU_AND_SMALL_GPU_UTILITY_LANE.md` · E0 + E3 product surface
- `SECOND_LIFE_COMPUTE_STRATEGY.md` · E3-E5 hold/rent/sell doctrine
- `VAST_AI_UTILIZATION_SIGNAL_RAIL.md` · rental signal rail powering Tier 2
- `COMPUTE_TRADE_UP_AND_REDEPLOYMENT_LANE.md` · Tier 4 mechanics
- `COMPUTE_UTILITY_SCORE_STANDARD.md` · score families per tier
- `COMPUTE_UTILIZATION_INDEX_SPEC.md` · Tier 6 forthcoming
- `EVIDENCE_VAULT_OBJECT_STORAGE_DOCTRINE.md` · the storage architecture every deed in this beachhead points back to
- `OBJECT_STORAGE_POLICY.md` · the technical implementation reference
