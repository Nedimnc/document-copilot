import os

import pytest
from pydantic import ValidationError

from app.config import Settings, apply_sdk_environment, get_settings


def test_settings_parses_required_values(valid_env):
    settings = Settings(_env_file=None)

    assert settings.supabase_url == "https://example.supabase.co"
    assert settings.supabase_anon_key == "anon-key"
    assert settings.supabase_service_role_key == "service-role-key"
    assert settings.database_url == "postgresql://user:pass@localhost:5432/app"
    assert settings.openai_api_key == "sk-test-key"
    assert settings.openai_embedding_model == "text-embedding-3-small"
    assert settings.openai_embedding_dimensions == 1536
    assert settings.allowed_origins == [
        "http://localhost:5173",
        "http://localhost:3000",
    ]
    assert settings.environment == "development"


def test_sqlalchemy_database_url_uses_psycopg_driver(valid_env):
    settings = Settings(_env_file=None)

    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")
    assert "postgresql+psycopg://user:pass@localhost:5432/app" == (
        settings.sqlalchemy_database_url
    )


def test_settings_requires_missing_values(monkeypatch):
    for key in (
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "OPENAI_EMBEDDING_MODEL",
        "OPENAI_EMBEDDING_DIMENSIONS",
        "ALLOWED_ORIGINS",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_rejects_empty_origins(valid_env, monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "  ,  ")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_rejects_non_positive_embedding_dimensions(valid_env, monkeypatch):
    monkeypatch.setenv("OPENAI_EMBEDDING_DIMENSIONS", "0")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_apply_sdk_environment_mirrors_openai_key(valid_env, monkeypatch):
    loaded = Settings(_env_file=None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    apply_sdk_environment(loaded)

    assert os.environ["OPENAI_API_KEY"] == "sk-test-key"


def test_get_settings_returns_cached_instance(valid_env):
    first = get_settings()
    second = get_settings()

    assert first is second
