"""seed_initial_admins — 최초 관리자 부트스트랩 (이메일 자동 승격 대체 경로)

점검보고서 #3 / D-2(a): 로그인 시 이메일 기반 자동 ADMIN 승격을 제거하면서,
최초 관리자 지정을 운영자가 통제하는 안전한 경로(시드 마이그레이션)로 대체한다.

`INITIAL_ADMIN_EMAILS` 환경변수(.env)에 등록된 이메일과 일치하는 **기존 사용자**를
ADMIN(70)으로 승격한다. 비어 있으면 아무 작업도 하지 않는다(no-op).
이후 관리자 지정/변경은 SYSTEM_ADMIN의 수동 변경(admin_update_user)으로 일원화한다.

Revision ID: a7b8c9d0e1f2
Revises: 69a346b7b787
Create Date: 2026-06-11 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.config import settings
from app.core.common.enums import UserRole

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "69a346b7b787"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SYSTEM_USER = "USR_00000000"
_ADMIN = UserRole.ADMIN.value
_USER = UserRole.USER.value


def upgrade() -> None:
    emails = settings.admin_emails
    if not emails:
        return
    op.get_bind().execute(
        sa.text(
            """
            UPDATE com_tn_user
            SET user_level = :admin_level,
                updated_at = NOW(),
                updated_by = :system_user
            WHERE email IN :emails
              AND user_level < :admin_level
              AND del_yn = false
            """
        ).bindparams(sa.bindparam("emails", expanding=True)),
        {"admin_level": _ADMIN, "system_user": _SYSTEM_USER, "emails": emails},
    )


def downgrade() -> None:
    emails = settings.admin_emails
    if not emails:
        return
    # 승격된 ADMIN(정확히 70)만 USER로 되돌린다. SYSTEM_ADMIN(100)은 건드리지 않는다.
    op.get_bind().execute(
        sa.text(
            """
            UPDATE com_tn_user
            SET user_level = :user_level,
                updated_at = NOW(),
                updated_by = :system_user
            WHERE email IN :emails
              AND user_level = :admin_level
              AND del_yn = false
            """
        ).bindparams(sa.bindparam("emails", expanding=True)),
        {
            "user_level": _USER,
            "admin_level": _ADMIN,
            "system_user": _SYSTEM_USER,
            "emails": emails,
        },
    )
