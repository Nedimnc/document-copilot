from logging.config import fileConfig
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config import get_settings
from app.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Owned in the initial migration, not in SQLAlchemy models. Keep autogenerate
# from trying to drop them.
MANAGED_OUTSIDE_ORM = {
    "fk_profiles_id_users",
    "document_chunks_embedding_hnsw",
    "document_chunks_search_vector_gin",
    "document_chunks_chunk_metadata_gin",
}


def get_database_url() -> str:
    # ConfigParser treats % as interpolation, so escape passwords that contain it.
    return get_settings().sqlalchemy_database_url.replace("%", "%%")


def include_object(
    object_: object,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: object,
) -> bool:
    return name not in MANAGED_OUTSIDE_ORM


def render_item(type_: str, obj: object, autogen_context: Any) -> str | bool:
    if type_ == "type" and isinstance(obj, Vector):
        autogen_context.imports.add("from pgvector.sqlalchemy import Vector")
        return f"Vector({obj.dim})"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
