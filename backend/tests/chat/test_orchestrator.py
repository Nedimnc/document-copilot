import asyncio
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.chat.grounding import GroundedTurnContext
from app.chat.messages import UIMessageIn
from app.chat.orchestrator import stream_chat_turn
from app.grounding.refusal import GROUNDING_VALIDATION_FAILURE_MESSAGE
from app.retrieval.types import RetrievedPassage

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
THREAD_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _passage(label: int = 1) -> RetrievedPassage:
    return RetrievedPassage(
        chunk_id=UUID(f"00000000-0000-4000-8000-{label:012d}"),
        document_id=UUID("22222222-2222-2222-2222-222222222222"),
        chunk_index=0,
        content="Net sales were $100B [detail].",
        page=1,
        section="Item 7",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2024, 11, 1),
        fiscal_year=2024,
        source_url="https://example.com",
        rrf_score=0.2,
        citation_label=label,
    )


def _collect_events(coro):
    return asyncio.run(_collect_async(coro))


async def _collect_async(coro):
    events = []
    async for event in coro:
        events.append(event)
    return events


def test_refusal_turn_streams_and_persists_without_llm():
    session = AsyncMock()
    session.commit = AsyncMock()
    turn = GroundedTurnContext(
        query="unknown",
        passages=[],
        system_addendum="no passages",
        has_citable_evidence=False,
        refusal_message="No evidence in corpus.",
    )

    with (
        patch("app.chat.orchestrator.get_thread", AsyncMock(return_value=MagicMock(title=None))),
        patch("app.chat.orchestrator.create_message", AsyncMock()),
        patch("app.chat.orchestrator.prepare_grounded_turn", AsyncMock(return_value=turn)),
        patch("app.chat.orchestrator.build_document_agent") as build_agent,
    ):
        events = _collect_events(
            stream_chat_turn(
                session,
                user_id=USER_ID,
                thread_id=THREAD_ID,
                user_text="What is revenue?",
                ui_messages=[
                    UIMessageIn(
                        role="user",
                        parts=[{"type": "text", "text": "What is revenue?"}],
                    )
                ],
            )
        )

    build_agent.assert_not_called()
    assert any(event.get("type") == "text-delta" for event in events)
    assert session.commit.await_count >= 2


def test_grounded_turn_validates_and_persists_citations():
    session = AsyncMock()
    session.commit = AsyncMock()
    turn = GroundedTurnContext(
        query="revenue",
        passages=[_passage(1)],
        system_addendum="[1] AAPL ...",
        has_citable_evidence=True,
        refusal_message=None,
    )

    async def fake_deltas():
        yield "Revenue was $100B [1]."

    class FakeStream:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        def stream_text(self, *, delta: bool, debounce_by):
            assert delta is True

            async def _gen():
                async for item in fake_deltas():
                    yield item

            return _gen()

        @property
        def usage(self):
            return MagicMock(input_tokens=10, output_tokens=20)

    agent = MagicMock()
    agent.run_stream.return_value = FakeStream()

    create_message = AsyncMock(
        side_effect=[
            MagicMock(id=UUID("33333333-3333-3333-3333-333333333333")),
            MagicMock(id=UUID("44444444-4444-4444-4444-444444444444")),
        ]
    )

    with (
        patch("app.chat.orchestrator.get_thread", AsyncMock(return_value=MagicMock(title="t"))),
        patch("app.chat.orchestrator.create_message", create_message),
        patch("app.chat.orchestrator.create_citations", AsyncMock()) as create_citations,
        patch("app.chat.orchestrator.prepare_grounded_turn", AsyncMock(return_value=turn)),
    ):
        _collect_events(
            stream_chat_turn(
                session,
                user_id=USER_ID,
                thread_id=THREAD_ID,
                user_text="revenue?",
                ui_messages=[
                    UIMessageIn(role="user", parts=[{"type": "text", "text": "revenue?"}])
                ],
                agent=agent,
            )
        )

    create_citations.assert_awaited_once()


def test_grounding_failure_streams_controlled_refusal_not_raw_answer():
    session = AsyncMock()
    session.commit = AsyncMock()
    turn = GroundedTurnContext(
        query="revenue",
        passages=[_passage(1)],
        system_addendum="[1] AAPL ...",
        has_citable_evidence=True,
        refusal_message=None,
    )

    async def fake_deltas():
        yield (
            "Net sales reached $383 billion in fiscal 2024 with no citation markers "
            "anywhere in this answer."
        )

    class FakeStream:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        def stream_text(self, *, delta: bool, debounce_by):
            async def _gen():
                async for item in fake_deltas():
                    yield item

            return _gen()

        @property
        def usage(self):
            return MagicMock(input_tokens=10, output_tokens=20)

    agent = MagicMock()
    agent.run_stream.return_value = FakeStream()

    create_message = AsyncMock(
        side_effect=[
            MagicMock(id=UUID("33333333-3333-3333-3333-333333333333")),
            MagicMock(id=UUID("44444444-4444-4444-4444-444444444444")),
        ]
    )

    with (
        patch("app.chat.orchestrator.get_thread", AsyncMock(return_value=MagicMock(title="t"))),
        patch("app.chat.orchestrator.create_message", create_message),
        patch("app.chat.orchestrator.create_citations", AsyncMock()) as create_citations,
        patch("app.chat.orchestrator.prepare_grounded_turn", AsyncMock(return_value=turn)),
    ):
        events = _collect_events(
            stream_chat_turn(
                session,
                user_id=USER_ID,
                thread_id=THREAD_ID,
                user_text="revenue?",
                ui_messages=[
                    UIMessageIn(role="user", parts=[{"type": "text", "text": "revenue?"}])
                ],
                agent=agent,
            )
        )

    deltas = [
        event.get("delta", "")
        for event in events
        if event.get("type") == "text-delta"
    ]
    streamed = "".join(deltas)
    assert GROUNDING_VALIDATION_FAILURE_MESSAGE in streamed
    assert "$383 billion" not in streamed
    create_citations.assert_not_awaited()
