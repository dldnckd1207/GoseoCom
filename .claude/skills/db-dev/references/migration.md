# Alembic 마이그레이션 규칙

---

## 1. 파일 구조

```
apps/server/
├── alembic/
│   ├── env.py           # 마이그레이션 환경 설정
│   └── versions/        # 마이그레이션 파일
│       ├── {rev}_{desc}.py
│       └── ...
└── alembic.ini          # Alembic 설정
```

---

## 2. 마이그레이션 파일 생성

### 자동 생성 (모델 기반)

```bash
cd apps/server
uv run alembic revision --autogenerate -m "설명"
```

> **주의:** autogenerate 후 반드시 생성된 파일 검토 필요. 불필요한 변경 포함 가능.

### 수동 생성 (빈 파일)

```bash
uv run alembic revision -m "설명"
```

---

## 3. 파일명 규칙

```
{revision_id}_{간단한_설명}.py

예시:
2227df8fb0d6_init_all_tables.py
1227cc541196_sfr108_user_token_device_info.py
```

- 설명은 영문 snake_case
- 날짜 prefix 불필요 (Alembic이 revision_id로 순서 관리)

---

## 4. 파일 구조 (필수 요소)

```python
"""간단한 설명

Revision ID: {revision_id}
Revises: {down_revision}
Create Date: {timestamp}
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '{revision_id}'
down_revision: Union[str, None] = '{parent_revision}'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 변경 사항 적용
    ...


def downgrade() -> None:
    # 변경 사항 롤백
    ...
```

---

## 5. Phase별 마이그레이션 원칙

| Phase | 내용 |
|-------|------|
| Phase 1 | 전체 스키마 초기화 (현재 완료: `2227df8fb0d6_init_all_tables.py`) |
| Phase 2 | `ai_th_page_revision` INSERT 활성화, `share_token` 등 선반영 컬럼 활용 |
| Phase 3 | `com_th_admin_audit_log` INSERT 활성화, 관리자 기능 |

> **선반영 컬럼**: Phase 2~3 기능을 위한 컬럼은 Phase 1 마이그레이션에 이미 포함됨 (스키마 변경 없이 로직만 추가)

---

## 6. 실행 명령

```bash
cd apps/server

# 최신 버전으로 업그레이드
uv run alembic upgrade head

# 현재 버전 확인
uv run alembic current

# 마이그레이션 이력 확인
uv run alembic history

# 한 단계 롤백
uv run alembic downgrade -1

# 특정 버전으로 롤백
uv run alembic downgrade {revision_id}
```

---

## 7. 새 모델 추가 시 체크리스트

1. `app/{domain}/models.py`에 모델 작성
2. **`alembic/env.py`에 import 추가** (아래 참조)
3. `alembic revision --autogenerate -m "설명"` 실행
4. 생성된 파일 검토 (불필요한 변경 제거)
5. Normal 테이블이면 Sequence 등록 코드 추가 (아래 참조)
6. `app/core/common/id_generator.py`의 `_SEQ_MAP`에 PREFIX 등록
7. `alembic upgrade head` 실행 및 확인

### alembic/env.py — 모델 import 방법

새 도메인 모델은 반드시 `env.py`에 추가해야 `autogenerate`가 감지한다.

```python
# alembic/env.py
import app.core.user.models   # noqa: F401
import app.core.files.models  # noqa: F401
import app.core.audit.models  # noqa: F401
import app.auth.models        # noqa: F401
import app.board.models       # noqa: F401
import app.translate.models   # noqa: F401
# 새 도메인 추가 시 여기에 추가:
# import app.{domain}.models  # noqa: F401
```

> `# noqa: F401` 필수 — ruff가 "미사용 import"로 경고 없이 통과.

### Normal 테이블 Sequence 등록

```python
def upgrade() -> None:
    op.create_table("{module}_tn_{name}", ...)
    op.execute("CREATE SEQUENCE IF NOT EXISTS seq_{name} START 1 INCREMENT 1")

def downgrade() -> None:
    op.drop_table("{module}_tn_{name}")
    op.execute("DROP SEQUENCE IF EXISTS seq_{name}")
```

---

## 8. 롤백 안전성

- 운영 환경에서는 `downgrade` 사용 지양 (데이터 손실 위험)
- 개발 환경에서는 자유롭게 사용 가능
- 테이블/컬럼 DROP 전에 데이터 백업 확인
- FK 제약 있는 테이블 삭제 시 역순으로 (자식 → 부모 순서)
