from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.retrieval.retriever import DocumentRetriever


@dataclass(frozen=True, slots=True)
class DocumentAgentDeps:
    user_id: UUID
    thread_id: UUID
    retriever: DocumentRetriever | None = None
