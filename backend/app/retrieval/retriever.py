"""Hybrid retrieval: semantic + lexical search, RRF fusion, grounding passages."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.documents import (
    get_adjacent_chunks,
    load_chunks_with_documents,
    search_chunk_ids_lexical,
    search_chunk_ids_semantic,
)
from app.database.models import DocumentChunk, SourceDocument
from app.retrieval.embeddings import embed_query
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.types import RetrievedPassage

# Over-fetch per retriever, fuse, then trim — same pattern as ai-cookbook hybrid search.
CANDIDATE_K = 50
TOP_K = 10
NEIGHBOR_CONTEXT_FOR_TOP_N = 3


@dataclass(frozen=True, slots=True)
class RetrievalOptions:
    candidate_k: int = CANDIDATE_K
    top_k: int = TOP_K
    include_neighbors: bool = False
    neighbor_context_for_top_n: int = NEIGHBOR_CONTEXT_FOR_TOP_N


class DocumentRetriever:
    def __init__(self, *, openai_client: AsyncOpenAI | None = None) -> None:
        self._client = openai_client or AsyncOpenAI()

    async def retrieve(
        self,
        session: AsyncSession,
        *,
        query: str,
        options: RetrievalOptions | None = None,
    ) -> list[RetrievedPassage]:
        opts = options or RetrievalOptions()
        if not query.strip():
            return []

        query_embedding = await embed_query(self._client, text=query)
        semantic_ids = await search_chunk_ids_semantic(
            session,
            query_embedding=query_embedding,
            limit=opts.candidate_k,
        )
        lexical_ids = await search_chunk_ids_lexical(
            session,
            query=query,
            limit=opts.candidate_k,
        )
        fused = reciprocal_rank_fusion([semantic_ids, lexical_ids])[: opts.top_k]
        if not fused:
            return []

        fused_ids = [chunk_id for chunk_id, _score in fused]
        score_by_id = {chunk_id: score for chunk_id, score in fused}
        rows = await load_chunks_with_documents(session, fused_ids)

        passages: list[RetrievedPassage] = []
        seen: set[UUID] = set()
        for label, (chunk, document) in enumerate(rows, start=1):
            seen.add(chunk.id)
            passages.append(
                _to_passage(
                    chunk,
                    document,
                    rrf_score=score_by_id.get(chunk.id),
                    citation_label=label,
                    is_neighbor=False,
                )
            )

        if opts.include_neighbors:
            for chunk, document in rows[: opts.neighbor_context_for_top_n]:
                neighbors = await get_adjacent_chunks(
                    session,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                )
                for neighbor in neighbors:
                    if neighbor.id in seen:
                        continue
                    seen.add(neighbor.id)
                    passages.append(
                        _to_passage(
                            neighbor,
                            document,
                            rrf_score=None,
                            citation_label=None,
                            is_neighbor=True,
                        )
                    )

        return passages


def citable_passages(passages: list[RetrievedPassage]) -> list[RetrievedPassage]:
    return [passage for passage in passages if passage.citation_label is not None]


def _to_passage(
    chunk: DocumentChunk,
    document: SourceDocument,
    *,
    rrf_score: float | None,
    citation_label: int | None,
    is_neighbor: bool,
) -> RetrievedPassage:
    return RetrievedPassage(
        chunk_id=chunk.id,
        document_id=document.id,
        chunk_index=chunk.chunk_index,
        content=chunk.content,
        page=chunk.page,
        section=chunk.section,
        ticker=document.ticker,
        company_name=document.company_name,
        filing_type=document.filing_type,
        filing_date=document.filing_date,
        fiscal_year=document.fiscal_year,
        source_url=document.source_url,
        rrf_score=rrf_score,
        citation_label=citation_label,
        is_neighbor=is_neighbor,
    )
