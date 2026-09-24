# Phase 8 — pilot validation

Goal from [client brief](../client-brief.md): **5 senior analysts** use Document Copilot for one week and report **≥3 hours saved per analyst per week** on filing intake. This guide covers automated checks and the human pilot checklist.

## Automated brief-question smoke (optional)

Requires: populated corpus, `backend/.env`, at least one `profiles` row (sign up once in the app).

Run all ten client-brief example questions sequentially (calls OpenAI; costs apply):

```bash
cd backend
uv run python smoke_assistant.py --brief-all
```

Run a single preset:

```bash
uv run python smoke_assistant.py --brief q01
uv run python smoke_assistant.py --brief q10_refusal
```

Review each answer manually for:

- At least one `[n]` citation when the answer is factual
- Sources panel opens and excerpts look plausible
- Question 10 and investment-advice prompts refuse or stay filing-bound

## Manual UI checklist (per analyst)

- [ ] Sign in with Driftwood email (Supabase)
- [ ] Thread list loads; new chat works
- [ ] Streaming status phases appear (searching → generating → validating)
- [ ] Inline `[1]` links jump to source cards
- [ ] SEC filing link opens correct ticker/year
- [ ] Unsupported question returns clear “not enough evidence” styling
- [ ] Chat history persists after logout/login

## Ten brief questions (human sign-off)

| ID | Topic | Pass criteria |
| ---- | ----- | ------------- |
| q01 | Apple revenue mix 2021–2025 | Cited; mix categories mentioned |
| q02 | Amazon AWS vs segments | Cited; compares segments/years |
| q03 | NVIDIA Data Center | Cited demand/supply language |
| q04 | Microsoft Azure / AI infra | Cited wording changes |
| q05 | Alphabet revenue lines | Cited segment trends |
| q06 | Cross-company risk factors (AI, etc.) | Cited or honest partial coverage |
| q07 | Apple + NVIDIA supplier concentration | Cited; trend if present in corpus |
| q08 | CapEx / purchase commitments (4 names) | Cited numbers or ranges |
| q09 | Geographic revenue (each company) | Cited latest 10-K exposures |
| q10 | Gen AI improved margins? | Refusal or evidence-only; no overclaim |

Record: analyst name, date, question id, pass/fail, notes (retrieval miss vs citation vs excerpt quality).

## Pilot rollout (5 analysts)

1. Deploy to Railway ([railway-deployment.md](railway-deployment.md)) or shared staging URL.
2. Create Supabase users or invite via email auth.
3. Share 15-minute walkthrough: trust model (citations, not advice), sample questions.
4. Collect time-saved estimate via simple form (before/after weekly intake hours).
5. Triage: retrieval gaps → corpus/chunk quality; UI → frontend; refusals → grounding copy.

## Out of scope for this pilot

Do not evaluate Document Copilot on: dynamic any-ticker search, live market data, charts, or buy/sell/hold. Those belong to a separate product ([Fundamentals Lab](../v2/fundamentals-lab-brief.md)).
