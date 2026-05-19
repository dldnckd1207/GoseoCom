"""sfr105_seed_boards

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-27 00:00:01.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SYSTEM_USER = "USR_00000000"


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO cms_tn_board (
            id, board_code, board_name, board_desc, board_type,
            read_yn, guest_read_yn, write_yn, guest_write_yn,
            notice_yn, reply_yn, comment_yn, secret_yn, like_yn, category_yn,
            attach_yn, attach_ext, attach_size, attach_count, list_count,
            auto_reply_enabled, auto_reply_delay_min, pipeline_enabled,
            sort_order, use_yn,
            created_at, created_by, updated_at, updated_by, del_yn
        ) VALUES
        (
            'BRD_00000001', 'translation', '번역', '번역 관련 게시판입니다.', 'LIST',
            true, true, true, false,
            true, false, true, false, false, false,
            true, 'jpg,png,pdf', 10240, 5, 20,
            false, 5, false,
            0, true,
            NOW(), '{_SYSTEM_USER}', NOW(), '{_SYSTEM_USER}', false
        ),
        (
            'BRD_00000002', 'questions', '질문', '질문을 남겨주세요.', 'QNA',
            true, true, true, false,
            true, false, true, false, false, false,
            true, 'jpg,png,pdf', 10240, 5, 20,
            false, 5, false,
            1, true,
            NOW(), '{_SYSTEM_USER}', NOW(), '{_SYSTEM_USER}', false
        ),
        (
            'BRD_00000003', 'free', '자유', '자유롭게 글을 작성하세요.', 'LIST',
            true, true, true, false,
            true, false, true, false, false, false,
            true, 'jpg,png,pdf', 10240, 5, 20,
            false, 5, false,
            2, true,
            NOW(), '{_SYSTEM_USER}', NOW(), '{_SYSTEM_USER}', false
        )
        ON CONFLICT (id) DO NOTHING
    """)

    # ID 시퀀스를 seed 데이터 이후로 앞당김 (seq_brd는 3부터 시작)
    op.execute("SELECT setval('seq_brd', 3, true)")


def downgrade() -> None:
    op.execute(
        "DELETE FROM cms_tn_board WHERE id IN ('BRD_00000001', 'BRD_00000002', 'BRD_00000003')"
    )
    op.execute("SELECT setval('seq_brd', 1, false)")
