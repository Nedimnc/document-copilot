# Frontend

Vite + React SPA for Document Copilot. Auth is Supabase email in the browser. The FastAPI backend only verifies the JWT.

## Setup

Copy `.env.example` to `.env` and fill in the public Supabase URL and anon/publishable key. Never put the service-role key here.

```bash
cd frontend
pnpm install
pnpm dev
```

- App: http://localhost:5173
- Sign in / sign up: http://localhost:5173/login
- Chat list: http://localhost:5173/
- Thread: http://localhost:5173/chats/:threadId

## Check

```bash
pnpm tsc --noEmit
pnpm lint
```
