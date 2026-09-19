import pytest
from fastapi import HTTPException

from app.auth.tokens import extract_bearer_token


def test_extracts_bearer_token():
    assert extract_bearer_token("Bearer user-jwt") == "user-jwt"


def test_missing_authorization_is_401():
    for header in (None, "", "   "):
        with pytest.raises(HTTPException) as exc_info:
            extract_bearer_token(header)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Missing authorization token"


def test_malformed_authorization_is_401():
    for header in ("Bearer", "Bearer   ", "Token user-jwt", "user-jwt"):
        with pytest.raises(HTTPException) as exc_info:
            extract_bearer_token(header)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authorization header"
