"""AI SDK UI message stream (SSE) helpers."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

# Matches UI_MESSAGE_STREAM_HEADERS from the `ai` package.
UI_MESSAGE_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Vercel-AI-UI-Message-Stream": "v1",
    "X-Accel-Buffering": "no",
}

TEXT_CHUNK_SIZE = 16


def format_sse(payload: dict[str, Any] | str) -> bytes:
    if payload == "[DONE]":
        return b"data: [DONE]\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n".encode()


def chunk_text(text: str, size: int = TEXT_CHUNK_SIZE) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + size] for index in range(0, len(text), size)]


def iter_ui_message_start(message_id: str) -> Iterator[dict[str, Any]]:
    yield {"type": "start", "messageId": message_id}
    yield {"type": "start-step"}


def iter_ui_message_finish() -> Iterator[dict[str, Any]]:
    yield {"type": "finish-step"}
    yield {"type": "finish"}


def iter_text_part_events(
    *, message_id: str, text: str, text_id: str = "0"
) -> Iterator[dict[str, Any]]:
    yield from iter_ui_message_start(message_id)
    yield {"type": "text-start", "id": text_id}
    for delta in chunk_text(text):
        yield {"type": "text-delta", "id": text_id, "delta": delta}
    yield {"type": "text-end", "id": text_id}
    yield from iter_ui_message_finish()


async def iter_streamed_text_part_events(
    *,
    message_id: str,
    text_deltas: AsyncIterator[str],
    text_id: str = "0",
) -> AsyncIterator[dict[str, Any]]:
    for event in iter_ui_message_start(message_id):
        yield event
    yield {"type": "text-start", "id": text_id}
    async for delta in text_deltas:
        if delta:
            yield {"type": "text-delta", "id": text_id, "delta": delta}
    yield {"type": "text-end", "id": text_id}
    for event in iter_ui_message_finish():
        yield event
