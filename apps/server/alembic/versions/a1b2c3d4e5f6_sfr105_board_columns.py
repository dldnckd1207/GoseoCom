"""sfr105_board_columns

Revision ID: a1b2c3d4e5f6
Revises: 4ad5979b5ce1
Create Date: 2026-04-27 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "4ad5979b5ce1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # cms_tn_board — 권한 컬럼 추가
    op.add_column(
        "cms_tn_board",
        sa.Column("read_yn", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column(
        "cms_tn_board",
        sa.Column("guest_read_yn", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column(
        "cms_tn_board",
        sa.Column("write_yn", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column(
        "cms_tn_board",
        sa.Column("guest_write_yn", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "cms_tn_board",
        sa.Column("category_yn", sa.Boolean(), server_default="false", nullable=False),
    )

    # cms_tn_board_category — Phase 3 선반영
    op.execute("CREATE SEQUENCE IF NOT EXISTS seq_bcat START 1 INCREMENT 1")
    op.create_table(
        "cms_tn_board_category",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("board_id", sa.String(length=20), nullable=False),
        sa.Column("category_name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("use_yn", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=20), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.String(length=20), nullable=False),
        sa.Column("del_yn", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["board_id"], ["cms_tn_board.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_board_category_board", "cms_tn_board_category", ["board_id"], unique=False)

    # cms_tn_post — category_id 추가
    op.add_column(
        "cms_tn_post",
        sa.Column("category_id", sa.String(length=20), nullable=True),
    )
    op.create_foreign_key(
        "fk_post_category",
        "cms_tn_post",
        "cms_tn_board_category",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_post_category", "cms_tn_post", ["category_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_post_category", table_name="cms_tn_post")
    op.drop_constraint("fk_post_category", "cms_tn_post", type_="foreignkey")
    op.drop_column("cms_tn_post", "category_id")

    op.drop_index("ix_board_category_board", table_name="cms_tn_board_category")
    op.drop_table("cms_tn_board_category")
    op.execute("DROP SEQUENCE IF EXISTS seq_bcat")

    op.drop_column("cms_tn_board", "category_yn")
    op.drop_column("cms_tn_board", "guest_write_yn")
    op.drop_column("cms_tn_board", "write_yn")
    op.drop_column("cms_tn_board", "guest_read_yn")
    op.drop_column("cms_tn_board", "read_yn")
