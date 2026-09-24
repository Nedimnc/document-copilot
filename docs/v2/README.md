# Second product line (v2)

Document Copilot ([client brief](../client-brief.md)) stays the **filing Q&A + citation** product. v2 is a **separate repo and trust model**, reusing stack patterns from this monorepo.

## Team decision (recorded)

**Selected concept:** [Fundamentals Lab](fundamentals-lab-brief.md) — Option A from scope planning.

| Option | Headline | Why not primary v2 |
| ------ | -------- | ------------------ |
| **A — Fundamentals Lab** | Screen any ticker, charts, Buy/Hold/Sell from **visible criteria** | **Chosen** — matches “dynamic UI + ratings” without duplicating RAG |
| B — Ticker dossier | On-demand EDGAR + chat per ticker | Overlaps Copilot; ops-heavy |
| C — Research memo generator | Transcripts/RSS drafts | Weaker trust; different sources |
| D — Watchlist monitor | Alerts + event timeline | Demo-friendly but narrow |

**One-liner for stakeholders**

- **Copilot:** “Cite the filing page for this question.”
- **Fundamentals Lab:** “Show me which names pass our rules and chart the metrics behind the rating.”

## Documents

- [Fundamentals Lab one-pager](fundamentals-lab-brief.md)
- [Scaffold a new repo from Document Copilot](scaffold-from-copilot.md)

## Explicit non-goals for v2 in Copilot repo

Do not add to Document Copilot: live quotes, universal ticker search, recommendation engine, or chart-first UI. Ship Copilot pilot + Railway first ([pilot validation](../guides/pilot-validation.md), [Railway](../guides/railway-deployment.md)).
