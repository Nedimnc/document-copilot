# Document Copilot implementation checklist

## Recommended build order

The most logical path is to build the backend first, then the frontend. The reason is that this product is not just a chat app; it is a trust-sensitive research system. The backend owns auth, retrieval, grounding, citation validation, and durable storage. Without that foundation, the frontend is just a shell and we risk shipping an interface that looks polished but cannot reliably answer from the corpus.

## Phase 0: project foundation

- [ ] Confirm the project requirements and success criteria from the client brief
- [ ] Set up the repo structure and naming conventions for backend and frontend
- [ ] Define environment config for backend and frontend in the single-source settings modules
- [ ] Confirm toolchain and package manager expectations:
  - [ ] Backend: Python + uv + FastAPI + PydanticAI
  - [ ] Frontend: Vite + React + TypeScript + pnpm
- [ ] Set up local development workflow and run scripts for both services
- [ ] Create a shared working plan for API contracts, auth flow, and model configuration

## Phase 1: backend foundation and auth

- [x] Initialize the FastAPI app and health-check endpoints
- [x] Create the shared backend configuration module and fail-fast env validation
- [x] Set up Supabase Auth integration and bearer-token verification middleware/dependencies
- [x] Define the authenticated user context and rule that all chat actions are user-scoped
- [x] Create the project structure for:
  - [x] app/api
  - [x] app/auth
  - [x] app/chat
  - [x] app/assistant
  - [x] app/retrieval
  - [x] app/grounding
  - [x] app/database
- [x] Decide the DB schema for users, threads, messages, source documents, chunks, embeddings, and citations
- [x] Set up SQLAlchemy/Alembic structure and migration workflow

## Phase 2: data model and Supabase schema

- [x] Create the core tables for:
  - [x] users / auth linkage
  - [x] chat threads
  - [x] chat messages
  - [x] source documents
  - [x] filing chunks
  - [x] embeddings
  - [x] citation records
- [x] Add database indexes and searchable columns for hybrid retrieval
- [x] Configure Postgres full-text search and pgvector usage for chunks
- [x] Define the source-document metadata model (company, filing type, filing date, page, URL, etc.)
- [x] Create typed query helpers for reading/writing chat and corpus records

## Phase 3: ingestion pipeline

- [x] Build the SEC filing download flow for the curated corpus
- [x] Create parsing logic for the filing HTML/text extraction pipeline
- [x] Normalize document metadata and preserve page-level references
- [x] Chunk filings into retrieval-friendly segments with page provenance
- [x] Generate embeddings for each chunk using the configured model
- [x] Store documents, chunks, embeddings, and metadata in Supabase/Postgres
- [x] Validate retrieval inputs with a small sample corpus before going wider
- [x] Add ingestion tests for parsing, chunking, and metadata integrity
- [x] Use Markdown-style table serialization in chunks (not Docling triplet tables) for readable citation excerpts

Corpus verified in Supabase (2026-09-21): **25** `source_documents`, **11,892** `document_chunks` (all with 1536-dim embeddings). Hybrid retrieval smoke-tested against live DB. **Note:** existing rows may still show triplet table noise until a controlled `chunk_and_embed --force` refresh (see README).

## Phase 4: retrieval and grounding

- [x] Implement semantic retrieval over chunk embeddings
- [x] Implement lexical retrieval over search vectors
- [x] Fuse the ranked result sets with reciprocal rank fusion (RRF)
- [x] Create the retrieval service to fetch top chunks and nearby context for grounding
- [x] Define the grounding contract: answers must cite retrieved evidence and only state what the corpus supports
- [x] Build a citation validator that checks citation labels against retrieved passages (deterministic; not semantic claim↔passage matching)
- [x] Add tests for retrieval quality, citation extraction, and insufficient-evidence handling
- [x] Document refusal behavior when the corpus does not support the answer

Hybrid retrieval follows [ai-cookbook hybrid-retrieval](https://github.com/daveebbelaar/ai-cookbook/tree/main/knowledge/hybrid-retrieval): over-fetch 50 per channel, RRF with k=60, return top 10 citable passages. Neighbor context is off by default for chat; enable via `RetrievalOptions(include_neighbors=True)` for diagnostics. Code: `backend/app/retrieval/`, `backend/app/grounding/`. Refusal copy: `grounding/refusal.py`.

## Phase 5: LLM orchestration and assistant logic

- [x] Define the typed assistant output schema for grounded answers and citations
- [x] Create the PydanticAI agent boundary and dependency injection model
- [x] Write system instructions for:
  - [x] grounded-only answers
  - [x] explicit citations
  - [x] no invented facts
  - [x] concise but verifiable responses
  - [x] no stock recommendations or investment advice
- [x] Build the chat orchestrator for one turn of retrieval + answer generation + save-to-db
- [x] Implement message conversion between AI SDK format and internal types
- [x] Add backend streaming response handling for incremental chat output
- [x] Add structured logging and usage metadata capture
- [x] Validate and canonicalize citations before streaming assistant text to the client

## Phase 6: chat API and persistence

- [x] Build the thread creation and listing endpoints
- [x] Build the message history retrieval endpoints
- [x] Build the streaming chat endpoint with authenticated request validation
- [x] Persist user messages and assistant replies to the database
- [x] Persist citation records and referenced passages for later display
- [x] Confirm the answer contract is consistent with the frontend consumer expectations
- [x] Validate the API against sample analyst prompts from the client brief

`GET /chat/threads/{id}/messages` returns `citations[]` per assistant message (ticker, filing, page, excerpt, SEC URL). Stream emits `data-copilot-status` for pipeline phases. Use `backend/smoke_assistant.py` for manual analyst-style prompts.

## Phase 7: frontend app shell and chat UI

- [x] Set up the Vite React SPA and app routing
- [x] Add the Supabase browser client and environment validation module
- [x] Create shared API helpers for bearer-token-authenticated calls
- [x] Build the login / auth flow using Driftwood email addresses
- [x] Build the thread list and conversation history UI
- [x] Build the chat composer and streaming message interface
- [x] Display citations, source filings, page references, and underlying passages
- [x] Add empty states, loading states, and error handling for invalid or unsupported questions
- [x] Ensure the frontend does not contain any privileged credentials or server-side logic

## Phase 8: end-to-end validation against the client brief

- [ ] Test the core analyst questions from the brief with real corpus-backed answers
- [ ] Confirm each answer includes precise filing and page citations (page may be absent on HTML-derived chunks)
- [ ] Validate that the system refuses unsupported claims explicitly and clearly
- [ ] Spot-check citation excerpts for readable table text after corpus refresh
- [ ] Check the experience for the pilot analyst group: trust, speed, and usefulness
- [ ] Measure whether the workflow saves at least 3 hours per analyst per week
- [ ] Review any gaps in retrieval quality or citation clarity before scaling out

## Phase 9: Railway deployment

- [ ] Define Railway services: backend (Uvicorn on `$PORT`) and frontend (static `dist/` with SPA fallback)
- [ ] Document production env matrix: backend `ALLOWED_ORIGINS`, Supabase keys, `DATABASE_URL`, OpenAI; frontend `VITE_*` at build time
- [ ] Configure Supabase Auth Site URL and redirect URLs for the production frontend origin
- [ ] Run `alembic upgrade head` against the target Supabase project before traffic
- [ ] Confirm corpus loaded in the target project (or run ingestion runbook)
- [ ] Set health check to `/health`; optional `/health/ready` with DB ping
- [ ] Smoke-test prod: sign-in, stream chat, citations, refusal path
- [ ] Fill in root README “Running locally” with copy-paste commands (or link consolidated guide)

## Phase 10: launch readiness

- [ ] Tighten observability, logging, and failure handling (`structlog` configuration, JSON in prod)
- [ ] Review security boundaries for auth, tokens, service-role usage, and DB connection role vs RLS
- [ ] Add rate limiting on `/chat/stream` and auth-sensitive routes
- [ ] Create runbooks for ingestion, app startup, corpus refresh, and incident response
- [ ] Prepare a pilot rollout plan for 5 senior analysts
- [ ] Document known limitations and the explicit out-of-scope boundaries
- [ ] CI: pytest + ruff + frontend `tsc` / lint on PRs

Practical recommendation — build in this order:

1. Backend foundation + auth
2. Database schema + ingestion pipeline
3. Retrieval + grounding
4. LLM orchestration + chat endpoints
5. Frontend UI
6. Pilot validation (Phase 8)
7. Deployment (Phase 9)
8. Launch hardening (Phase 10)

This keeps the system grounded in the actual trust contract first and prevents the frontend from becoming a polished wrapper around a weak backend.
