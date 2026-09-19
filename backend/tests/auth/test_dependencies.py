import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from supabase import AuthApiError, AuthRetryableError

from app.auth.dependencies import verify_access_token

USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def _client_with_user(user: object | None = None, error: Exception | None = None):
    auth = AsyncMock()
    if error is not None:
        auth.get_user.side_effect = error
    else:
        auth.get_user.return_value = SimpleNamespace(user=user)
    return SimpleNamespace(auth=auth)


def test_verify_access_token_returns_current_user(valid_env):
    user = SimpleNamespace(id=str(USER_ID), email="analyst@driftwood.example")
    mock_create = AsyncMock(return_value=_client_with_user(user))

    with patch("app.auth.dependencies.create_user_client", mock_create):
        current_user = asyncio.run(verify_access_token("user-jwt"))

    assert current_user.id == USER_ID
    assert current_user.email == "analyst@driftwood.example"
    assert current_user.access_token == "user-jwt"
    mock_create.return_value.auth.get_user.assert_awaited_once_with(jwt="user-jwt")


def test_verify_access_token_rejects_invalid_token(valid_env):
    mock_create = AsyncMock(
        return_value=_client_with_user(
            error=AuthApiError("invalid", 401, None),
        )
    )

    with (
        patch("app.auth.dependencies.create_user_client", mock_create),
        pytest.raises(HTTPException) as exc_info,
    ):
        asyncio.run(verify_access_token("bad-jwt"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"


def test_verify_access_token_maps_retryable_errors_to_502(valid_env):
    mock_create = AsyncMock(
        return_value=_client_with_user(error=AuthRetryableError("timeout", 503))
    )

    with (
        patch("app.auth.dependencies.create_user_client", mock_create),
        pytest.raises(HTTPException) as exc_info,
    ):
        asyncio.run(verify_access_token("user-jwt"))

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Auth provider unavailable"


def test_verify_access_token_requires_email(valid_env):
    user = SimpleNamespace(id=str(USER_ID), email=None)
    mock_create = AsyncMock(return_value=_client_with_user(user))

    with (
        patch("app.auth.dependencies.create_user_client", mock_create),
        pytest.raises(HTTPException) as exc_info,
    ):
        asyncio.run(verify_access_token("user-jwt"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authenticated user is missing an email"
