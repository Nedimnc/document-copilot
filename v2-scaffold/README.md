# Fundamentals Lab — repo seed

This folder is a **starter checklist** for the second repository. It is not a runnable app. Follow [docs/v2/scaffold-from-copilot.md](../docs/v2/scaffold-from-copilot.md) and copy files from Document Copilot into a new git repo named e.g. `fundamentals-lab`.

## Initialize new repo

```bash
# From a parent directory (not inside document-copilot)
git clone <your-document-copilot-url> fundamentals-lab
cd fundamentals-lab
# Remove copilot-specific history — prefer fresh repo:
rm -rf .git
git init
git remote add origin <new-fundamentals-lab-url>
```

Or use GitHub “Use this template” after you push a trimmed branch.

## Strip from clone before first commit

- `backend/ingest/`
- `backend/app/retrieval/`, `grounding/`, `chat/orchestrator.py`
- `data/downloads`, `data/markdown` payloads
- `docs/client-brief.md` (replace with fundamentals-lab-brief)
- Copy in `docs/v2/fundamentals-lab-brief.md` as `docs/client-brief.md`

## Keep and rename

- Stack: FastAPI + Supabase + Vite + Railway toml files
- Auth flow and `lib/api.ts` pattern
- Alembic workflow (new initial migration for Lab tables)

## Suggested first commit message

```text
Initial Fundamentals Lab scaffold from Document Copilot template.

Screening/ratings product; no filing RAG. See docs/client-brief.md.
```

## Product docs to copy into new repo

- `docs/v2/fundamentals-lab-brief.md` → `docs/client-brief.md`
- `docs/v2/README.md` → `docs/product-context.md` (optional)

Document Copilot remains in its own repository for filing Q&A and pilot delivery.
