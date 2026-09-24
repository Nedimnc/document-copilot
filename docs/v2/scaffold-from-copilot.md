# Scaffold Fundamentals Lab from Document Copilot

Create a **new Git repository** (do not extend Document Copilot’s scope). Copy patterns, not the RAG pipeline.

## 1. Create repo

```bash
mkdir fundamentals-lab && cd fundamentals-lab
git init
```

Copy from Document Copilot:

| Copy | To | Notes |
| ---- | --- | ----- |
| Root `AGENTS.md` | `./AGENTS.md` | Trim ingestion/RAG sections |
| `backend/app/config.py` | same | Add `MARKET_DATA_API_KEY`, remove embedding-only if unused |
| `backend/app/main.py` | same | Drop chat router until ready |
| `backend/app/auth/` | same | JWT verification unchanged |
| `backend/app/database/session.py`, `supabase.py` | same | New models for watchlists, screens |
| `backend/pyproject.toml` | same | Remove pydantic-ai/pgvector until needed |
| `frontend/src/lib/env.ts`, `http.ts`, `api.ts`, `supabase.ts`, `auth.ts` | same | Rename `VITE_*` only if needed |
| `frontend/package.json` scripts | same | Add chart lib when building UI |
| `docs/guides/supabase-setup.md` | same | New Supabase project recommended |
| `backend/railway.toml`, `frontend/railway.toml` | same | Update service names |

Do **not** copy: `backend/ingest/`, `backend/app/retrieval/`, `backend/app/grounding/`, `backend/app/chat/orchestrator.py`, corpus data.

## 2. Minimal backend modules (v1)

```text
backend/app/
├── api/
│   ├── health.py          # /health, /health/ready
│   ├── screen.py          # POST /screen/run
│   └── watchlist.py       # CRUD watchlists
├── market/
│   ├── client.py          # HTTP to fundamentals API
│   └── normalize.py       # Ticker → metrics DTO
├── scoring/
│   ├── criteria.py        # User criteria schema
│   └── rate.py            # Buy/Hold/Sell + trace
└── database/
    └── models.py          # profiles, watchlists, screen_runs
```

## 3. Minimal frontend routes (v1)

```text
frontend/src/pages/
├── LoginPage.tsx          # reuse pattern
├── WatchlistPage.tsx      # tickers + run screen
├── ScreenResultsPage.tsx  # grid + ratings
└── CompanyPage.tsx        # charts + criteria trace
```

## 4. Environment

**Backend:** Supabase + `DATABASE_URL` + `MARKET_DATA_API_KEY` + `ALLOWED_ORIGINS`

**Frontend:** `VITE_API_BASE_URL`, `VITE_SUPABASE_*`

## 5. Starter tree in this repo

See [v2-scaffold/](../../v2-scaffold/README.md) for a copy-paste checklist and placeholder README to seed the new repo.

## 6. First milestone

1. Auth + health + one API route returning mock metrics for `AAPL`
2. Single criteria rule (e.g. gross margin > 40%) → Pass/Fail
3. One chart on company page

Then replace mock with real API client behind an interface for tests.
