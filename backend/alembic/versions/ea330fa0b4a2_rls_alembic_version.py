"""Enable RLS on alembic_version.

Alembic creates this table without row security, which Supabase flags as
unrestricted. No policies on purpose: authenticated/anon get nothing;
the postgres role used by migrations still bypasses RLS.

Revision ID: ea330fa0b4a2
Revises: 5eb9edb8a8c2
Create Date: 2026-09-17
"""

from alembic import op

revision: str = "ea330fa0b4a2"
down_revision: str | None = "5eb9edb8a8c2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE alembic_version FROM anon, authenticated")


def downgrade() -> None:
    op.execute("ALTER TABLE alembic_version DISABLE ROW LEVEL SECURITY")
