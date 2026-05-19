"""sfr108_enable_category_yn

Revision ID: c2d3e4f5a6b7
Revises: d80be6b751d2
Create Date: 2026-05-16 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "d80be6b751d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        UPDATE cms_tn_board
        SET category_yn = true
        WHERE board_code IN ('translation', 'questions', 'free')
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE cms_tn_board
        SET category_yn = false
        WHERE board_code IN ('translation', 'questions', 'free')
    """)
