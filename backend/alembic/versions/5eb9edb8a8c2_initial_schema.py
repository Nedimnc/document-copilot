"""initial schema

Revision ID: 5eb9edb8a8c2
Revises:
Create Date: 2026-09-17

"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "5eb9edb8a8c2"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_profiles"),
    )
    op.create_foreign_key(
        "fk_profiles_id_users",
        "profiles",
        "users",
        ["id"],
        ["id"],
        referent_schema="auth",
        ondelete="CASCADE",
    )

    op.create_table(
        "chat_threads",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["profiles.id"],
            name="fk_chat_threads_user_id_profiles",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chat_threads"),
    )
    op.create_index(
        "ix_chat_threads_user_id_updated_at",
        "chat_threads",
        ["user_id", "updated_at"],
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("thread_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["chat_threads.id"],
            name="fk_chat_messages_thread_id_chat_threads",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chat_messages"),
    )
    op.create_index(
        "ix_chat_messages_thread_id_created_at",
        "chat_messages",
        ["thread_id", "created_at"],
    )

    op.create_table(
        "source_documents",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("cik", sa.String(), nullable=False),
        sa.Column("filing_type", sa.String(), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("accession_number", sa.String(), nullable=False),
        sa.Column("primary_document", sa.String(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column(
            "markdown_content",
            sa.Text(),
            server_default=sa.text("''"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_documents"),
        sa.UniqueConstraint("accession_number", name="uq_source_documents_accession_number"),
    )
    op.create_index(
        "ix_source_documents_ticker_filing_date",
        "source_documents",
        ["ticker", "filing_date"],
    )
    op.create_index(
        "ix_source_documents_filing_type_fiscal_year",
        "source_documents",
        ["filing_type", "fiscal_year"],
    )

    op.create_table(
        "document_chunks",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english'::regconfig, content)", persisted=True),
        ),
        sa.Column(
            "chunk_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["source_documents.id"],
            name="fk_document_chunks_document_id_source_documents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document_chunks"),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name="uq_document_chunks_document_id"
        ),
    )
    op.execute(
        "CREATE INDEX document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX document_chunks_search_vector_gin "
        "ON document_chunks USING gin (search_vector)"
    )
    op.execute(
        "CREATE INDEX document_chunks_chunk_metadata_gin "
        "ON document_chunks USING gin (chunk_metadata)"
    )

    op.create_table(
        "message_citations",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["chat_messages.id"],
            name="fk_message_citations_message_id_chat_messages",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["document_chunks.id"],
            name="fk_message_citations_chunk_id_document_chunks",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["source_documents.id"],
            name="fk_message_citations_document_id_source_documents",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_message_citations"),
    )
    op.create_index(
        "ix_message_citations_message_id_sort_order",
        "message_citations",
        ["message_id", "sort_order"],
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER set_profiles_updated_at
        BEFORE UPDATE ON profiles
        FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )
    op.execute(
        """
        CREATE TRIGGER set_chat_threads_updated_at
        BEFORE UPDATE ON chat_threads
        FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )
    op.execute(
        """
        CREATE TRIGGER set_source_documents_updated_at
        BEFORE UPDATE ON source_documents
        FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS trigger
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $$
        BEGIN
          INSERT INTO public.profiles (id, email)
          VALUES (NEW.id, NEW.email);
          RETURN NEW;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW EXECUTE FUNCTION public.handle_new_user()
        """
    )

    for table in (
        "profiles",
        "chat_threads",
        "chat_messages",
        "source_documents",
        "document_chunks",
        "message_citations",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY profiles_select_own ON profiles
        FOR SELECT TO authenticated
        USING (id = auth.uid())
        """
    )
    op.execute(
        """
        CREATE POLICY profiles_update_own ON profiles
        FOR UPDATE TO authenticated
        USING (id = auth.uid())
        WITH CHECK (id = auth.uid())
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_all_own ON chat_threads
        FOR ALL TO authenticated
        USING (user_id = auth.uid())
        WITH CHECK (user_id = auth.uid())
        """
    )
    op.execute(
        """
        CREATE POLICY chat_messages_all_own ON chat_messages
        FOR ALL TO authenticated
        USING (
          EXISTS (
            SELECT 1 FROM chat_threads
            WHERE chat_threads.id = chat_messages.thread_id
              AND chat_threads.user_id = auth.uid()
          )
        )
        WITH CHECK (
          EXISTS (
            SELECT 1 FROM chat_threads
            WHERE chat_threads.id = chat_messages.thread_id
              AND chat_threads.user_id = auth.uid()
          )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY message_citations_all_own ON message_citations
        FOR ALL TO authenticated
        USING (
          EXISTS (
            SELECT 1 FROM chat_messages
            JOIN chat_threads ON chat_threads.id = chat_messages.thread_id
            WHERE chat_messages.id = message_citations.message_id
              AND chat_threads.user_id = auth.uid()
          )
        )
        WITH CHECK (
          EXISTS (
            SELECT 1 FROM chat_messages
            JOIN chat_threads ON chat_threads.id = chat_messages.thread_id
            WHERE chat_messages.id = message_citations.message_id
              AND chat_threads.user_id = auth.uid()
          )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY source_documents_select_authenticated ON source_documents
        FOR SELECT TO authenticated
        USING (true)
        """
    )
    op.execute(
        """
        CREATE POLICY document_chunks_select_authenticated ON document_chunks
        FOR SELECT TO authenticated
        USING (true)
        """
    )

    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON profiles, chat_threads, chat_messages, message_citations
        TO authenticated
        """
    )
    op.execute(
        "GRANT SELECT ON source_documents, document_chunks TO authenticated"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user()")
    op.execute("DROP TRIGGER IF EXISTS set_source_documents_updated_at ON source_documents")
    op.execute("DROP TRIGGER IF EXISTS set_chat_threads_updated_at ON chat_threads")
    op.execute("DROP TRIGGER IF EXISTS set_profiles_updated_at ON profiles")
    op.execute("DROP FUNCTION IF EXISTS public.set_updated_at()")

    op.drop_table("message_citations")
    op.drop_table("document_chunks")
    op.drop_table("source_documents")
    op.drop_table("chat_messages")
    op.drop_table("chat_threads")
    op.drop_table("profiles")
