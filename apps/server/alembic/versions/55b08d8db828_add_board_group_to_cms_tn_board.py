"""add_board_group_to_cms_tn_board

Revision ID: 55b08d8db828
Revises: b2c3d4e5f6a7
Create Date: 2026-05-04 13:38:44.982727

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "55b08d8db828"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "cms_tn_board",
        sa.Column("board_group", sa.String(50), nullable=True),
    )
    op.create_index("ix_board_board_group", "cms_tn_board", ["board_group"])
    op.execute(
        "UPDATE cms_tn_board SET board_group = 'community' "
        "WHERE board_code IN ('translation', 'questions', 'free')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_board_board_group")
    op.drop_column("cms_tn_board", "board_group")
