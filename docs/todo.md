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
- [ ] Set up Supabase Auth integration and bearer-token verification middleware/dependencies
- [ ] Define the authenticated user context and rule that all chat actions are user-scoped
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

- [ ] Build the SEC filing download flow for the curated corpus
- [ ] Create parsing logic for the filing HTML/text extraction pipeline
- [ ] Normalize document metadata and preserve page-level references
- [ ] Chunk filings into retrieval-friendly segments with page provenance
- [ ] Generate embeddings for each chunk using the configured model
- [ ] Store documents, chunks, embeddings, and metadata in Supabase/Postgres
- [ ] Validate retrieval inputs with a small sample corpus before going wider
- [ ] Add ingestion tests for parsing, chunking, and metadata integrity

## Phase 4: retrieval and grounding

- [ ] Implement semantic retrieval over chunk embeddings
- [ ] Implement lexical retrieval over search vectors
- [ ] Fuse the ranked result sets with reciprocal rank fusion (RRF)
- [ ] Create the retrieval service to fetch top chunks and nearby context for grounding
- [ ] Define the grounding contract: answers must cite retrieved evidence and only state what the corpus supports
- [ ] Build a citation validator that checks answer claims against retrieved passages
- [ ] Add tests for retrieval quality, citation extraction, and insufficient-evidence handling
- [ ] Document refusal behavior when the corpus does not support the answer

## Phase 5: LLM orchestration and assistant logic

- [ ] Define the typed assistant output schema for grounded answers and citations
- [ ] Create the PydanticAI agent boundary and dependency injection model
- [ ] Write system instructions for:
  - [ ] grounded-only answers
  - [ ] explicit citations
  - [ ] no invented facts
  - [ ] concise but verifiable responses
  - [ ] no stock recommendations or investment advice
- [ ] Build the chat orchestrator for one turn of retrieval + answer generation + save-to-db
- [ ] Implement message conversion between AI SDK format and internal types
- [ ] Add backend streaming response handling for incremental chat output
- [ ] Add structured logging and usage metadata capture

## Phase 6: chat API and persistence

- [ ] Build the thread creation and listing endpoints
- [ ] Build the message history retrieval endpoints
- [ ] Build the streaming chat endpoint with authenticated request validation
- [ ] Persist user messages and assistant replies to the database
- [ ] Persist citation records and referenced passages for later display
- [ ] Confirm the answer contract is consistent with the frontend consumer expectations
- [ ] Validate the API against sample analyst prompts from the client brief

## Phase 7: frontend app shell and chat UI

- [ ] Set up the Vite React SPA and app routing
- [ ] Add the Supabase browser client and environment validation module
- [ ] Create shared API helpers for bearer-token-authenticated calls
- [ ] Build the login / auth flow using Driftwood email addresses
- [ ] Build the thread list and conversation history UI
- [ ] Build the chat composer and streaming message interface
- [ ] Display citations, source filings, page references, and underlying passages
- [ ] Add empty states, loading states, and error handling for invalid or unsupported questions
- [ ] Ensure the frontend does not contain any privileged credentials or server-side logic

## Phase 8: end-to-end validation against the client brief
- [ ] Test the core analyst questions from the brief with real corpus-backed answers
- [ ] Confirm each answer includes precise filing and page citations
- [ ] Validate that the system refuses unsupported claims explicitly and clearly
- [ ] Check the experience for the pilot analyst group: trust, speed, and usefulness
- [ ] Measure whether the workflow saves at least 3 hours per analyst per week
- [ ] Review any gaps in retrieval quality or citation clarity before scaling out

## Phase 9: launch readiness
- [ ] Tighten observability, logging, and failure handling
- [ ] Review security boundaries for auth, tokens, and service-role usage
- [ ] Validate deployment readiness for Railway + Supabase
- [ ] Create runbooks for ingestion, app startup, and incident response
- [ ] Prepare a pilot rollout plan for 5 senior analysts
- [ ] Document known limitations and the explicit out-of-scope boundaries

Practical recommendation
Build in this order:

Backend foundation + auth
Database schema + ingestion pipeline
Retrieval + grounding
LLM orchestration + chat endpoints
Frontend UI
Pilot validation and rollout
This keeps the system grounded in the actual trust contract first and prevents the frontend from becoming a polished wrapper around a weak backend.