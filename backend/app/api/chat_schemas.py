from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.chats import CitationRecord


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class CitationResponse(BaseModel):
    id: UUID
    chunk_id: UUID
    document_id: UUID
    sort_order: int
    excerpt: str
    page: int | None
    ticker: str
    company_name: str
    filing_type: str
    fiscal_year: int
    filing_date: date
    source_url: str
    section: str | None

    @classmethod
    def from_record(cls, record: CitationRecord) -> CitationResponse:
        return cls(
            id=record.id,
            chunk_id=record.chunk_id,
            document_id=record.document_id,
            sort_order=record.sort_order,
            excerpt=record.excerpt,
            page=record.page,
            ticker=record.ticker,
            company_name=record.company_name,
            filing_type=record.filing_type,
            fiscal_year=record.fiscal_year,
            filing_date=record.filing_date,
            source_url=record.source_url,
            section=record.section,
        )


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    parts: list[TextPart]
    citations: list[CitationResponse] = Field(default_factory=list)
    created_at: datetime
