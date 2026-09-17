from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR

from app.database.models import (
    EMBEDDING_DIMENSIONS,
    Base,
    ChatMessage,
    ChatThread,
    DocumentChunk,
    MessageCitation,
    Profile,
    SourceDocument,
)


def test_metadata_contains_expected_tables():
    assert set(Base.metadata.tables) == {
        "profiles",
        "chat_threads",
        "chat_messages",
        "source_documents",
        "document_chunks",
        "message_citations",
    }


def test_source_document_has_filing_metadata_columns():
    columns = set(SourceDocument.__table__.columns.keys())

    assert {
        "ticker",
        "company_name",
        "cik",
        "filing_type",
        "filing_date",
        "report_date",
        "fiscal_year",
        "accession_number",
        "source_url",
        "markdown_content",
    }.issubset(columns)


def test_chunk_uses_pgvector_and_generated_search_vector():
    embedding = DocumentChunk.__table__.c.embedding
    search_vector = DocumentChunk.__table__.c.search_vector

    assert isinstance(embedding.type, Vector)
    assert embedding.type.dim == EMBEDDING_DIMENSIONS
    assert isinstance(search_vector.type, TSVECTOR)
    assert search_vector.computed is not None


def test_chunk_metadata_and_citation_payload_are_jsonb():
    assert isinstance(DocumentChunk.__table__.c.chunk_metadata.type, JSONB)
    assert isinstance(ChatMessage.__table__.c.payload.type, JSONB)


def test_chat_tables_are_user_scoped():
    assert "user_id" in ChatThread.__table__.columns
    assert ChatMessage.__table__.c.thread_id.foreign_keys
    assert MessageCitation.__table__.c.message_id.foreign_keys
    assert Profile.__table__.c.id.primary_key
