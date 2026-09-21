import asyncio
from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.database.models import DocumentChunk, SourceDocument
from app.retrieval.retriever import DocumentRetriever, RetrievalOptions


def _chunk(chunk_id: UUID, *, document_id: UUID, index: int) -> DocumentChunk:
    return DocumentChunk(
        id=chunk_id,
        document_id=document_id,
        chunk_index=index,
        content=f"chunk {index} text",
        token_count=10,
        embedding=[0.0] * 1536,
    )


def _document(document_id: UUID) -> SourceDocument:
    return SourceDocument(
        id=document_id,
        ticker="AAPL",
        company_name="Apple Inc.",
        cik="0000320193",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        accession_number="0000320193-24-000123",
        source_url="https://example.com/aapl",
        markdown_content="",
    )


def test_retrieve_fuses_and_labels_passages():
    doc_id = UUID("11111111-1111-4111-8111-111111111111")
    chunk_a = UUID("22222222-2222-4222-8222-222222222222")
    chunk_b = UUID("33333333-3333-4333-8333-333333333333")
    session = AsyncMock()
    retriever = DocumentRetriever(openai_client=AsyncMock())

    with (
        patch(
            "app.retrieval.retriever.embed_query",
            new=AsyncMock(return_value=[0.1] * 1536),
        ),
        patch(
            "app.retrieval.retriever.search_chunk_ids_semantic",
            new=AsyncMock(return_value=[chunk_a, chunk_b]),
        ),
        patch(
            "app.retrieval.retriever.search_chunk_ids_lexical",
            new=AsyncMock(return_value=[chunk_b, chunk_a]),
        ),
        patch(
            "app.retrieval.retriever.load_chunks_with_documents",
            new=AsyncMock(
                return_value=[
                    (_chunk(chunk_a, document_id=doc_id, index=0), _document(doc_id)),
                    (_chunk(chunk_b, document_id=doc_id, index=1), _document(doc_id)),
                ]
            ),
        ),
        patch(
            "app.retrieval.retriever.get_adjacent_chunks",
            new=AsyncMock(return_value=[]),
        ),
    ):
        passages = asyncio.run(
            retriever.retrieve(
                session,
                query="Apple revenue",
                options=RetrievalOptions(include_neighbors=False, top_k=2),
            )
        )

    assert len(passages) == 2
    assert passages[0].citation_label == 1
    assert passages[0].chunk_id == chunk_a
    assert passages[1].citation_label == 2
    assert passages[0].rrf_score is not None


def test_retrieve_empty_query_returns_no_passages():
    retriever = DocumentRetriever(openai_client=AsyncMock())
    passages = asyncio.run(retriever.retrieve(AsyncMock(), query="   "))
    assert passages == []
