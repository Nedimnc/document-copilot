import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.database.supabase import create_service_role_client, create_user_client


def test_user_client_uses_anon_key_and_caller_jwt(valid_env):
    mock_create = AsyncMock(return_value=object())

    with patch("app.database.supabase.create_async_client", mock_create):
        asyncio.run(create_user_client("user-jwt"))

    url, key = mock_create.await_args.args
    options = mock_create.await_args.kwargs["options"]
    assert url == "https://example.supabase.co"
    assert key == "anon-key"
    assert options.headers["Authorization"] == "Bearer user-jwt"
    assert options.persist_session is False
    assert options.auto_refresh_token is False


def test_user_client_strips_bearer_prefix(valid_env):
    mock_create = AsyncMock(return_value=object())

    with patch("app.database.supabase.create_async_client", mock_create):
        asyncio.run(create_user_client("Bearer user-jwt"))

    options = mock_create.await_args.kwargs["options"]
    assert options.headers["Authorization"] == "Bearer user-jwt"


def test_user_client_rejects_empty_token(valid_env):
    for token in ("", "   ", "Bearer", "   Bearer   "):
        with pytest.raises(ValueError, match="access_token is required"):
            asyncio.run(create_user_client(token))


def test_service_role_client_uses_service_key_not_user_jwt(valid_env):
    mock_create = AsyncMock(return_value=object())

    with patch("app.database.supabase.create_async_client", mock_create):
        asyncio.run(create_service_role_client())

    url, key = mock_create.await_args.args
    options = mock_create.await_args.kwargs["options"]
    assert url == "https://example.supabase.co"
    assert key == "service-role-key"
    assert "Authorization" not in options.headers
    assert options.persist_session is False
    assert options.auto_refresh_token is False
