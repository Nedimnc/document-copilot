# Document Copilot

An internal AI chatbot that lets analysts query a corpus of documents in plain English and get sourced, citable answers.

## The client

**Driftwood Capital** — fictional independent investment research firm. Their analysts spend half their week reading 10-Ks and 10-Qs before they can produce any original analysis. Document Copilot eats that intake work so they can skip straight to insight.

Full brief: [docs/client-brief.md](docs/client-brief.md)

## Stack

| Layer              | Choice                                               |
| ------------------ | ---------------------------------------------------- |
| Backend            | Python + FastAPI                                     |
| Frontend           | Vite + React SPA + TypeScript                        |
| Database           | Supabase Postgres (users, chats, documents, chunks)  |
| Migrations         | SQLAlchemy models + Alembic                          |
| Retrieval          | Supabase `pgvector` + Postgres full-text search      |
| Auth               | Supabase Auth (email only)                           |
| Hosting            | Railway                                              |
| LLM + embeddings   | OpenAI                                               |

## Architecture

High-level map of how the analyst UI, API, corpus, and external services connect. Deeper design notes (chat turn sequence, modules, data model): [docs/architecture.md](docs/architecture.md).

<p align="center">
  <img src="docs/assets/architecture.svg" alt="Document Copilot architecture: React SPA and Railway frontend/API, Supabase Auth and Postgres with hybrid retrieval, OpenAI for chat and embeddings, and offline SEC ingestion into document_chunks" width="920" />
</p>

## Repo layout

```text
document-copilot/
├── AGENTS.md           # agent instructions (read first)
├── README.md           # this file
├── data/               # local corpus + download script (payloads gitignored)
├── docs/
│   ├── architecture.md # system design (as built)
│   ├── client-brief.md # the client one-pager
│   └── todo.md         # implementation checklist
├── backend/            # FastAPI service
└── frontend/           # React SPA (Vite)
```

## Prerequisites

Install these before setting up `backend/` or `frontend/`:

| Tool | Version | Used for | Install |
| ---- | ------- | -------- | ------- |
| [Python](https://www.python.org/downloads/) | 3.12+ | Backend runtime | OS package manager or python.org |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | latest | Backend deps + `data/download.py` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Node.js](https://nodejs.org/) | 20+ (LTS) | Frontend toolchain | nodejs.org or `nvm install --lts` |
| [pnpm](https://pnpm.io/installation) | latest | Frontend package manager | `corepack enable && corepack prepare pnpm@latest --activate` |

You also need accounts/keys for external services once the app is wired up. Start with [docs/guides/supabase-setup.md](docs/guides/supabase-setup.md) (account + project), then create an [OpenAI API key](https://platform.openai.com/api-keys) when the LLM layer is wired up.

## Running locally

You run **two processes**: FastAPI on port **8000** and the Vite dev server on port **5173**. Both talk to the same **Supabase** project (Auth + Postgres). Chat also needs an **OpenAI** key and a **loaded corpus** (`document_chunks` with embeddings). If you are joining an existing team project, ask for env values and skip ingestion; otherwise follow [Supabase setup](docs/guides/supabase-setup.md) and [Sample SEC data](#sample-sec-data) below.

### 1. One-time setup

**Supabase project** — create a project, run migrations, enable email auth, and set Auth redirect URLs to include `http://localhost:5173`. Step-by-step: [docs/guides/supabase-setup.md](docs/guides/supabase-setup.md).

**Backend environment** — from the repo root:

```bash
cd backend
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `backend/.env` with:

- Supabase URL and keys (`SUPABASE_*`)
- `DATABASE_URL` — **direct** Postgres host (`db.<ref>.supabase.co`), not the pooler URL
- `OPENAI_API_KEY` and model settings (see `.env.example`)
- `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

Install Python deps and apply schema:

```bash
cd backend
uv sync
uv run alembic upgrade head
```

**Frontend environment**:

```bash
cd frontend
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `frontend/.env`:

- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` — same Supabase project as the backend (anon key only)

Install frontend deps:

```bash
cd frontend
pnpm install
```

**Corpus** — the app will sign in and load threads, but answers need ingested filings in Supabase. Either use a shared dev database that already has chunks, or run the [Sample SEC data](#sample-sec-data) pipeline once (`download` → `to_markdown` → `load_documents` → `chunk_and_embed`).

### 2. Start the app (every day)

Use **two terminals**.

**Terminal 1 — API:**

```bash
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — UI:**

```bash
cd frontend
pnpm dev
```

Then open **http://localhost:5173**, sign in with email (Supabase), and start a chat.

### 3. Quick checks

| Check | URL / command | Expected |
| ----- | ------------- | -------- |
| API health | http://127.0.0.1:8000/health | `{"status":"ok"}` |
| API docs | http://127.0.0.1:8000/docs | OpenAPI UI |
| Backend tests | `cd backend && uv run pytest -m "not integration" -q` | All pass |
| Frontend types | `cd frontend && pnpm exec tsc -b --noEmit` | No errors |

**Optional — backend smoke script** (retrieval + LLM stream in the terminal, no browser):

```bash
cd backend
uv run python smoke_assistant.py
```

### 4. Common issues

- **CORS errors in the browser** — add your frontend origin to `ALLOWED_ORIGINS` in `backend/.env` and restart Uvicorn.
- **Auth redirect / magic link fails** — in Supabase Dashboard → Authentication → URL configuration, set Site URL and redirect URLs to include `http://localhost:5173`.
- **Empty or “no evidence” answers** — corpus not loaded; run ingestion or point `DATABASE_URL` at a project that already has `document_chunks`.
- **Migration errors** — confirm `DATABASE_URL` uses the direct connection string; see [backend setup](docs/guides/backend-setup.md).

More detail: [backend setup](docs/guides/backend-setup.md), [frontend setup](docs/guides/frontend-setup.md), [architecture](docs/architecture.md).

## Deploying to Railway

Two services (backend + frontend), Supabase unchanged. Step-by-step: [docs/guides/railway-deployment.md](docs/guides/railway-deployment.md). Config files: `backend/railway.toml`, `frontend/railway.toml`.

Pilot checklist (Phase 8): [docs/guides/pilot-validation.md](docs/guides/pilot-validation.md).

## Second product (Fundamentals Lab)

Separate from Document Copilot—screening, charts, criteria-based ratings. Planning docs: [docs/v2/README.md](docs/v2/README.md). Repo seed checklist: [v2-scaffold/README.md](v2-scaffold/README.md).

## Sample SEC data

Use the standalone downloader to fetch a small local 10-K sample from SEC EDGAR.
Edit the params at the top of `data/download.py`, especially `USER_AGENT`, then run:

```bash
uv run data/download.py
```

By default this downloads the latest 5 10-K filings for AAPL, MSFT, NVDA, AMZN, and GOOGL into year folders under `data/downloads/` and writes a `manifest.json`.
Convert those HTML files to Markdown (same year layout) with:

```bash
cd backend
uv run python -m ingest.to_markdown
```

Load the Markdown filings into `source_documents`:

```bash
cd backend
uv run python -m ingest.load_documents
```

Chunk the original HTML (not the Markdown export) and write `document_chunks`:

```bash
cd backend
uv run python -m ingest.chunk_and_embed
```

Ingestion uses Docling with Markdown-style table serialization in chunks so citation excerpts stay readable. Re-chunking an existing corpus replaces all `document_chunks` rows (new UUIDs and embeddings). **`message_citations.chunk_id` uses `ON DELETE RESTRICT`**, so you cannot delete chunks that pilot chat history still references. Safe refresh options:

1. **Empty / dev database:** run `uv run python -m ingest.chunk_and_embed --force` for the full manifest after `load_documents`.
2. **Database with chat history:** archive or truncate dependent citation/message rows first, or refresh only on a new Supabase project and point staging at it.

After a full re-chunk, re-run `uv run python -m ingest._validate_phase3` and update any hard-coded chunk count expectations in that script.

Downloaded and converted files are gitignored; the `data/` folder itself stays in git for the scripts and notes.
