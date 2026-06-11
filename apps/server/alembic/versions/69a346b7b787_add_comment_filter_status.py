"""add_comment_filter_status

Revision ID: 69a346b7b787
Revises: fe2bb45ca6a2
Create Date: 2026-06-09 23:39:22.797792

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "69a346b7b787"
down_revision: str | None = "fe2bb45ca6a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cms_tn_comment",
        sa.Column("filter_status", sa.String(length=20), server_default="PENDING", nullable=False),
    )
    # 기존 is_filtered=true 행은 FLAGGED로 초기화
    op.execute("UPDATE cms_tn_comment SET filter_status = 'FLAGGED' WHERE is_filtered = true")
    op.create_index("ix_comment_filter_status", "cms_tn_comment", ["filter_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_comment_filter_status", table_name="cms_tn_comment")
    op.drop_column("cms_tn_comment", "filter_status")
