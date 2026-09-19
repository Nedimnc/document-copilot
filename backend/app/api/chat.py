from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.user import CurrentUser
from app.chat.messages import UIMessageIn, last_user_text, ui_payload
from app.chat.streaming import (
    CHUNK_DELAY_SECONDS,
    UI_MESSAGE_STREAM_HEADERS,
    format_sse,
    iter_stub_events,
    stub_reply_text,
)
from app.database.chats import (
    create_message,
    create_thread,
    get_thread,
    get_thread_by_id,
    list_messages,
    list_threads,
)
from app.database.models import ChatMessage, ChatThread
from app.database.session import get_db_session, get_session_factory

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateThreadRequest(BaseModel):
    title: str | None = None


class ThreadResponse(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    parts: list[TextPart]
    created_at: datetime


class StreamChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: UUID | None = None
    thread_id: UUID | None = Field(default=None, alias="threadId")
    messages: list[UIMessageIn]
    trigger: str | None = None
    message_id: str | None = Field(default=None, alias="messageId")

    def resolved_thread_id(self) -> UUID:
        thread_id = self.thread_id or self.id
        if thread_id is None:
            raise ValueError("thread id is required")
        return thread_id


def _thread_response(thread: ChatThread) -> ThreadResponse:
    return ThreadResponse(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


def _message_response(message: ChatMessage) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        parts=[TextPart(text=message.content)],
        created_at=message.created_at,
    )


async def require_owned_thread(
    session: AsyncSession, *, user_id: UUID, thread_id: UUID
) -> ChatThread:
    thread = await get_thread_by_id(session, thread_id=thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )
    if thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this thread",
        )
    return thread


async def persist_stub_turn(
    *, user_id: UUID, thread_id: UUID, user_text: str, assistant_text: str
) -> None:
    factory = get_session_factory()
    async with factory() as session:
        thread = await get_thread(session, user_id=user_id, thread_id=thread_id)
        if thread is None:
            raise LookupError("thread not found")
        if not thread.title:
            thread.title = user_text[:80]

        await create_message(
            session,
            user_id=user_id,
            thread_id=thread_id,
            role="user",
            content=user_text,
            payload=ui_payload(user_text),
        )
        await create_message(
            session,
            user_id=user_id,
            thread_id=thread_id,
            role="assistant",
            content=assistant_text,
            payload=ui_payload(assistant_text),
        )
        await session.commit()


@router.get("/threads")
async def get_threads(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ThreadResponse]:
    threads = await list_threads(session, user_id=current_user.id)
    return [_thread_response(thread) for thread in threads]


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def post_thread(
    body: CreateThreadRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ThreadResponse:
    thread = await create_thread(
        session, user_id=current_user.id, title=body.title
    )
    return _thread_response(thread)


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MessageResponse]:
    await require_owned_thread(
        session, user_id=current_user.id, thread_id=thread_id
    )
    messages = await list_messages(
        session, user_id=current_user.id, thread_id=thread_id
    )
    return [_message_response(message) for message in messages]


@router.post("/stream")
async def stream_chat(
    body: StreamChatRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    try:
        thread_id = body.resolved_thread_id()
        user_text = last_user_text(body.messages)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    await require_owned_thread(
        session, user_id=current_user.id, thread_id=thread_id
    )

    assistant_text = stub_reply_text(user_text)
    message_id = str(uuid4())

    async def generate() -> AsyncIterator[bytes]:
        for event in iter_stub_events(message_id=message_id, text=assistant_text):
            if await request.is_disconnected():
                return
            yield format_sse(event)
            if CHUNK_DELAY_SECONDS:
                await asyncio.sleep(CHUNK_DELAY_SECONDS)

        if await request.is_disconnected():
            return

        await persist_stub_turn(
            user_id=current_user.id,
            thread_id=thread_id,
            user_text=user_text,
            assistant_text=assistant_text,
        )
        yield format_sse("[DONE]")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=UI_MESSAGE_STREAM_HEADERS,
    )
