# Supabase setup

We use Supabase for **Postgres** (users, chats, source documents, chunks, embeddings, and citations) and **Auth** (email sign-in only). You need one hosted Supabase project before wiring up `backend/` and `frontend/`.

## 1. Create an account

1. Go to [supabase.com](https://supabase.com) and sign up (GitHub or email).
2. Confirm your email if prompted.
3. You land in the [dashboard](https://supabase.com/dashboard). The free tier is enough for local development.

## 2. Create a project

1. Open [New project](https://supabase.com/dashboard/new).
2. Pick your organization (a personal org is created automatically on first signup).
3. Set a **project name** (e.g. `Document Copilot`).
4. Choose a **database password** — save it somewhere safe; you need it for direct DB access and `supabase link`.
5. Pick a **region** close to you.
6. Click **Create new project** and wait until status is healthy (~1–2 minutes).

## 3. Collect credentials

You need these values in backend and frontend env config (exact variable names will live in each service's settings module once the app is built).

| Value | Where to find it | Used by |
| ----- | ---------------- | ------- |
| **Project URL** | Dashboard → **Project Settings** → **API** → Project URL | Frontend + backend |
| **anon (public) key** | Same page → `anon` `public` key | Frontend (browser-safe) |
| **service_role (secret) key** | Same page → `service_role` `secret` key | Backend only — never expose to the browser |
| **Project ref** | Dashboard URL `supabase.com/dashboard/project/<ref>` or `supabase projects list` | CLI commands |
| **Direct database connection string** | Dashboard → **Project Settings** → **Database** → Connection string | Alembic migrations and backend DB access |
| **Database password** | What you set at project creation | Direct Postgres connection |

From the CLI you can also print API keys:

```bash
supabase projects api-keys --project-ref <your-project-ref>
```

Keep `service_role` out of git, client bundles, and frontend env files.

## 4. Auth settings (email only)

This app uses email/password auth only — no Google/SSO. Signup happens in the React app against Supabase Auth. FastAPI never stores passwords; it only verifies the JWT.

Open your project: `https://supabase.com/dashboard/project/<your-ref>`

### Providers

1. Go to **Authentication → Sign In / Providers**.
2. Leave **Email** enabled.
3. Disable every other provider (Google, GitHub, SSO, etc.).
4. Open the Email provider settings.
5. For local development, turn **Confirm email** **off**. Otherwise signup creates a user but no session until the inbox link is clicked.
6. Re-enable confirm-email before any real rollout.

### URL configuration

1. Go to **Authentication → URL Configuration**.
2. Set **Site URL** to `http://localhost:5173`.
3. Add these **Redirect URLs**:
   - `http://localhost:5173`
   - `http://localhost:5173/**`
   - `http://localhost:5173/login`

### Create a user

Either:

- Use the app: `http://localhost:5173/login` → **Need an account? Sign up**
- Or dashboard: **Authentication → Users → Add user** (email + password, auto-confirm)

After signup, `auth.users` gets a row and the `handle_new_user` trigger inserts a matching `public.profiles` row. Check **Table Editor → profiles**.

### Frontend env

`frontend/.env` needs the same **public** values as the backend (never the service-role key):

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<your-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon or sb_publishable_ key>
```

### Quick check

1. Start the backend (`uv run uvicorn app.main:app --reload` from `backend/`).
2. Start the frontend (`pnpm dev` from `frontend/`).
3. Sign up, then you should land on `/` and see `Backend verified <email>`.
4. `GET http://127.0.0.1:8000/auth/me` with `Authorization: Bearer <access_token>` should return `{ "id", "email" }`.

## 5. Database schema management

Document Copilot uses Alembic from the Python backend to manage database schema. Do not create production tables manually in the Supabase dashboard.

Alembic migrations create and update:

- the `vector` extension for `pgvector`
- source document and chunk tables
- embedding columns
- generated full-text search columns
- HNSW and GIN indexes
- chat and citation tables
- row-level security policies

Use the direct/session database connection string for Alembic. Do not use the transaction pooler connection string for migrations.

From `backend/`:

```bash
uv run alembic upgrade head
```

See [Backend setup](backend-setup.md) for the Alembic workflow.

## Next steps

- [Backend setup](backend-setup.md) — Python service + Supabase client
- [Frontend setup](frontend-setup.md) — React app + `@supabase/supabase-js`
