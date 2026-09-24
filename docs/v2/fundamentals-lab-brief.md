# Fundamentals Lab — product one-pager

**Status:** Planned second project (separate repo). **Not** Document Copilot.

## Users

- Driftwood analysts screening coverage lists before deep filing work
- Partners preparing **client-facing** screens (numbers + charts visible on screen)

## Job to be done

Pick tickers (or a saved universe), set **fundamental criteria**, see **tables and charts**, get a **Buy / Hold / Sell** label with a **criteria trace** (which metrics passed or failed—not a black box).

## Data sources (not bulk 10-K RAG)

| Source | Use |
| ------ | --- |
| Market data / fundamentals API (e.g. FMP, Alpha Vantage, Polygon tier) | Prices, ratios, statements, history |
| Optional link-out | SEC filing URL for one metric; optional future Copilot deep-link |

Prototype may use limited free tiers; production requires license review and rate limits.

## Trust model

| Document Copilot | Fundamentals Lab |
| ---------------- | ---------------- |
| “Every claim cites a passage” | “Every rating shows inputs and rules” |
| Refuse when corpus lacks evidence | Flag missing/stale API fields |
| No investment advice | **Explicit disclaimer:** model-assisted rating from **user-defined** criteria; not research advice |

Store: criteria version, raw metrics snapshot, rule outcomes, final label, timestamp.

## MVP UI (v1)

1. Ticker search + watchlist (any symbol API supports)
2. Criteria builder (thresholds: margin, revenue growth, leverage, FCF yield, etc.)
3. Results grid: ticker, key metrics, pass/fail per rule, aggregate rating
4. Company detail: 5y line charts (price, revenue, margin), criteria breakdown
5. Export or copy summary for meetings (CSV or PDF later)

No filing chat in v1 unless optional “open in Copilot” link.

## Out of scope (v1)

- Curated multi-year EDGAR corpus RAG (that is Copilot)
- Autonomous trading or portfolio execution
- Multi-tenant external clients / billing
- Mobile app
- Guaranteed accuracy of third-party API data (show source + as-of date)

## Definition of done (pilot)

Three internal users can: add 10 tickers, define one criteria template, run screen, open two names, and **explain the rating using on-screen numbers** in under 5 minutes without opening a 10-K.

## Stack (reuse from Document Copilot)

FastAPI, Supabase Auth, Vite React, Railway two-service deploy, env modules—see [scaffold-from-copilot.md](scaffold-from-copilot.md).

## Relation to Copilot

```text
Copilot  = intake acceleration (read filings, cite passages)
Lab      = screening acceleration (compare fundamentals, visual criteria)
```

Optional integration later: “Why did margin fail?” → deep link to Copilot with ticker + topic prefilled.
