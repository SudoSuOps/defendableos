# DefendableOS

**Proof of Value · the operating system for evidence-backed valuation.**

DefendableOS turns real-world and digital assets into evidence-backed, market-ready records — with verified inputs, comparable analysis, provenance, valuation receipts, and transferable **Defendable Deeds**.

- **Platform:** DefendableOS
- **Customer promise:** Proof of Value
- **Doctrine:** Validate the Validator
- **Intelligence engine:** AIOV (AI Opinion of Value)
- **Artifact:** Defendable Deed
- **Public identity rail:** `defendable.eth` ENS subnames
- **Edge appliance:** Defendable Box

> Public landing site lives at [defendableos.com](https://defendableos.com) (separate repo at [SudoSuOps/defendable](https://github.com/SudoSuOps/defendable)).
> This repository is the **platform** — portal, API, and edge appliance.

---

## Architecture

```
defendableos/
├── apps/web/                Next.js 14 portal (App Router · TypeScript · Tailwind)
├── services/
│   ├── api/                 FastAPI · Python 3.12 · SQLAlchemy 2 · Alembic
│   ├── worker/              Background tasks (extraction, manifests, AI calls)
│   └── edge-agent/          Defendable Box CLI (Python)
├── packages/
│   ├── prompts/             Versioned AIOV / validator prompts
│   ├── schemas/             Shared schemas
│   └── ui/                  Shared branded UI tokens
├── infrastructure/
│   ├── docker-compose.yml   Postgres + Redis + MinIO + API + worker
│   └── env/.env.example     Environment variable contract
├── data/                    Sample evidence, example deeds, receipts
└── docs/                    ARCHITECTURE · SECURITY · ENS · EDGE · API · DEMO
```

## The product thesis

A client submits a compute asset (e.g., NVIDIA RTX PRO 6000 Blackwell GPU). The platform:

1. Records the asset with a public reference ID
2. Receives evidence uploads → SHA-256 hashed → evidence manifest generated
3. Searches **private evidence** (organization-scoped) + **public market** (Brave LLM Context)
4. Uses **Kimi K2.6** (via internal model gateway) for evidence-aware AIOV draft
5. Runs **Validate the Validator** deterministic + model-assisted review
6. Generates a versioned **Defendable Deed** JSON record
7. Reserves an **ENS subname** under `defendable.eth` (mock issuance in MVP)
8. Publishes a privacy-safe **public verification page** at `/verify/{slug}`
9. Accepts **Defendable Box** edge uploads with locally-precomputed hashes

**Evidence is the permanent record. AI is not the source of truth.**

---

## Local development setup

### Prerequisites

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+
- `pnpm` or `npm`

### 1. Boot the stack

```bash
cp infrastructure/env/.env.example .env
docker compose -f infrastructure/docker-compose.yml up -d postgres redis minio
```

This brings up:
- **Postgres** on `localhost:5432`
- **Redis** on `localhost:6379`
- **MinIO** on `localhost:9000` (console at `localhost:9001`)

### 2. Install API dependencies + run migrations

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.services.seed   # seeds Swarm & Bee Demo org + RTX 6000 asset
```

### 3. Start the API

```bash
uvicorn app.main:app --reload --port 8000
# OpenAPI docs · http://localhost:8000/docs
```

### 4. Install + run the portal

```bash
cd apps/web
npm install
cp .env.local.example .env.local   # if not auto-created
npm run dev
# Portal · http://localhost:3000
```

### 5. (Optional) Edge agent

```bash
cd services/edge-agent
python -m venv .venv && source .venv/bin/activate
pip install -e .
defendable-box --help
```

---

## Environment variables

See `infrastructure/env/.env.example` for the full contract.

Critical secrets (never committed, never exposed to browser):
- `BRAVE_API_KEY` — Brave LLM Context API for public market research
- `MOONSHOT_API_KEY` — Kimi K2.6 model gateway
- `JWT_SECRET`, `SESSION_SECRET`, `EDGE_ENROLLMENT_SECRET`
- `ENS_SIGNER_PRIVATE_KEY` — **never required in mock mode** (default)

When external API keys are absent:
- App runs cleanly with seed data
- Integration panels show "not configured" state
- Mock responses are clearly labeled — no fake live results

---

## Demo walkthrough

See [`docs/MVP_DEMO.md`](docs/MVP_DEMO.md) for the founder demo click-through.

Quick path:
1. Open `http://localhost:3000` → portal
2. Sign in as the demo user (seeded)
3. Open the seeded asset: **RTX PRO 6000 Blackwell Workstation GPU** (`DOV-COMPUTE-000001`)
4. Walk through tabs: Evidence → Research → AIOV → Validator → Deed
5. View public verification preview
6. Open Edge Devices → see `box-01.swarmbee.defendable.eth`

---

## Documentation

| Doc | Topic |
|-----|-------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Service boundaries · data flow · storage strategy |
| [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md) | Tenant isolation · secrets · privacy rules · threat model |
| [`docs/ENS_IDENTITY_MODEL.md`](docs/ENS_IDENTITY_MODEL.md) | `defendable.eth` naming · mock/CCIP/wrapped adapters · live-write safety |
| [`docs/EDGE_BOX_PROTOCOL.md`](docs/EDGE_BOX_PROTOCOL.md) | Enrollment · heartbeat · evidence hashing · revocation |
| [`docs/API.md`](docs/API.md) | Endpoint reference |
| [`docs/MVP_DEMO.md`](docs/MVP_DEMO.md) | Founder demo flow · keyed vs. unkeyed states |

---

## Disclosure language

DefendableOS records are evidence and analysis packages. Asset-specific professional, legal, regulatory, licensing, authentication, insurance, or appraisal requirements may still apply. AIOV is AI-assisted and reviewable — **not** a licensed appraisal, legal certification, authentication guarantee, warranty, insurance determination, or regulated professional conclusion.

Public verification pages contain only approved non-sensitive proof data. Private evidence, serial numbers, purchase costs, and confidential documents stay server-side.

---

## License

Proprietary. © 2026 Swarm and Bee LLC. All rights reserved.

DefendableOS™, Proof of Value™, Validate the Validator™, AIOV™, and Defendable Deed™ are unregistered trademarks of Swarm and Bee LLC (Florida LLC · doing business as Swarm & Bee AI).
