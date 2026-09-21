from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CitationDraft:
    chunk_id: UUID
    document_id: UUID
    excerpt: str
    page: int | None
    sort_order: int
