"""add_id_sequences

Revision ID: 8b16bfd02543
Revises: b616ef19fa71
Create Date: 2026-04-15 18:24:29.923134

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "8b16bfd02543"
down_revision: str | None = "b616ef19fa71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
