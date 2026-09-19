"""Convert AI SDK UI messages to plain text we can persist."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UIMessageIn(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    role: str
    parts: list[dict[str, Any]] = Field(default_factory=list)


def extract_text(message: UIMessageIn) -> str:
    texts: list[str] = []
    for part in message.parts:
        if part.get("type") == "text" and isinstance(part.get("text"), str):
            texts.append(part["text"])
    return "".join(texts)


def last_user_text(messages: list[UIMessageIn]) -> str:
    for message in reversed(messages):
        if message.role != "user":
            continue
        text = extract_text(message).strip()
        if text:
            return text
    raise ValueError("Request must include a user message with text")


def ui_payload(content: str) -> dict[str, Any]:
    return {"parts": [{"type": "text", "text": content}]}
