from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.user import CurrentUser
from app.database.session import get_db_session
from app.main import create_app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
THREAD_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

CURRENT_USER = CurrentUser(
    id=USER_ID,
    email="analyst@driftwood.example",
    access_token="user-jwt",
)


def _thread(*, user_id: UUID = USER_ID, title: str | None = "Filing question"):
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return SimpleNamespace(
        id=THREAD_ID,
        user_id=user_id,
        title=title,
        created_at=now,
        updated_at=now,
    )


def _message(*, role: str, content: str):
    return SimpleNamespace(
        id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        role=role,
        content=content,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _client(user: CurrentUser = CURRENT_USER) -> TestClient:
    app = create_app()

    async def override_user() -> CurrentUser:
        return user

    async def override_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db_session] = override_db
    return TestClient(app)


def test_list_threads_requires_auth(valid_env):
    response = TestClient(create_app()).get("/chat/threads")

    assert response.status_code == 401


def test_list_and_create_threads(valid_env):
    thread = _thread()

    with (
        patch("app.api.chat.list_threads", AsyncMock(return_value=[thread])),
        patch("app.api.chat.create_thread", AsyncMock(return_value=thread)),
    ):
        client = _client()
        listed = client.get("/chat/threads")
        created = client.post("/chat/threads", json={"title": "Filing question"})

    assert listed.status_code == 200
    assert listed.json()[0]["id"] == str(THREAD_ID)
    assert created.status_code == 201
    assert created.json()["title"] == "Filing question"


def test_messages_404_when_thread_missing(valid_env):
    with patch("app.api.chat.get_thread_by_id", AsyncMock(return_value=None)):
        response = _client().get(f"/chat/threads/{THREAD_ID}/messages")

    assert response.status_code == 404
    assert response.json()["detail"] == "Thread not found"


def test_messages_403_when_thread_belongs_to_someone_else(valid_env):
    with patch(
        "app.api.chat.get_thread_by_id",
        AsyncMock(return_value=_thread(user_id=OTHER_USER_ID)),
    ):
        response = _client().get(f"/chat/threads/{THREAD_ID}/messages")

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this thread"


def test_list_messages_for_owner(valid_env):
    with (
        patch("app.api.chat.get_thread_by_id", AsyncMock(return_value=_thread())),
        patch(
            "app.api.chat.list_messages",
            AsyncMock(return_value=[_message(role="user", content="hello")]),
        ),
    ):
        response = _client().get(f"/chat/threads/{THREAD_ID}/messages")

    assert response.status_code == 200
    body = response.json()[0]
    assert body["role"] == "user"
    assert body["parts"] == [{"type": "text", "text": "hello"}]


def test_stream_403_for_other_users_thread(valid_env):
    with patch(
        "app.api.chat.get_thread_by_id",
        AsyncMock(return_value=_thread(user_id=OTHER_USER_ID)),
    ):
        response = _client().post(
            "/chat/stream",
            json={
                "id": str(THREAD_ID),
                "messages": [
                    {"id": "m1", "role": "user", "parts": [{"type": "text", "text": "hi"}]}
                ],
            },
        )

    assert response.status_code == 403


def test_stream_404_for_missing_thread(valid_env):
    with patch("app.api.chat.get_thread_by_id", AsyncMock(return_value=None)):
        response = _client().post(
            "/chat/stream",
            json={
                "threadId": str(THREAD_ID),
                "messages": [
                    {"id": "m1", "role": "user", "parts": [{"type": "text", "text": "hi"}]}
                ],
            },
        )

    assert response.status_code == 404


def test_stream_emits_ui_events_and_persists(valid_env):
    persist = AsyncMock()
    session_factory = MagicMock()

    with (
        patch("app.api.chat.get_thread_by_id", AsyncMock(return_value=_thread())),
        patch("app.api.chat.CHUNK_DELAY_SECONDS", 0),
        patch("app.api.chat.persist_stub_turn", persist),
        patch("app.api.chat.get_session_factory", return_value=session_factory),
    ):
        response = _client().post(
            "/chat/stream",
            json={
                "id": str(THREAD_ID),
                "messages": [
                    {
                        "id": "m1",
                        "role": "user",
                        "parts": [{"type": "text", "text": "What is a 10-K?"}],
                    }
                ],
            },
        )

    assert response.status_code == 200
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"type":"start"' in response.text
    assert 'data: {"type":"text-delta"' in response.text
    assert 'data: {"type":"finish"}' in response.text
    assert "data: [DONE]" in response.text
    persist.assert_awaited_once()
    assert persist.await_args.kwargs["user_text"] == "What is a 10-K?"
    assert persist.await_args.kwargs["thread_id"] == THREAD_ID
    session_factory.assert_not_called()
