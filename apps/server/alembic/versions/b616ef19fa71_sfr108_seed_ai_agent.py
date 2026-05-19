"""sfr108_seed_ai_agent

Revision ID: b616ef19fa71
Revises: 1227cc541196
Create Date: 2026-04-15 17:08:04.240538

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b616ef19fa71"
down_revision: str | None = "1227cc541196"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    now = "NOW()"
    op.execute(f"""
        INSERT INTO com_tn_user (
            id, email, name, profile_image_url,
            user_level, use_yn, block_yn,
            joined_at,
            created_at, created_by,
            updated_at, updated_by,
            del_yn
        ) VALUES (
            'USR_00000000',
            'ai@haedok.internal',
            '해독이',
            NULL,
            0,
            true,
            false,
            {now},
            {now}, 'USR_00000000',
            {now}, 'USR_00000000',
            false
        )
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM com_tn_user WHERE id = 'USR_00000000'")
