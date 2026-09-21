from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.user import CurrentUser
from app.database.chats import CitationRecord
from app.database.session import get_db_session
from app.main import create_app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
THREAD_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
MESSAGE_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

CURRENT_USER = CurrentUser(
    id=USER_ID,
    email="analyst@driftwood.example",
    access_token="user-jwt",
)


def _client() -> TestClient:
    app = create_app()

    async def override_user() -> CurrentUser:
        return CURRENT_USER

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db_session] = override_db
    return TestClient(app)


def test_messages_include_citation_payload(valid_env):
    thread = SimpleNamespace(
        id=THREAD_ID,
        user_id=USER_ID,
        title="Q",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    message = SimpleNamespace(
        id=MESSAGE_ID,
        role="assistant",
        content="Revenue rose [1].",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    record = CitationRecord(
        id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        message_id=MESSAGE_ID,
        chunk_id=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        document_id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
        sort_order=0,
        excerpt="iPhone net sales increased.",
        page=42,
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        fiscal_year=2025,
        filing_date=date(2025, 10, 31),
        source_url="https://example.com/aapl",
        section="Item 7",
    )

    with (
        patch("app.api.chat.get_thread_by_id", AsyncMock(return_value=thread)),
        patch("app.api.chat.list_messages", AsyncMock(return_value=[message])),
        patch(
            "app.api.chat.list_citations_for_thread",
            AsyncMock(return_value={MESSAGE_ID: [record]}),
        ),
    ):
        response = _client().get(f"/chat/threads/{THREAD_ID}/messages")

    assert response.status_code == 200
    body = response.json()[0]
    assert body["citations"][0]["ticker"] == "AAPL"
    assert body["citations"][0]["excerpt"] == "iPhone net sales increased."
    assert body["citations"][0]["page"] == 42
