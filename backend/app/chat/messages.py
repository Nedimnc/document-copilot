"""Convert AI SDK UI messages to plain text we can persist."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)


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


def ui_messages_to_model_history(
    messages: list[UIMessageIn],
    *,
    max_turns: int = 6,
) -> list[ModelMessage]:
    """Map prior UI turns to PydanticAI history, excluding the latest user message."""
    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None

    for message in messages:
        text = extract_text(message).strip()
        if not text:
            continue
        if message.role == "user":
            pending_user = text
        elif message.role == "assistant" and pending_user is not None:
            pairs.append((pending_user, text))
            pending_user = None

    if len(pairs) > max_turns:
        pairs = pairs[-max_turns:]

    history: list[ModelMessage] = []
    for user_text, assistant_text in pairs:
        history.append(ModelRequest(parts=[UserPromptPart(user_text)]))
        history.append(
            ModelResponse(
                parts=[TextPart(assistant_text)],
                model_name="document-copilot",
            )
        )
    return history
