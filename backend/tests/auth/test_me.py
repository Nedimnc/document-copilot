from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth.user import CurrentUser

USER_ID = UUID("11111111-1111-1111-1111-111111111111")


def test_me_requires_bearer_token(valid_env):
    from app.main import create_app

    client = TestClient(create_app())
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization token"


def test_me_returns_current_user(valid_env):
    from app.main import create_app

    current_user = CurrentUser(
        id=USER_ID,
        email="analyst@driftwood.example",
        access_token="user-jwt",
    )

    with patch(
        "app.auth.dependencies.verify_access_token",
        new=AsyncMock(return_value=current_user),
    ):
        client = TestClient(create_app())
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer user-jwt"}
        )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(USER_ID),
        "email": "analyst@driftwood.example",
    }
