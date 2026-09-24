from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.chat_schemas import CitationResponse, MessageResponse, TextPart
from app.auth.dependencies import get_current_user
from app.auth.user import CurrentUser
from app.chat.messages import UIMessageIn, last_user_text
from app.chat.orchestrator import stream_chat_turn
from app.chat.streaming import UI_MESSAGE_STREAM_HEADERS, format_sse
from app.database.chats import (
    create_thread,
    delete_thread,
    get_thread_by_id,
    list_citations_for_thread,
    list_messages,
    list_threads,
)
from app.database.models import ChatMessage, ChatThread
from app.database.session import get_db_session

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateThreadRequest(BaseModel):
    title: str | None = None


class ThreadResponse(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


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


def _message_response(
    message: ChatMessage,
    *,
    citations: list[CitationResponse] | None = None,
) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        parts=[TextPart(text=message.content)],
        citations=citations or [],
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


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_owned_thread(
    thread_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await require_owned_thread(
        session, user_id=current_user.id, thread_id=thread_id
    )
    await delete_thread(session, user_id=current_user.id, thread_id=thread_id)


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
    citations_by_message = await list_citations_for_thread(
        session, user_id=current_user.id, thread_id=thread_id
    )
    return [
        _message_response(
            message,
            citations=[
                CitationResponse.from_record(record)
                for record in citations_by_message.get(message.id, [])
            ],
        )
        for message in messages
    ]


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

    async def generate() -> AsyncIterator[bytes]:
        async for event in stream_chat_turn(
            session,
            user_id=current_user.id,
            thread_id=thread_id,
            user_text=user_text,
            ui_messages=body.messages,
        ):
            if await request.is_disconnected():
                return
            yield format_sse(event)

        if await request.is_disconnected():
            return

        yield format_sse("[DONE]")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers=UI_MESSAGE_STREAM_HEADERS,
    )
