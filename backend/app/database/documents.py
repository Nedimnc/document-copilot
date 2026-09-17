from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DocumentChunk, SourceDocument


async def add_source_document(
    session: AsyncSession, document: SourceDocument
) -> SourceDocument:
    session.add(document)
    await session.flush()
    return document


async def get_source_document(
    session: AsyncSession, document_id: UUID
) -> SourceDocument | None:
    result = await session.execute(
        select(SourceDocument).where(SourceDocument.id == document_id)
    )
    return result.scalar_one_or_none()


async def get_source_document_by_accession(
    session: AsyncSession, accession_number: str
) -> SourceDocument | None:
    result = await session.execute(
        select(SourceDocument).where(
            SourceDocument.accession_number == accession_number
        )
    )
    return result.scalar_one_or_none()


async def list_source_documents(
    session: AsyncSession, *, ticker: str | None = None
) -> list[SourceDocument]:
    stmt = select(SourceDocument).order_by(
        SourceDocument.ticker.asc(), SourceDocument.filing_date.desc()
    )
    if ticker is not None:
        stmt = stmt.where(SourceDocument.ticker == ticker)
    result = await session.execute(stmt)
    return list(result.scalars())


async def add_chunks(
    session: AsyncSession, chunks: list[DocumentChunk]
) -> list[DocumentChunk]:
    session.add_all(chunks)
    await session.flush()
    return chunks


async def get_chunk(session: AsyncSession, chunk_id: UUID) -> DocumentChunk | None:
    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.id == chunk_id)
    )
    return result.scalar_one_or_none()


async def get_chunks_by_ids(
    session: AsyncSession, chunk_ids: list[UUID]
) -> list[DocumentChunk]:
    if not chunk_ids:
        return []
    result = await session.execute(
        select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
    )
    chunks = list(result.scalars())
    by_id = {chunk.id: chunk for chunk in chunks}
    return [by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in by_id]


async def get_chunks_for_document(
    session: AsyncSession, document_id: UUID
) -> list[DocumentChunk]:
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(result.scalars())
