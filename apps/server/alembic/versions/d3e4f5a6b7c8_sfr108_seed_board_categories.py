"""sfr108_seed_board_categories

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-05-16 00:00:01.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SYSTEM_USER = "USR_00000000"
_CATEGORIES = [("선사", 0), ("삼국", 1), ("고려", 2), ("조선", 3)]
_BOARD_CODES = ["translation", "questions", "free"]


def upgrade() -> None:
    idx = 1
    for board_code in _BOARD_CODES:
        for category_name, sort_order in _CATEGORIES:
            cat_id = f"BCAT_{idx:08d}"
            op.execute(f"""
                INSERT INTO cms_tn_board_category
                    (id, board_id, category_name, sort_order, use_yn,
                     created_at, created_by, updated_at, updated_by, del_yn)
                SELECT
                    '{cat_id}',
                    id,
                    '{category_name}',
                    {sort_order},
                    true,
                    NOW(), '{_SYSTEM_USER}', NOW(), '{_SYSTEM_USER}', false
                FROM cms_tn_board
                WHERE board_code = '{board_code}'
                ON CONFLICT (id) DO NOTHING
            """)
            idx += 1

    op.execute("""
        SELECT setval('seq_bcat', GREATEST((SELECT last_value FROM seq_bcat), 12), true)
    """)


def downgrade() -> None:
    category_names = ", ".join(f"'{c}'" for c, _ in _CATEGORIES)
    board_codes = ", ".join(f"'{b}'" for b in _BOARD_CODES)
    # created_by 조건 추가 — 동일 이름을 수동 생성한 카테고리는 보존
    op.execute(f"""
        DELETE FROM cms_tn_board_category
        WHERE board_id IN (
            SELECT id FROM cms_tn_board WHERE board_code IN ({board_codes})
        )
        AND category_name IN ({category_names})
        AND created_by = '{_SYSTEM_USER}'
    """)
    # 빈 테이블이면 is_called=false(nextval=1), 데이터가 있으면 is_called=true(nextval=max+1)
    op.execute("""
        SELECT setval(
            'seq_bcat',
            GREATEST(
                COALESCE(
                    (SELECT MAX(CAST(SPLIT_PART(id, '_', 2) AS INTEGER))
                     FROM cms_tn_board_category),
                    0
                ),
                1
            ),
            (SELECT COUNT(*) > 0 FROM cms_tn_board_category)
        )
    """)
