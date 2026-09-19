"""Supabase client construction.

User-scoped clients send the caller's JWT so Postgres RLS sees auth.uid().
The service-role client bypasses RLS and is only for privileged backend writes.
"""

from supabase import AsyncClient, AsyncClientOptions, create_async_client

from app.config import get_settings


def _normalize_access_token(access_token: str) -> str:
    token = access_token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    elif token.lower() == "bearer":
        token = ""
    if not token:
        raise ValueError("access_token is required")
    return token


def _server_options(**headers: str) -> AsyncClientOptions:
    # This process is not a browser: do not persist or refresh sessions.
    return AsyncClientOptions(
        persist_session=False,
        auto_refresh_token=False,
        headers=dict(headers),
    )


async def create_user_client(access_token: str) -> AsyncClient:
    token = _normalize_access_token(access_token)
    settings = get_settings()
    return await create_async_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=_server_options(Authorization=f"Bearer {token}"),
    )


async def create_service_role_client() -> AsyncClient:
    settings = get_settings()
    return await create_async_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=_server_options(),
    )
