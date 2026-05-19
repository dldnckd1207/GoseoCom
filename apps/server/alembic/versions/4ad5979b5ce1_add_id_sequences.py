"""add_id_sequences

Revision ID: 4ad5979b5ce1
Revises: 8b16bfd02543
Create Date: 2026-04-15 18:30:29.860924

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4ad5979b5ce1"
down_revision: str | None = "8b16bfd02543"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SEQUENCES = [
    "seq_usr",  # USR_
    "seq_oauth",  # OAUTH_
    "seq_utkn",  # UTKN_
    "seq_file",  # FILE_
    "seq_fmap",  # FMAP_
    "seq_brd",  # BRD_
    "seq_post",  # POST_
    "seq_cmt",  # CMT_
    "seq_book",  # BOOK_
    "seq_bpage",  # BPAGE_
]


def upgrade() -> None:
    for seq in SEQUENCES:
        op.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1 INCREMENT 1")


def downgrade() -> None:
    for seq in SEQUENCES:
        op.execute(f"DROP SEQUENCE IF EXISTS {seq}")
