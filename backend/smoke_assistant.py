"""Manual smoke tests for one grounded assistant turn (retrieval + LLM + validation).

Edit the controls in main(), then run from backend/:

    uv run python smoke_assistant.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from uuid import UUID

_BACKEND_ROOT = Path(__file__).resolve().parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select

from app.chat.messages import UIMessageIn
from app.chat.orchestrator import stream_chat_turn
from app.database.chats import create_thread
from app.database.models import Profile
from app.database.session import get_session_factory

# Client-brief-style prompts for quick manual checks.
SAMPLE_QUERIES: dict[str, str] = {
    "apple_mix": (
        "Across Apple's 2021–2025 10-Ks, how did the revenue mix between iPhone, "
        "Services, Mac, iPad, and Wearables change? Cite the filings."
    ),
    "nvidia_dc": (
        "How did NVIDIA describe demand drivers and supply constraints for Data Center "
        "from fiscal 2021 through fiscal 2025? One short paragraph with citations."
    ),
    "q10_refusal": (
        "Do the filings prove that generative AI improved margins for any of these "
        "companies? Only state what the corpus supports."
    ),
    "no_advice": (
        "Should I buy NVIDIA stock based on the latest 10-K? "
        "Answer only from the corpus and do not give investment advice."
    ),
}


async def run_one_turn(*, user_id: UUID, question: str) -> str:
    factory = get_session_factory()
    async with factory() as session:
        thread = await create_thread(session, user_id=user_id, title=question[:80])
        await session.commit()

        deltas: list[str] = []
        async for event in stream_chat_turn(
            session,
            user_id=user_id,
            thread_id=thread.id,
            user_text=question,
            ui_messages=[
                UIMessageIn(role="user", parts=[{"type": "text", "text": question}])
            ],
        ):
            if event.get("type") == "text-delta":
                deltas.append(str(event.get("delta", "")))

        answer = "".join(deltas)
        print(f"thread_id={thread.id}")
        return answer


async def main() -> None:
    # --- controls (edit these) ---
    query_key: str = "apple_mix"  # key from SAMPLE_QUERIES
    use_custom_question: bool = False
    custom_question: str = "What did Apple disclose about iPhone net sales in FY2025?"
    # -----------------------------

    if use_custom_question:
        question = custom_question.strip()
    else:
        if query_key not in SAMPLE_QUERIES:
            keys = ", ".join(sorted(SAMPLE_QUERIES))
            raise SystemExit(f"Unknown query_key {query_key!r}. Choose one of: {keys}")
        question = SAMPLE_QUERIES[query_key]

    factory = get_session_factory()
    async with factory() as session:
        user_id = await session.scalar(select(Profile.id).limit(1))
    if user_id is None:
        raise SystemExit("No profiles row — sign up once in the app so auth.users exists.")

    print(f"query_key={query_key if not use_custom_question else 'custom'}")
    print(f"question={question}\n")
    answer = await run_one_turn(user_id=user_id, question=question)
    print("--- answer ---")
    print(answer)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
