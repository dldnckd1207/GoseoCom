"""sfr205_post_book_id

Revision ID: fe2bb45ca6a2
Revises: d760d31a9579
Create Date: 2026-06-06 17:27:41.862603

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fe2bb45ca6a2"
down_revision: str | None = "d760d31a9579"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("cms_tn_post", sa.Column("book_id", sa.String(length=20), nullable=True))
    op.create_index("ix_post_book", "cms_tn_post", ["book_id"], unique=False)
    op.create_foreign_key(
        "fk_post_book_id", "cms_tn_post", "ai_tn_book", ["book_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_post_book_id", "cms_tn_post", type_="foreignkey")
    op.drop_index("ix_post_book", table_name="cms_tn_post")
    op.drop_column("cms_tn_post", "book_id")
