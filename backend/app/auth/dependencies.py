from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from supabase import AsyncClient, AuthApiError, AuthRetryableError

from app.auth.tokens import extract_bearer_token
from app.auth.user import CurrentUser
from app.database.supabase import create_user_client


async def get_access_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    return extract_bearer_token(authorization)


async def verify_access_token(access_token: str) -> CurrentUser:
    client = await create_user_client(access_token)
    try:
        response = await client.auth.get_user(jwt=access_token)
    except AuthRetryableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Auth provider unavailable",
        ) from exc
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = getattr(response, "user", None)
    if user is None or not getattr(user, "id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = getattr(user, "email", None)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user is missing an email",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(str(user.id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser(id=user_id, email=email, access_token=access_token)


async def get_current_user(
    access_token: Annotated[str, Depends(get_access_token)],
) -> CurrentUser:
    return await verify_access_token(access_token)


async def get_user_client(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncClient:
    return await create_user_client(current_user.access_token)
