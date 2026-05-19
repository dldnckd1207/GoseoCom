# 구현 패턴 템플릿

새 도메인 CRUD를 구현할 때 참조하는 전체 템플릿입니다.

---

## 1. 새 도메인 추가 시 생성할 파일

```
app/{domain}/
├── __init__.py
├── models.py      # SQLAlchemy 모델
├── schemas.py     # Pydantic Request/Response 스키마
├── repository.py  # DB 쿼리 (비즈니스 로직 없음)
├── service.py     # 비즈니스 로직 (Repository 호출)
└── router.py      # FastAPI APIRouter (엔드포인트 정의)
```

`main.py`에 라우터 등록 필수.

---

## 2. Model 패턴

```python
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin


class {Domain}(Base, TimestampMixin, SoftDeleteMixin):
    """도메인 설명"""

    __tablename__ = "{module}_tn_{domain}"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # {PREFIX}_00000001
    # --- 비즈니스 컬럼 ---
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    use_yn: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        Index("ix_{domain}_use", "use_yn"),
    )
```

**핵심 규칙:**
- `TimestampMixin`: `created_at`, `created_by`, `updated_at`, `updated_by` 자동 포함
- `SoftDeleteMixin`: `del_yn`, `deleted_at`, `deleted_by` 자동 포함
- 논리 삭제 불필요한 이력 테이블은 `TimestampMixin`만 사용 (또는 둘 다 미사용)
- 새 모델은 반드시 `alembic/env.py`에서 import 확인

---

## 3. Schema 패턴

```python
from datetime import datetime
from pydantic import BaseModel, Field


# --- Request ---

class {Domain}CreateRequest(BaseModel):
    name: str = Field(..., max_length=100, description="명칭")
    description: str | None = Field(None, max_length=500)
    use_yn: bool = Field(True)


class {Domain}UpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    use_yn: bool | None = None


class {Domain}SearchRequest(BaseModel):
    keyword: str | None = None
    use_yn: bool | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


# --- Response ---

class {Domain}Response(BaseModel):
    id: str
    name: str
    description: str | None
    use_yn: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# 목록 응답은 PageData[{Domain}Response] 사용 — 별도 ListResponse 클래스 불필요
# ApiResponse[PageData[{Domain}Response]] 형태로 반환
```

**핵심 규칙:**
- `model_config = {"from_attributes": True}` — ORM 모델에서 직접 변환
- Request 스키마는 `BaseModel` 상속 (Pydantic v2)
- `created_by`, `updated_by`는 Response에서 기본 노출 안 함 (관리자 전용 응답에만 포함)
- 목록 응답용 별도 `{Domain}ListResponse` 클래스 불필요 — `PageData[{Domain}Response]` 공용 사용

---

## 4. Repository 패턴

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.{domain}.models import {Domain}
from app.{domain}.schemas import {Domain}SearchParams


class {Domain}Repository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: str) -> {Domain} | None:
        result = await self.db.execute(
            select({Domain}).where({Domain}.id == id, {Domain}.del_yn.is_(False))
        )
        return result.scalar_one_or_none()

    async def get_list(self, params: {Domain}SearchParams) -> tuple[list[{Domain}], int]:
        q = select({Domain}).where({Domain}.del_yn.is_(False))

        if params.keyword:
            q = q.where({Domain}.name.ilike(f"%{params.keyword}%"))
        if params.use_yn is not None:
            q = q.where({Domain}.use_yn == params.use_yn)

        # 전체 건수
        count_result = await self.db.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = count_result.scalar_one()

        # 페이징
        offset = (params.page - 1) * params.size
        items_result = await self.db.execute(
            q.order_by({Domain}.sort_order, {Domain}.created_at.desc())
             .offset(offset)
             .limit(params.size)
        )
        items = list(items_result.scalars().all())

        return items, total

    async def create(self, entity: {Domain}) -> {Domain}:
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def delete(self, entity: {Domain}, deleted_by: str) -> None:
        entity.del_yn = True
        entity.deleted_by = deleted_by
        from datetime import datetime, timezone
        entity.deleted_at = datetime.now(timezone.utc)
```

**핵심 규칙:**
- `flush()` — 세션 내 SELECT로 확인 가능하게 함 (commit은 Service가 담당)
- `del_yn.is_(False)` — SQLAlchemy Boolean 비교는 `==` 대신 `is_(False)` 사용
- Repository는 순수 DB 접근만, 비즈니스 로직 없음

---

## 5. Service 패턴

```python
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.id_generator import next_id
from app.core.common.response import ApiResponse, PageData
from app.{domain}.models import {Domain}
from app.{domain}.repository import {Domain}Repository
from app.{domain}.schemas import (
    {Domain}CreateRequest,
    {Domain}Response,
    {Domain}SearchRequest,
    {Domain}UpdateRequest,
)


class {Domain}Service:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = {Domain}Repository(db)
        self.db = db

    async def get_list(self, req: {Domain}SearchRequest) -> ApiResponse[PageData[{Domain}Response]]:
        items, total = await self.repo.get_list(req)
        return ApiResponse.success(PageData(
            items=[{Domain}Response.model_validate(i) for i in items],
            total=total,
            page=req.page,
            size=req.size,
        ))

    async def get_detail(self, id: str) -> ApiResponse[{Domain}Response]:
        entity = await self.repo.get_by_id(id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "{DOMAIN}_NOT_FOUND", "message": "{도메인}을(를) 찾을 수 없습니다."},
            )
        return ApiResponse.success({Domain}Response.model_validate(entity))

    async def create(self, req: {Domain}CreateRequest, created_by: str) -> ApiResponse[{Domain}Response]:
        id = await next_id("{PREFIX}_", self.db)
        entity = {Domain}(
            id=id,
            name=req.name,
            description=req.description,
            use_yn=req.use_yn,
            created_by=created_by,
            updated_by=created_by,
        )
        await self.repo.create(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return ApiResponse.created({Domain}Response.model_validate(entity))

    async def update(self, id: str, req: {Domain}UpdateRequest, updated_by: str) -> ApiResponse[{Domain}Response]:
        entity = await self.repo.get_by_id(id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "{DOMAIN}_NOT_FOUND", "message": "{도메인}을(를) 찾을 수 없습니다."},
            )
        if req.name is not None:
            entity.name = req.name
        if req.description is not None:
            entity.description = req.description
        if req.use_yn is not None:
            entity.use_yn = req.use_yn
        entity.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(entity)
        return ApiResponse.updated({Domain}Response.model_validate(entity))

    async def delete(self, id: str, deleted_by: str) -> ApiResponse[None]:
        entity = await self.repo.get_by_id(id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "{DOMAIN}_NOT_FOUND", "message": "{도메인}을(를) 찾을 수 없습니다."},
            )
        await self.repo.delete(entity, deleted_by)
        await self.db.commit()
        return ApiResponse.deleted()
```

**핵심 규칙:**
- `commit()`은 Service에서 호출
- `flush()`는 Repository에서, 같은 트랜잭션 내 후속 조회 필요 시
- 수정 시 `None` 병합: `if req.field is not None: entity.field = req.field`
- 에러: `raise HTTPException(status_code=..., detail={"code": "...", "message": "..."})`

---

## 6. Router 패턴

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole
from app.core.common.response import ApiResponse, PageData
from app.db.session import get_db
from app.{domain}.schemas import (
    {Domain}CreateRequest,
    {Domain}Response,
    {Domain}SearchRequest,
    {Domain}UpdateRequest,
)
from app.{domain}.service import {Domain}Service

router = APIRouter(prefix="/api/v1/{domain}s", tags=["{domain}"])


def _service(db: AsyncSession = Depends(get_db)) -> {Domain}Service:
    return {Domain}Service(db)


# 목록 조회 — 검색 조건 있음 → POST
@router.post("/list", response_model=ApiResponse[PageData[{Domain}Response]])
async def list_{domain}s(
    req: {Domain}SearchRequest,
    service: {Domain}Service = Depends(_service),
    _: dict = require_level(UserRole.GUEST),
) -> ApiResponse[PageData[{Domain}Response]]:
    return await service.get_list(req)


# 단건 조회 — path param만 → GET
@router.get("/{id}", response_model=ApiResponse[{Domain}Response])
async def get_{domain}(
    id: str,
    service: {Domain}Service = Depends(_service),
    _: dict = require_level(UserRole.GUEST),
) -> ApiResponse[{Domain}Response]:
    return await service.get_detail(id)


@router.post("", response_model=ApiResponse[{Domain}Response], status_code=201)
async def create_{domain}(
    req: {Domain}CreateRequest,
    payload: dict = require_level(UserRole.USER),
    service: {Domain}Service = Depends(_service),
) -> ApiResponse[{Domain}Response]:
    return await service.create(req, created_by=payload["sub"])


@router.put("/{id}", response_model=ApiResponse[{Domain}Response])
async def update_{domain}(
    id: str,
    req: {Domain}UpdateRequest,
    payload: dict = require_level(UserRole.USER),
    service: {Domain}Service = Depends(_service),
) -> ApiResponse[{Domain}Response]:
    return await service.update(id, req, updated_by=payload["sub"])


@router.delete("/{id}", response_model=ApiResponse[None])
async def delete_{domain}(
    id: str,
    payload: dict = require_level(UserRole.ADMIN),
    service: {Domain}Service = Depends(_service),
) -> ApiResponse[None]:
    return await service.delete(id, deleted_by=payload["sub"])
```

**핵심 규칙:**
- 모든 응답은 `ApiResponse[T]`로 래핑 (`{ header, body: { data } }`)
- 목록 조회: `POST /list` + `ApiResponse[PageData[T]]`
- 단건 조회: `GET /{id}` + `ApiResponse[T]`
- 삭제: `ApiResponse[None]` 반환 (204 대신 200 + `DELETED` code)
- 권한 불필요 시 `_: dict = require_level(UserRole.GUEST)` 패턴
- `payload["sub"]` — JWT `sub` 클레임 = 사용자 ID (`USR_XXXXXXXX`)
