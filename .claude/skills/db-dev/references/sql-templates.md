# SQLAlchemy 모델 + DDL 템플릿

PostgreSQL 16+ 기준입니다.

---

## 1. Normal 테이블 (`_tn_`) — 마스터/업무

ID-Gen + TimestampMixin + SoftDeleteMixin 포함 표준 템플릿.

### SQLAlchemy 모델

```python
from sqlalchemy import Boolean, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class Board(Base, TimestampMixin, SoftDeleteMixin):
    """게시판"""

    __tablename__ = "cms_tn_board"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # BRD_00000001
    board_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    board_name: Mapped[str] = mapped_column(String(100), nullable=False)
    board_desc: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    use_yn: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        UniqueConstraint("board_code", name="uq_board_code"),
        Index("ix_board_use", "use_yn", "sort_order"),
    )
```

### 해당 PostgreSQL DDL

```sql
CREATE TABLE cms_tn_board (
    id          VARCHAR(20)  NOT NULL,
    board_code  VARCHAR(50)  NOT NULL,
    board_name  VARCHAR(100) NOT NULL,
    board_desc  VARCHAR(500),
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    use_yn      BOOLEAN      NOT NULL DEFAULT true,
    -- 공통 컬럼 (TimestampMixin) --
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by  VARCHAR(20)  NOT NULL,
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_by  VARCHAR(20)  NOT NULL,
    -- 논리 삭제 (SoftDeleteMixin) --
    del_yn      BOOLEAN      NOT NULL DEFAULT false,
    deleted_at  TIMESTAMPTZ,
    deleted_by  VARCHAR(20),
    PRIMARY KEY (id),
    CONSTRAINT uq_board_code UNIQUE (board_code)
);

CREATE INDEX ix_board_use ON cms_tn_board (use_yn, sort_order);
```

---

## 2. History 테이블 (`_th_`) — 이력/로그

BIGSERIAL PK, append-only. TimestampMixin/SoftDeleteMixin 없음.

### SQLAlchemy 모델

```python
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PostHistory(Base):
    """게시글 이력 — append-only"""

    __tablename__ = "cms_th_post_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(
        ForeignKey("cms_tn_post.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # CREATE | UPDATE | DELETE | ROLLBACK
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_post_history_post", "post_id", "changed_at"),
    )
```

### 해당 PostgreSQL DDL

```sql
CREATE TABLE cms_th_post_history (
    id          BIGSERIAL    NOT NULL,
    post_id     VARCHAR(20)  NOT NULL REFERENCES cms_tn_post(id) ON DELETE RESTRICT,
    version     INTEGER      NOT NULL,
    action      VARCHAR(20)  NOT NULL,
    title       VARCHAR(255) NOT NULL,
    content     TEXT         NOT NULL,
    changed_by  VARCHAR(20)  NOT NULL,
    changed_at  TIMESTAMPTZ  NOT NULL,
    PRIMARY KEY (id)
);

CREATE INDEX ix_post_history_post ON cms_th_post_history (post_id, changed_at);
```

---

## 3. FileMap 첨부/탈부착 패턴

`com_tn_file_map`은 다형 매핑 테이블. `target_id`에 FK 없이 `target_type`으로 대상 구분.

### 첨부 (Upsert)

```python
# (file_id, target_type, target_id) 기준으로 있으면 del_yn=false, 없으면 INSERT (FBR-02)
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = pg_insert(FileMap).values(
    id=await next_id("FMAP_", db),
    file_id=file_id,
    target_type=target_type,   # "POST" | "COMMENT" | "BOOK"
    target_id=target_id,
    file_group=file_group,
    sort_order=sort_order,
    created_at=now,
    created_by=user_id,
    updated_at=now,
    updated_by=user_id,
    del_yn=False,
)
stmt = stmt.on_conflict_do_update(
    index_elements=["file_id", "target_type", "target_id"],
    set_={"del_yn": False, "updated_at": now, "updated_by": user_id},
)
await db.execute(stmt)
```

### 탈부착 (Soft Delete)

```python
await db.execute(
    update(FileMap)
    .where(
        FileMap.file_id == file_id,
        FileMap.target_type == target_type,
        FileMap.target_id == target_id,
    )
    .values(del_yn=True, deleted_at=now, deleted_by=user_id)
)
```

### 조회

```python
# 특정 엔티티의 첨부파일 목록
result = await db.execute(
    select(FileMap)
    .where(
        FileMap.target_type == "POST",
        FileMap.target_id == post_id,
        FileMap.del_yn.is_(False),
    )
    .order_by(FileMap.sort_order)
)
```

---

## 4. JSONB 컬럼 (Phase 2+)

```python
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

---

## 4. ALTER 패턴 (Alembic)

### 컬럼 추가

```python
# alembic/versions/{revision}_{desc}.py
def upgrade() -> None:
    op.add_column("ai_tn_book", sa.Column("summary_text", sa.Text(), nullable=True))
    op.add_column("ai_tn_book", sa.Column("keywords", postgresql.JSONB(), nullable=True))

def downgrade() -> None:
    op.drop_column("ai_tn_book", "keywords")
    op.drop_column("ai_tn_book", "summary_text")
```

### 인덱스 추가

```python
def upgrade() -> None:
    op.create_index("ix_post_auto_reply", "cms_tn_post", ["auto_reply_status", "created_at"])

def downgrade() -> None:
    op.drop_index("ix_post_auto_reply", table_name="cms_tn_post")
```

### 컬럼 수정 (타입/nullable 변경)

```python
def upgrade() -> None:
    op.alter_column("cms_tn_post", "title",
        existing_type=sa.String(255),
        type_=sa.String(500),
        nullable=False,
    )
```

---

## 5. ID-Gen 시퀀스 등록

새 `_tn_` 테이블 생성 시 PostgreSQL Sequence 등록 필수.

```python
def upgrade() -> None:
    # 테이블 생성 후 시퀀스 등록
    op.create_table("cms_tn_board", ...)
    op.execute("CREATE SEQUENCE IF NOT EXISTS seq_brd START 1 INCREMENT 1")

def downgrade() -> None:
    op.drop_table("cms_tn_board")
    op.execute("DROP SEQUENCE IF EXISTS seq_brd")
```

`id_generator.py`의 `_SEQ_MAP`에도 동기화:

```python
_SEQ_MAP = {
    ...
    "BRD_": "seq_brd",  # 추가
}
```
