# Railway deployment

Two Railway services from this monorepo: **backend** (`backend/`) and **frontend** (`frontend/`). Supabase stays hosted; corpus and chats live in Postgres.

## 1. Supabase (before deploy)

1. Run migrations: `cd backend && uv run alembic upgrade head`
2. Confirm corpus loaded (`document_chunks` populated) or run ingestion locally against prod DB (careful).
3. **Authentication → URL configuration:** set Site URL and redirect URLs to your Railway frontend URL (and localhost for dev).

## 2. Backend service

| Setting | Value |
| -------- | ----- |
| Root directory | `backend` |
| Config file | `backend/railway.toml` (auto-detected when root is `backend`) |

**Environment variables** (mirror [backend/.env.example](../../backend/.env.example)):

- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL` (direct Postgres host, not pooler)
- `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_EMBEDDING_DIMENSIONS`
- `ALLOWED_ORIGINS` — comma-separated; include `https://<your-frontend>.up.railway.app` (no trailing slash)
- Optional: `ENVIRONMENT=production`

**Health check:** `GET /health` → `{"status":"ok"}`. Optional readiness: `GET /health/ready` (DB ping).

**Public URL:** note the backend hostname for `VITE_API_BASE_URL`.

## 3. Frontend service

| Setting | Value |
| -------- | ----- |
| Root directory | `frontend` |
| Config file | `frontend/railway.toml` (auto-detected when root is `frontend`) |

**Build-time variables** (required for `pnpm build`):

- `VITE_API_BASE_URL=https://<your-backend>.up.railway.app`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

Railway exposes these during the build step. Redeploy frontend after changing them.

**Runtime:** `vite preview` serves `dist/` with SPA fallback for `/chats/:id` routes.

## 4. Smoke test (production)

1. Open frontend URL → sign in.
2. New chat → ask one [client brief](../client-brief.md) question → confirm citations and sources panel.
3. Ask question 10 (AI margins) → expect refusal or strictly filing-bound answer.
4. `curl https://<backend>/health`

## 5. Migrations on deploy

Railway does not run Alembic automatically. Options:

- Run `uv run alembic upgrade head` locally against prod `DATABASE_URL` before first deploy (recommended).
- Add a one-off Railway job or release command later if you want automation.

## 6. Known limitations

- Ingestion remains **CLI-only**; re-chunk in a maintenance window (see root README).
- OpenAPI at `/docs` is enabled in all environments today; restrict later via `ENVIRONMENT` if needed.
