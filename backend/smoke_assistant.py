"""Manual smoke tests for grounded assistant turns (retrieval + LLM + validation).

From backend/:

    uv run python smoke_assistant.py
    uv run python smoke_assistant.py --brief q01
    uv run python smoke_assistant.py --brief-all
"""

from __future__ import annotations

import argparse
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

# Client-brief example questions (docs/client-brief.md)
BRIEF_QUESTIONS: dict[str, str] = {
    "q01": (
        "Across Apple's 2021–2025 10-Ks, how did the revenue mix between iPhone, "
        "Services, Mac, iPad, and Wearables change, and which category appears to "
        "have contributed most to any mix shift?"
    ),
    "q02": (
        "For Amazon, compare AWS operating income and margin against North America "
        "and International from 2021–2025. In which years did AWS appear to fund "
        "losses or weaker profitability elsewhere?"
    ),
    "q03": (
        "How did NVIDIA describe demand drivers, customer concentration, and supply "
        "constraints for its Data Center business from fiscal 2021 through fiscal 2025?"
    ),
    "q04": (
        "Across Microsoft's 2021–2025 filings, what changed in the way the company "
        "describes Azure, AI infrastructure, and cloud capacity constraints?"
    ),
    "q05": (
        "For Alphabet, how did Google Search, YouTube ads, Google Network, "
        "subscriptions/platforms/devices, and Google Cloud revenue trends differ "
        "across the available 10-Ks?"
    ),
    "q06": (
        "Which of the five companies added, removed, or materially changed risk-factor "
        "language related to AI, cloud infrastructure, export controls, supply chain "
        "concentration, or regulation between 2021 and 2025?"
    ),
    "q07": (
        "For Apple and NVIDIA, what do the filings say about supplier concentration "
        "or dependence on third-party manufacturing, and did the wording become more "
        "or less urgent over time?"
    ),
    "q08": (
        "Compare capital expenditures and purchase commitments for Microsoft, Alphabet, "
        "Amazon, and NVIDIA. What do the filings imply about the scale and timing of "
        "AI/cloud infrastructure investment?"
    ),
    "q09": (
        "For each company, summarize the most important geographic revenue exposures "
        "disclosed in the latest 10-K, then identify any year-over-year changes that "
        "could matter to an analyst."
    ),
    "q10_refusal": (
        "Do the filings prove that generative AI improved margins for any of these "
        "companies? What evidence exists in the corpus, and where should you refuse "
        "to infer beyond the filings?"
    ),
}

SAMPLE_QUERIES: dict[str, str] = {
    "apple_mix": BRIEF_QUESTIONS["q01"],
    "nvidia_dc": BRIEF_QUESTIONS["q03"],
    "q10_refusal": BRIEF_QUESTIONS["q10_refusal"],
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


async def _resolve_user_id() -> UUID:
    factory = get_session_factory()
    async with factory() as session:
        user_id = await session.scalar(select(Profile.id).limit(1))
    if user_id is None:
        raise SystemExit("No profiles row — sign up once in the app so auth.users exists.")
    return user_id


async def run_brief_all(user_id: UUID) -> None:
    for key in sorted(BRIEF_QUESTIONS):
        question = BRIEF_QUESTIONS[key]
        print(f"\n========== {key} ==========")
        print(f"question={question}\n")
        answer = await run_one_turn(user_id=user_id, question=question)
        print("--- answer ---")
        print(answer)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--brief",
        metavar="ID",
        help=f"Run one brief question ({', '.join(sorted(BRIEF_QUESTIONS))})",
    )
    parser.add_argument(
        "--brief-all",
        action="store_true",
        help="Run all ten client-brief questions (OpenAI cost applies)",
    )
    parser.add_argument(
        "--query-key",
        default="apple_mix",
        help=f"Legacy preset key when no --brief flags ({', '.join(sorted(SAMPLE_QUERIES))})",
    )
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()
    user_id = await _resolve_user_id()

    if args.brief_all:
        await run_brief_all(user_id)
        return

    if args.brief:
        if args.brief not in BRIEF_QUESTIONS:
            keys = ", ".join(sorted(BRIEF_QUESTIONS))
            raise SystemExit(f"Unknown --brief {args.brief!r}. Choose: {keys}")
        question = BRIEF_QUESTIONS[args.brief]
        print(f"brief={args.brief}")
    else:
        if args.query_key not in SAMPLE_QUERIES:
            keys = ", ".join(sorted(SAMPLE_QUERIES))
            raise SystemExit(f"Unknown query_key {args.query_key!r}. Choose: {keys}")
        question = SAMPLE_QUERIES[args.query_key]
        print(f"query_key={args.query_key}")

    print(f"question={question}\n")
    answer = await run_one_turn(user_id=user_id, question=question)
    print("--- answer ---")
    print(answer)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
