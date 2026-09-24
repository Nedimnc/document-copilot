from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ChatMessage,
    ChatThread,
    DocumentChunk,
    MessageCitation,
    SourceDocument,
)

# Chat rows are owned by CurrentUser.id. Every helper takes user_id so a
# missing filter cannot leak another analyst's threads.


async def create_thread(
    session: AsyncSession, *, user_id: UUID, title: str | None = None
) -> ChatThread:
    thread = ChatThread(user_id=user_id, title=title)
    session.add(thread)
    await session.flush()
    return thread


async def list_threads(session: AsyncSession, *, user_id: UUID) -> list[ChatThread]:
    result = await session.execute(
        select(ChatThread)
        .where(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.desc())
    )
    return list(result.scalars())


async def get_thread(
    session: AsyncSession, *, user_id: UUID, thread_id: UUID
) -> ChatThread | None:
    result = await session.execute(
        select(ChatThread).where(
            ChatThread.id == thread_id, ChatThread.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def delete_thread(
    session: AsyncSession, *, user_id: UUID, thread_id: UUID
) -> None:
    thread = await get_thread(session, user_id=user_id, thread_id=thread_id)
    if thread is None:
        raise LookupError("thread not found")
    await session.delete(thread)
    await session.flush()


async def get_thread_by_id(
    session: AsyncSession, *, thread_id: UUID
) -> ChatThread | None:
    # Unscoped lookup so the API can return 404 vs 403. Do not use this
    # result without an owner check.
    result = await session.execute(
        select(ChatThread).where(ChatThread.id == thread_id)
    )
    return result.scalar_one_or_none()


async def create_message(
    session: AsyncSession,
    *,
    user_id: UUID,
    thread_id: UUID,
    role: str,
    content: str,
    payload: dict[str, Any] | None = None,
) -> ChatMessage:
    thread = await get_thread(session, user_id=user_id, thread_id=thread_id)
    if thread is None:
        raise LookupError("thread not found")

    now = datetime.now(UTC)
    message = ChatMessage(
        thread_id=thread.id,
        role=role,
        content=content,
        payload=payload,
        created_at=now,
    )
    session.add(message)
    thread.updated_at = now
    await session.flush()
    return message


async def list_messages(
    session: AsyncSession, *, user_id: UUID, thread_id: UUID
) -> list[ChatMessage]:
    thread = await get_thread(session, user_id=user_id, thread_id=thread_id)
    if thread is None:
        raise LookupError("thread not found")

    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread.id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars())


async def create_citations(
    session: AsyncSession,
    *,
    user_id: UUID,
    message_id: UUID,
    citations: list[MessageCitation],
) -> list[MessageCitation]:
    result = await session.execute(
        select(ChatMessage).where(ChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise LookupError("message not found")

    thread = await get_thread(session, user_id=user_id, thread_id=message.thread_id)
    if thread is None:
        raise LookupError("thread not found")

    for citation in citations:
        citation.message_id = message.id
        session.add(citation)
    await session.flush()
    return citations


@dataclass(frozen=True, slots=True)
class CitationRecord:
    id: UUID
    message_id: UUID
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


async def list_citations_for_thread(
    session: AsyncSession, *, user_id: UUID, thread_id: UUID
) -> dict[UUID, list[CitationRecord]]:
    thread = await get_thread(session, user_id=user_id, thread_id=thread_id)
    if thread is None:
        raise LookupError("thread not found")

    result = await session.execute(
        select(MessageCitation, SourceDocument, DocumentChunk)
        .join(SourceDocument, MessageCitation.document_id == SourceDocument.id)
        .join(DocumentChunk, MessageCitation.chunk_id == DocumentChunk.id)
        .join(ChatMessage, MessageCitation.message_id == ChatMessage.id)
        .where(ChatMessage.thread_id == thread.id)
        .order_by(MessageCitation.message_id.asc(), MessageCitation.sort_order.asc())
    )
    grouped: dict[UUID, list[CitationRecord]] = {}
    for citation, document, chunk in result.all():
        grouped.setdefault(citation.message_id, []).append(
            CitationRecord(
                id=citation.id,
                message_id=citation.message_id,
                chunk_id=citation.chunk_id,
                document_id=citation.document_id,
                sort_order=citation.sort_order,
                excerpt=citation.excerpt,
                page=citation.page,
                ticker=document.ticker,
                company_name=document.company_name,
                filing_type=document.filing_type,
                fiscal_year=document.fiscal_year,
                filing_date=document.filing_date,
                source_url=document.source_url,
                section=chunk.section,
            )
        )
    return grouped


async def list_citations(
    session: AsyncSession, *, user_id: UUID, message_id: UUID
) -> list[MessageCitation]:
    result = await session.execute(
        select(ChatMessage).where(ChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise LookupError("message not found")

    thread = await get_thread(session, user_id=user_id, thread_id=message.thread_id)
    if thread is None:
        raise LookupError("thread not found")

    citation_result = await session.execute(
        select(MessageCitation)
        .where(MessageCitation.message_id == message.id)
        .order_by(MessageCitation.sort_order.asc())
    )
    return list(citation_result.scalars())
