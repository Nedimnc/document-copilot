# Backend

FastAPI service for Document Copilot. Python 3.12+, managed with `uv`.

## Setup

Copy `.env.example` to `.env` and fill in real values. `DATABASE_URL` must be the Supabase **direct** connection (`db.<project-ref>.supabase.co`), not the pooler. Set `OPENAI_CHAT_MODEL` (default in example: `gpt-4o-mini`) and ensure `document_chunks` is loaded (`uv run python -m ingest.chunk_and_embed`) before expecting corpus-backed answers.

```bash
cd backend
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

- Health: http://127.0.0.1:8000/health
- Current user: http://127.0.0.1:8000/auth/me (`Authorization: Bearer <supabase_access_token>`)
- Chat: `GET/POST /chat/threads`, `GET /chat/threads/{id}/messages`, `POST /chat/stream` (grounded SSE via PydanticAI)
- Docs: http://127.0.0.1:8000/docs

## Migrations

Alembic owns the schema. Use the direct Supabase URL in `.env`, then:

```bash
uv run alembic upgrade head
```

After changing SQLAlchemy models:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

Review the generated file before applying. Vector indexes, generated `tsvector` columns, and RLS policies are maintained by hand in migrations.

Manual grounded-chat smoke (edit `query_key` in `main()`):

```bash
uv run python smoke_assistant.py
```

## Test / lint

```bash
uv run pytest
uv run ruff check app tests
```

## Dependencies

```bash
uv add package-name
uv add --dev package-name
```
