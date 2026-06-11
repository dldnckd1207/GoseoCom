"""sfr206_book_title_gin_index

Revision ID: 31233b1255cb
Revises: 57a14d596e9a
Create Date: 2026-05-26 15:53:26.785580

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31233b1255cb"
down_revision: str | None = "57a14d596e9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_tn_book_title_gin "
        "ON ai_tn_book USING gin (title gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ai_tn_book_title_gin")
