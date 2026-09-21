"""Single source of truth for backend environment configuration.

Import `settings` from this module. Do not call `os.getenv` or `load_dotenv`
elsewhere. Missing required values fail when Settings is constructed.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Resolve .env from this file so loading does not depend on the process cwd.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _parse_origins(value: object) -> list[str]:
    if isinstance(value, str):
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    elif isinstance(value, list):
        origins = [str(item).strip() for item in value if str(item).strip()]
    else:
        raise TypeError("ALLOWED_ORIGINS must be a comma-separated list of origins")
    if not origins:
        raise ValueError("ALLOWED_ORIGINS must include at least one origin")
    return origins


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Direct/session URL only. Alembic cannot use the transaction pooler.
    database_url: str

    openai_api_key: str
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str
    openai_embedding_dimensions: int

    allowed_origins: Annotated[list[str], NoDecode] = Field(
        validation_alias="ALLOWED_ORIGINS"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> list[str]:
        return _parse_origins(value)

    @field_validator("openai_embedding_dimensions")
    @classmethod
    def dimensions_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("OPENAI_EMBEDDING_DIMENSIONS must be a positive integer")
        return value

    @property
    def sqlalchemy_database_url(self) -> str:
        # SQLAlchemy needs the psycopg3 driver name in the scheme.
        if self.database_url.startswith("postgresql://"):
            return "postgresql+psycopg://" + self.database_url.removeprefix(
                "postgresql://"
            )
        return self.database_url


def apply_sdk_environment(settings: Settings) -> None:
    # OpenAI's SDK reads OPENAI_API_KEY from the process env, not from Settings.
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key


@lru_cache
def get_settings() -> Settings:
    loaded = Settings()
    apply_sdk_environment(loaded)
    return loaded


class _SettingsProxy:
    """Delay env loading until first attribute access.

    Lets tests import this module and construct Settings() with a patched env
    without requiring a real .env at collection time.
    """

    def __getattr__(self, name: str) -> object:
        return getattr(get_settings(), name)


settings = _SettingsProxy()
