# NexusDB: Governed Natural Language Database Navigation

NexusDB is a self-correcting multi-agent query engine and governed write-back platform. It turns natural-language questions into read-only SQL through semantic schema memory (ChromaDB), an AST-level SQL safety guard (`sqlglot`), a bounded reflection loop, sequential agents, and a SHA-256 audit ledger. The React frontend uses a warm paper visual style and streams an **11-stage pipeline** over SSE (`POST /query/stream`).

PostgreSQL 16 is the production target. Local development falls back to SQLite when Postgres is not running.

---

## Architecture

```
Frontend (React 19 + Vite)  --SSE /query/stream-->  Stage orchestrator (11 stages)
                                                       |
                                                       v
Query Agent (text-to-SQL + reflection) -> Analysis Agent -> Visualization Agent
                                                       |
Semantic memory (ChromaDB + glossary.yaml)    SQL Guard (sqlglot)
                                                       |
PostgreSQL 16 / SQLite   |   Governed actions (nexus_writer)   |   Audit chain
```

Key backend modules live under `backend/app/`: `core/pipeline.py` (stages), `core/sql_guard.py`, `llm/` (Gemini or FakeLLM in `DEMO_MODE`), `governance/` (RBAC, actions, audit), `memory/` (schema index).

The older root helpers (`main.py`, `llm.py`, `models.py`, `database.py`, `run_backend.bat`) still exist for Windows convenience scripts. The supported API used by the current UI is the FastAPI app in `backend/app/main.py`.

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Optional: Docker Desktop (PostgreSQL 16 via Compose)

### Windows (batch files)

From the repository root:

```bat
run_backend.bat
run_frontend.bat
```

Or both:

```bat
start_all.bat
```

`run_backend.bat` starts root `main.py`. For the full 11-stage API used by the UI, prefer:

```bat
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend: http://localhost:5173 — Backend: http://localhost:8000 — Docs: http://localhost:8000/docs

### Local Python + Node (SQLite fallback)

1. Copy `.env.example` to `.env` (do not commit `.env`). Set `GEMINI_API_KEY` only if you want live Gemini; otherwise leave `DEMO_MODE=true`.
2. Backend:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python db/seed/generate.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

3. Frontend:

```bash
cd frontend
npm install
npm run dev
```

Copy `VITE_API_URL=http://localhost:8000` into `frontend/.env` if you need a non-default API host.

### Makefile

| Target | What it does |
| :--- | :--- |
| `make up` | `docker compose up -d` |
| `make down` | Stop Compose |
| `make seed` | Generate local seed data |
| `make index` | Rebuild semantic schema index |
| `make test` | Unit tests |
| `make eval` | 40-question evaluation harness |
| `make lint` | Ruff (if installed) |
| `make demo` | Seed, index, then run uvicorn |

### Docker Compose

```bash
docker compose up --build
```

API on port 8000; production frontend (nginx) on port 3000.

---

## Environment variables

Copy `.env.example`. Placeholder values only — never commit a real `.env`.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL_OWNER` | local `nexus_owner` URL | Owner role (schema init) |
| `DATABASE_URL_READER` | local `nexus_reader` URL | Read-only query execution |
| `DATABASE_URL_WRITER` | local `nexus_writer` URL | Governed write-back actions |
| `DATABASE_URL` | local `enterprise_finance` URL | Legacy scripts / root helpers |
| `JWT_SECRET` | `change-me` | Demo JWT signing secret |
| `JWT_EXPIRE_MINUTES` | `60` | Token lifetime |
| `GEMINI_API_KEY` | empty | Live LLM; unused when FakeLLM is on |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model id |
| `EMBEDDING_BACKEND` | `local` | `local` or `gemini` |
| `CHROMA_PATH` | `./.chroma` | Vector store path |
| `DEMO_MODE` | `true` | Deterministic FakeLLM, no API key |
| `MAX_RETRIES` | `3` | Reflection-loop repair budget |
| `STATEMENT_TIMEOUT_MS` | `5000` | Query timeout |
| `ROW_CAP` | `1000` | Hard row cap |
| `CORS_ORIGINS` | Vite + nginx origins | Comma-separated browser origins |
| `VITE_API_URL` | `http://localhost:8000` | Frontend API base (also `frontend/.env.example`) |
| `PORT` | `8000` | Backend listen port |

Demo logins (development only): `viewer@nexusdb.local` / `viewer123`, `officer@nexusdb.local` / `officer123`, `manager@nexusdb.local` / `manager123`, `admin@nexusdb.local` / `admin123`. The UI can also switch roles from the header.

---

## Tests and evaluation

```bash
# Unit tests (Makefile)
make test

# Unit + integration
python -m pytest backend/tests/unit backend/tests/integration -v

# 40-question benchmark (writes reports/eval-latest.json and .md)
python backend/tests/eval/run_eval.py
# or
make eval
```

Latest checked-in eval summary: 40/40 execution accuracy in `DEMO_MODE` (see `reports/eval-latest.md`).

---

## API used by the frontend

- `POST /query/stream` — SSE frames for the 11 pipeline stages
- `POST /auth/login` — demo JWT
- `GET /health`, `GET /metrics`, `GET /schema`, `GET /audit`, `GET /audit/verify`
- `POST /actions/confirm` — governed write-back

Do not point the current UI at the older `POST /api/query` helper surface.

---

## Known limitations

Writes are only the pre-authorized actions in `backend/app/governance/actions.py`. Results are capped at 1,000 rows. Execution is a single database (Postgres or SQLite). Statements time out after 5 seconds.
