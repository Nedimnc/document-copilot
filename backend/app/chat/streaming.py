"""AI SDK UI message stream (SSE) helpers for the stubbed chat slice."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

# Matches UI_MESSAGE_STREAM_HEADERS from the `ai` package.
UI_MESSAGE_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Vercel-AI-UI-Message-Stream": "v1",
    "X-Accel-Buffering": "no",
}

CHUNK_DELAY_SECONDS = 0.03
TEXT_CHUNK_SIZE = 16


def format_sse(payload: dict[str, Any] | str) -> bytes:
    if payload == "[DONE]":
        return b"data: [DONE]\n\n"
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n".encode()


def stub_reply_text(user_text: str) -> str:
    return (
        "This is a stubbed assistant reply. Retrieval is not wired yet. "
        f"You asked: {user_text}"
    )


def chunk_text(text: str, size: int = TEXT_CHUNK_SIZE) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + size] for index in range(0, len(text), size)]


def iter_stub_events(
    *, message_id: str, text: str, text_id: str = "0"
) -> Iterator[dict[str, Any]]:
    yield {"type": "start", "messageId": message_id}
    yield {"type": "start-step"}
    yield {"type": "text-start", "id": text_id}
    for delta in chunk_text(text):
        yield {"type": "text-delta", "id": text_id, "delta": delta}
    yield {"type": "text-end", "id": text_id}
    yield {"type": "finish-step"}
    yield {"type": "finish"}
