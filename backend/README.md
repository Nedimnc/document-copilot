# Backend

FastAPI service for Document Copilot. Python 3.12+, managed with `uv`.

## Setup

Copy `.env.example` to `.env` and fill in real values. `DATABASE_URL` must be the Supabase **direct** connection (`db.<project-ref>.supabase.co`), not the pooler.

```bash
cd backend
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

- Health: http://127.0.0.1:8000/health
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
