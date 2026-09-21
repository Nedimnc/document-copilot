"""One chat turn: retrieve, generate, validate, persist."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID, uuid4

import structlog
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.agent import DEFAULT_USAGE_LIMITS, build_document_agent
from app.assistant.instructions import full_system_instructions
from app.chat.grounding import prepare_grounded_turn
from app.chat.messages import UIMessageIn, ui_messages_to_model_history, ui_payload
from app.chat.status import status_event
from app.database.chats import create_citations, create_message, get_thread
from app.grounding.refusal import (
    GROUNDING_VALIDATION_FAILURE_MESSAGE,
    INSUFFICIENT_EVIDENCE_USER_MESSAGE,
    LLM_UNAVAILABLE_MESSAGE,
)
from app.grounding.validator import (
    build_message_citations,
    canonicalize_answer_citations,
    drafts_to_message_citations,
)
from app.retrieval.retriever import DocumentRetriever

logger = structlog.get_logger(__name__)


async def stream_chat_turn(
    session: AsyncSession,
    *,
    user_id: UUID,
    thread_id: UUID,
    user_text: str,
    ui_messages: list[UIMessageIn],
    agent: Agent[None, str] | None = None,
    retriever: DocumentRetriever | None = None,
) -> AsyncIterator[dict[str, Any]]:
    message_id = str(uuid4())
    text_id = "0"
    retrieval_started = time.perf_counter()

    thread = await get_thread(session, user_id=user_id, thread_id=thread_id)
    if thread is None:
        raise LookupError("thread not found")

    await create_message(
        session,
        user_id=user_id,
        thread_id=thread_id,
        role="user",
        content=user_text,
        payload=ui_payload(user_text),
    )
    if not thread.title:
        thread.title = user_text[:80]
    await session.commit()

    yield status_event(phase="retrieval", label="Searching SEC filings…")

    turn = await prepare_grounded_turn(
        session, query=user_text, retriever=retriever
    )
    retrieval_ms = int((time.perf_counter() - retrieval_started) * 1000)

    log = logger.bind(
        user_id=str(user_id),
        thread_id=str(thread_id),
        query_length=len(user_text),
        passage_count=len(turn.passages),
        retrieval_ms=retrieval_ms,
    )

    if not turn.has_citable_evidence:
        assistant_text = turn.refusal_message or INSUFFICIENT_EVIDENCE_USER_MESSAGE
        log.info("chat_turn_refusal", reason="no_citable_evidence")
        yield status_event(phase="refusal", label="No matching passages in corpus")
        async for event in _stream_fixed_text(
            message_id=message_id,
            text_id=text_id,
            text=assistant_text,
        ):
            yield event
        await _persist_assistant(
            session,
            user_id=user_id,
            thread_id=thread_id,
            content=assistant_text,
            passages=turn.passages,
            cited_labels=[],
        )
        yield status_event(phase="done", label="Done")
        return

    yield status_event(
        phase="generating",
        label=f"Generating answer from {len([p for p in turn.passages if p.citation_label is not None])} passages…",
    )

    active_agent = agent or build_document_agent()
    history = ui_messages_to_model_history(ui_messages)
    instructions = full_system_instructions(grounding_addendum=turn.system_addendum)
    llm_started = time.perf_counter()
    llm_failed = False
    full_text = ""

    try:
        async with active_agent.run_stream(
            user_text,
            message_history=history,
            instructions=instructions,
            usage_limits=DEFAULT_USAGE_LIMITS,
        ) as result:
            delta_buffer: list[str] = []
            async for delta in result.stream_text(delta=True, debounce_by=None):
                delta_buffer.append(delta)
            full_text = "".join(delta_buffer)
            usage = result.usage
            log.info(
                "chat_turn_llm_complete",
                llm_ms=int((time.perf_counter() - llm_started) * 1000),
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
    except ModelHTTPError as exc:
        llm_failed = True
        log.error("chat_turn_llm_http_error", status=exc.status_code, body=exc.body)
    except Exception as exc:
        llm_failed = True
        log.exception("chat_turn_llm_error", error=str(exc))

    if llm_failed:
        async for event in _stream_fixed_text(
            message_id=message_id,
            text_id=text_id,
            text=LLM_UNAVAILABLE_MESSAGE,
        ):
            yield event
        await _persist_assistant(
            session,
            user_id=user_id,
            thread_id=thread_id,
            content=LLM_UNAVAILABLE_MESSAGE,
            passages=turn.passages,
            cited_labels=[],
        )
        yield status_event(phase="done", label="Done")
        return

    yield status_event(phase="validating", label="Checking citations…")
    canonical = canonicalize_answer_citations(full_text, turn.passages)
    if canonical is not None:
        assistant_text = canonical.text
        cited_labels = list(canonical.cited_labels)
        log.info("chat_turn_grounded_ok", cited_labels=cited_labels)
    else:
        assistant_text = GROUNDING_VALIDATION_FAILURE_MESSAGE
        cited_labels = []
        log.warning("chat_turn_grounding_failed")

    async for event in _stream_fixed_text(
        message_id=message_id,
        text_id=text_id,
        text=assistant_text,
    ):
        yield event

    await _persist_assistant(
        session,
        user_id=user_id,
        thread_id=thread_id,
        content=assistant_text,
        passages=turn.passages,
        cited_labels=cited_labels,
    )
    yield status_event(phase="done", label="Done")


async def _stream_fixed_text(
    *, message_id: str, text_id: str, text: str
) -> AsyncIterator[dict[str, Any]]:
    from app.chat.streaming import iter_text_part_events

    for event in iter_text_part_events(
        message_id=message_id, text=text, text_id=text_id
    ):
        yield event


async def _persist_assistant(
    session: AsyncSession,
    *,
    user_id: UUID,
    thread_id: UUID,
    content: str,
    passages: list,
    cited_labels: list[int],
) -> None:
    assistant = await create_message(
        session,
        user_id=user_id,
        thread_id=thread_id,
        role="assistant",
        content=content,
        payload=ui_payload(content),
    )
    if cited_labels:
        drafts = build_message_citations(passages, cited_labels)
        citations = drafts_to_message_citations(assistant.id, drafts)
        await create_citations(
            session,
            user_id=user_id,
            message_id=assistant.id,
            citations=citations,
        )
    await session.commit()
