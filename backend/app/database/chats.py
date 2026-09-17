from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatMessage, ChatThread, MessageCitation


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
