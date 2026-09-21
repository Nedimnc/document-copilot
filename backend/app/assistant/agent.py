from __future__ import annotations

from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from app.assistant.instructions import BASE_SYSTEM_INSTRUCTIONS
from app.config import Settings, settings

# Cap cost per chat turn during the pilot.
DEFAULT_USAGE_LIMITS = UsageLimits(request_limit=4, total_tokens_limit=16_000)

MAX_HISTORY_TURNS = 6


def build_document_agent(
    app_settings: Settings | None = None,
) -> Agent[None, str]:
    loaded = app_settings or settings
    model_name = f"openai:{loaded.openai_chat_model}"
    return Agent(
        model_name,
        instructions=BASE_SYSTEM_INSTRUCTIONS,
        output_type=str,
        retries=1,
    )
