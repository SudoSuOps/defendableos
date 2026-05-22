# MVP Demo · Founder Walkthrough

The complete demo runs locally with **no external keys**. Adding Brave + Kimi keys upgrades the same flow with live integrations · the UI tells the truth either way.

## Boot

```bash
cp infrastructure/env/.env.example .env
docker compose -f infrastructure/docker-compose.yml up -d postgres redis minio

cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.services.seed
uvicorn app.main:app --reload --port 8000

# In a second shell:
cd apps/web
npm install
cp .env.local.example .env.local
npm run dev   # http://localhost:3000
```

Default seed user: `demo@swarmandbee.ai` / `defendable-demo`

## Click-through

| Step | Where | What you see |
|---|---|---|
| 1 | `http://localhost:3000` | Landing page · "Evidence first. Opinion second. Proof after review." |
| 2 | `/login` | Pre-filled demo creds · sign in |
| 3 | `/portal` | Dashboard · 6 stat cards · Swarm & Bee Demo org · ENS reserved chip in header |
| 4 | `/portal/assets` | Inventory includes the seeded `DOV-COMPUTE-000001` RTX PRO 6000 Blackwell |
| 5 | `/portal/assets/<id>` | Asset workspace overview · compute identity · workflow stage |
| 6 | `Evidence` tab | Upload a PDF / JSON / TXT · SHA-256 appears · manifest v1 generated |
| 7 | `AI Search` tab → Private | Lexical match across uploaded chunks |
| 8 | `AI Search` tab → Public | If `BRAVE_API_KEY` set: live sources. If not: session created, sources empty, status `FAILED` with provider tag |
| 9 | `AIOV` tab | Generate draft · structured analysis · narrative · missing-evidence chips |
| 10 | `Validator` tab | Run validator · 12 checks · `PASSED_FOR_PACKAGING` or repair list |
| 11 | `Deed` tab | Generate deed version · institutional card + `deed.record.json` · ENS reserved name shown |
| 12 | `Deed` tab → Publish | (Admin only) Publish public verification page → `/verify/<slug>` |
| 13 | `/verify/<slug>` | Privacy-filtered public record · serial / purchase cost / narrative all absent |
| 14 | `/portal/edge` | `Defendable Box 01` · `ENROLLED_DEMO` · `box-01.swarmbee.defendable.eth` |
| 15 | `/portal/edge/enroll` | Generate token + copy-paste install snippet for the agent |

## Demo · external key states (honest)

| Key | Absent | Present |
|---|---|---|
| `BRAVE_API_KEY` | Sessions created · status `FAILED` · provider says `BRAVE_LLM_CONTEXT` · sources empty | Live Brave results · `retrieved_at` set · classification defaults to `UNKNOWN` |
| `MOONSHOT_API_KEY` | AIOV uses local scaffold · `AIOutput.status=NOT_CONFIGURED` · still structured · still passes the validator's AI-assisted-limitation rule | Live Kimi K2.6 narrative + optional structured JSON |
| `ENS_LIVE_WRITES_ENABLED` | All ENS identities `RESERVED_NOT_ISSUED` · mock-mode | Admin must opt-in per action · onchain adapter still raises NotImplementedError until wired |

## Operator runbook

- **Reset the demo**: `docker compose -f infrastructure/docker-compose.yml down -v` + `alembic upgrade head` + reseed
- **Inspect a manifest**: open MinIO console at `localhost:9001` (minioadmin / minioadmin) → `defendable-private` → `organizations/.../assets/.../manifests/`
- **See a published deed JSON**: `defendable-public/verification/<slug>/deed-public.json`
- **Audit trail for an asset**: portal Audit tab or `GET /api/v1/assets/<id>/audit`
- **Tests**: from `services/api/`: `pytest app/tests -v`
