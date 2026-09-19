from __future__ import annotations

from datetime import date
from typing import Any

from app.database.models import SourceDocument

# Names for the curated ticker list in data/download.py. Fail if a new
# ticker shows up so we don't store a placeholder company name.
COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
}

LOADABLE_STATUSES = frozenset({"success", "exists"})


def company_name_for(ticker: str) -> str:
    try:
        return COMPANY_NAMES[ticker]
    except KeyError as exc:
        raise ValueError(f"Unknown ticker {ticker!r}; add it to COMPANY_NAMES") from exc


def document_from_filing(filing: dict[str, Any], markdown: str) -> SourceDocument:
    ticker = filing["ticker"]
    report = filing.get("report_date") or filing["filing_date"]
    report_date = date.fromisoformat(filing["report_date"]) if filing.get("report_date") else None
    return SourceDocument(
        ticker=ticker,
        company_name=company_name_for(ticker),
        cik=filing["cik"],
        filing_type=filing["form"],
        filing_date=date.fromisoformat(filing["filing_date"]),
        report_date=report_date,
        fiscal_year=int(str(report)[:4]),
        accession_number=filing["accession_number"],
        primary_document=filing.get("primary_document"),
        source_url=filing["source_url"],
        markdown_content=markdown,
    )
