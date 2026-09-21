from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RetrievedPassage:
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    page: int | None
    section: str | None
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    fiscal_year: int
    source_url: str
    rrf_score: float | None
    citation_label: int | None
    is_neighbor: bool = False
