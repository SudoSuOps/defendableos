# Kimi Agent Swarm · DefendableOS MVP audit brief

Use this brief at https://www.kimi.com/agent-swarm (logged in with the
Swarm & Bee Kimi account that holds the monthly plan).

The Agent Swarm hosted product can spawn up to 300 sub-agents in parallel.
We use it for the ARCHITECTURAL AUDIT only — not for the live production
pipeline. The live pipeline is our own Defendable Swarm:
  · Brave  · canonical public-market retrieval
  · Kimi   · research foreman (via our gateway)
  · OpenAI · independent challenger (via our gateway)
  · Defendable Box · sovereign evidence capture
  · DefendableOS · tribunal · receipts · deeds · policy

Doctrine line for the audit:
  *Moonshot built the workforce. DefendableOS decides what is real.*

---

## Paste this into kimi.com/agent-swarm as the assignment

```
Assignment: DefendableOS MVP architectural audit · first Defendable Compute pilot

Repository: github.com/SudoSuOps/defendableos
Live demo: locally on port 3000 (Next.js) + 8000 (FastAPI)
Asset under audit: NVIDIA RTX PRO 6000 Blackwell Workstation GPU (DOV-COMPUTE-000001)

Project doctrine (non-negotiable):
  1. No evidence, no claim.
  2. No validator pass, no deed.
  3. No private evidence on ENS.
  4. No provider output becomes truth without a receipt and a challenge.

You may NOT implement code changes. Audit only.

Spawn parallel specialist teams covering:

  Team 1 · Backend architecture & data-model integrity
    · 16 SQLAlchemy models · cascade rules · indexes
    · FK ordering · transaction boundaries · UUID PK strategy
    · Alembic single-migration approach · future versioning path

  Team 2 · Security, secrets and privacy leakage risk
    · .env contract (BRAVE / MOONSHOT / OPENAI / EBAY / ENS_SIGNER)
    · Server-side-only secrets · browser visibility audit
    · filter_public_payload() · the canary test
    · tenant isolation in every private query
    · edge-token + enrollment-token lifecycle

  Team 3 · Provider gateway (Brave / Kimi / OpenAI / eBay)
    · ModelProvider interface · ToolDefinition + VisionImage support
    · Kimi K2.6 quirks (temperature=1 only · 4xx-not-swallowed)
    · OpenAI multimodal · gpt-4o-class vs o1/o3 reasoning_effort
    · Brave parser using grounding.generic[]
    · eBay Browse + Marketplace Insights tier separation
    · Provider switching via MODEL_PROVIDER

  Team 4 · Tribunal / Validate the Validator doctrine
    · 12 deterministic checks · check ID stability
    · Tool-use VALIDATOR_FLAG_TOOL · severity enum enforcement
    · Server-side downgrade guard (listing → confirmed-sale)
    · Disclaimer false-positive trap (denial vs affirmative)
    · Receipt SHA-256 determinism on identical evidence

  Team 5 · ENS / defendable.eth public-safe identity model
    · Mock / Offchain CCIP / Onchain wrapped adapters
    · Live-write triple-gate (ENS_LIVE_WRITES_ENABLED + signer + opt-in)
    · Naming hierarchy · blocked labels · public-record payload
    · Where ENS belongs (proof rail) vs. private DB (evidence)

  Team 6 · Defendable Box edge protocol
    · Enrollment-token lifecycle · one-time · hashed in DB
    · Edge-token JWT (separate secret from portal JWT)
    · Local SHA-256 + server re-hash · mismatch rejection
    · Revocation path · provenance=EDGE_CAPTURED tagging

  Team 7 · Portal UX (Next.js 14 + App Router)
    · 16 routes · asset workspace tabs · /verify/[slug]
    · No hydration errors · no client-side secrets
    · Privacy filter rendered correctly · ENS chip in header
    · Brave/Kimi NOT_CONFIGURED honest states

  Team 8 · Test coverage and CI readiness
    · 13 pytest cases · 1 canary on public deed privacy
    · GitHub Actions workflow (backend + frontend + edge-agent)
    · pgvector path · worker / Dramatiq scaffold
    · What's missing before first paying customer

  Team 9 · Missing features before first controlled live canary
    · Image evidence path · vision extraction
    · eBay sold-comp Marketplace Insights approval status
    · Operator review queue · dual-approval before publication
    · Customer notification on validator status changes

  Team 10 · Commercial presentation quality
    · Brand alignment with defendableos.com landing
    · Founder-demo click-through smoothness
    · ENS reservation language ("RESERVED_NOT_ISSUED" badge usage)
    · Deed-page final polish · public verification page

Deliverables:

  A. Executive verdict in 5 sentences or less
  B. Critical blockers ranked by severity (BLOCKING → HIGH → MEDIUM → LOW)
  C. Architecture strengths · what to preserve and protect
  D. Required repairs before live API calls on a real client asset
  E. Recommended first compute pilot workflow (10-step click-through)
  F. File-by-file implementation backlog · grouped by team
  G. Final verdict: PASS · PASS WITH REPAIRS · FAIL
     for running the first live Tribunal canary
     against an actual NVIDIA RTX PRO 6000 Blackwell Workstation GPU asset
```

---

## How to give the Swarm access to the code

Option A · Direct repo browse:
  Paste the GitHub URL · `github.com/SudoSuOps/defendableos`
  Most Swarm runs can clone and browse a public repo.

Option B · Upload the docs only:
  Drop `docs/ARCHITECTURE.md`, `docs/SECURITY_MODEL.md`,
  `docs/ENS_IDENTITY_MODEL.md`, `docs/EDGE_BOX_PROTOCOL.md`,
  `docs/API.md`, `docs/MVP_DEMO.md`, `README.md` into the
  Swarm's working space. They contain the doctrine and the
  service boundaries.

Option C · Cherry-pick the doctrine files:
  Just upload `services/api/app/services/deed.py`,
  `services/api/app/services/validator_checks.py`,
  `services/api/app/services/ens.py`,
  `services/api/app/services/tool_contracts.py`,
  and `services/api/alembic/versions/0001_initial.py`.

---

## After the audit

Bring the report back · I'll grade it against our doctrine and triage:
  · Findings the audit caught that we already knew → no action
  · Findings that are real surprises → grouped into a new task list
  · Findings that contradict our doctrine → respond and explain why
  · Specific code changes the Swarm suggests → reviewed before any merge
