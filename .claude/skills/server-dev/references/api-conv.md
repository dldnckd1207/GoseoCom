# API 컨벤션

---

## 1. HTTP Method

| 작업 | Method | 이유 |
|------|--------|------|
| 단건 조회 (path param만) | `GET` | QS 없음, 브라우저/캐시 친화적 |
| 목록/검색 조회 (조건 있음) | `POST` | QS 노출 방지, body로 검색 조건 전달 |
| 생성 | `POST` | |
| 수정 | `PUT` | 전체 필드 전달 원칙 (PATCH 미사용) |
| 삭제 | `DELETE` | |
| 파일 서빙 | `GET` | 브라우저 직접 접근 |

**판단 기준:** QS가 필요 없으면 `GET`, 검색 조건·필터·페이지네이션 등 body가 필요하면 `POST`

```
GET  /posts/{id}        → 단건 조회 (path param만)
POST /posts/list        → 목록 조회 (검색 조건 body)
POST /posts             → 생성
PUT  /posts/{id}        → 수정
DELETE /posts/{id}      → 삭제
```

> `PATCH` 사용 금지 (Architecture AD-17).

---

## 2. Base URL

| 대상 | Base URL | 비고 |
|------|----------|------|
| 클라이언트 (GUEST/USER) | `/api/v1/{resource}` | `router.py` |
| 관리자 (ADMIN 이상) | `/admin/api/v1/{resource}` | `admin_router.py`, Phase 3 |

**라우터 분리 원칙:**
- 같은 도메인이라도 클라이언트용과 관리자용 라우터를 별도 파일로 분리
- `router.py`: GUEST/USER 대상, 활성 데이터만 노출
- `admin_router.py`: ADMIN 대상, 전체 데이터 포함 (비활성/삭제 포함), Phase 3 구현

```python
# router.py — 클라이언트용
router = APIRouter(prefix="/api/v1/{resource}s", tags=["{resource}"])

# admin_router.py — 관리자용 (Phase 3)
admin_router = APIRouter(prefix="/admin/api/v1/{resource}s", tags=["admin-{resource}"])
```

---

## 3. 공통 응답 형식

모든 응답은 아래 구조를 따른다. HTTP status code는 transport 레벨 오류에만 의미, 앱 레벨 성공/실패는 `header.success`로 판단.

```json
{
  "header": {
    "success": true,
    "code": "SUCCESS",
    "message": "요청이 성공적으로 처리되었습니다."
  },
  "body": {
    "data": { ... }
  }
}
```

### 작업별 응답

| 작업 | `header.code` | `body.data` | HTTP status |
|------|--------------|-------------|-------------|
| 조회 (단건/목록) | `SUCCESS` | 데이터 객체 또는 페이징 객체 | 200 |
| 생성 | `CREATED` | 생성된 전체 객체 | 201 |
| 수정 | `UPDATED` | 수정된 전체 객체 | 200 |
| 삭제 | `DELETED` | `null` | 200 |

### 목록/페이징 data 구조

```json
{
  "header": { "success": true, "code": "SUCCESS", "message": "..." },
  "body": {
    "data": {
      "items": [...],
      "total": 100,
      "page": 1,
      "size": 20
    }
  }
}
```

### 에러 응답

```json
{
  "header": {
    "success": false,
    "code": "POST_NOT_FOUND",
    "message": "게시글을 찾을 수 없습니다."
  },
  "body": {
    "data": null
  }
}
```

---

## 4. 응답 코드 체계

### 성공 코드

| code | 의미 |
|------|------|
| `SUCCESS` | 조회/수정 성공 |
| `CREATED` | 생성 성공 |
| `UPDATED` | 수정 성공 |
| `DELETED` | 삭제 성공 |

### 에러 코드

| code | HTTP | 상황 |
|------|------|------|
| `UNAUTHORIZED` | 401 | 토큰 없음 |
| `TOKEN_EXPIRED` | 401 | 토큰 만료 |
| `INVALID_TOKEN` | 401 | 토큰 형식 오류 |
| `FORBIDDEN` | 403 | 권한 부족 / 소유권 없음 |
| `WITHDRAWN_USER` | 403 | 탈퇴 후 90일 이내 재가입 시도 |
| `{DOMAIN}_NOT_FOUND` | 404 | 리소스 없음 (예: `POST_NOT_FOUND`, `BOARD_NOT_FOUND`) |
| `{DOMAIN}_ALREADY_EXISTS` | 409 | 중복 (예: `BOARD_CODE_ALREADY_EXISTS`) |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |

---

## 5. 구현 패턴

### ApiResponse 사용

```python
from app.core.common.response import ApiResponse, PageData

# 단건 조회
return ApiResponse.success(PostResponse.model_validate(entity))

# 목록 조회
return ApiResponse.success(PageData(items=items, total=total, page=page, size=size))

# 생성
return ApiResponse.created(PostResponse.model_validate(entity))

# 수정
return ApiResponse.updated(PostResponse.model_validate(entity))

# 삭제
return ApiResponse.deleted()
```

### Router response_model

```python
@router.post("/posts", response_model=ApiResponse[PostResponse], status_code=201)
async def create_post(...):
    ...

@router.post("/posts/list", response_model=ApiResponse[PageData[PostResponse]])
async def list_posts(...):
    ...
```

---

## 6. 페이지네이션 요청

```python
class PostSearchRequest(BaseModel):
    keyword: str | None = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
```

기본값: `page=1`, `size=20`

---

## 7. Swagger 문서화

### 7.1 Schema 필드 문서화

모든 Pydantic 스키마 필드에 `description`과 `examples`를 추가한다.

```python
from pydantic import BaseModel, Field

class PostResponse(BaseModel):
    id: str = Field(..., description="게시글 ID", examples=["POST_00000001"])
    title: str = Field(..., description="게시글 제목", examples=["안녕하세요"])
    content: str = Field(..., description="게시글 본문")
    notice_yn: bool = Field(..., description="공지 여부", examples=[False])
    view_count: int = Field(..., description="조회수", examples=[0])
    created_at: datetime = Field(..., description="작성일시")

    model_config = {"from_attributes": True}
```

### 7.2 Router 엔드포인트 문서화

```python
@router.post(
    "/posts",
    summary="게시글 작성",
    description="로그인한 사용자가 게시판에 글을 작성합니다. 첨부파일은 file_ids로 전달.",
    response_model=ApiResponse[PostResponse],
    status_code=201,
    responses={
        401: _ERR_401_UNAUTHORIZED,
        403: _ERR_403_FORBIDDEN,
    },
    tags=["posts"],
)
async def create_post(...):
    ...
```

### 7.3 공통 에러 응답 딕셔너리 재사용

도메인별 `router.py` 상단에 공통 에러 응답을 정의하고 재사용한다.

```python
# router.py 상단에 정의
_ERR_401_UNAUTHORIZED = {
    "description": "인증 필요",
    "content": {"application/json": {"examples": {
        "no_token": {"summary": "토큰 없음", "value": {
            "header": {"success": False, "code": "UNAUTHORIZED", "message": "로그인이 필요합니다."},
            "body": {"data": None},
        }},
        "token_expired": {"summary": "토큰 만료", "value": {
            "header": {"success": False, "code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다."},
            "body": {"data": None},
        }},
    }}},
}

_ERR_403_FORBIDDEN = {
    "description": "권한 없음",
    "content": {"application/json": {"example": {
        "header": {"success": False, "code": "FORBIDDEN", "message": "접근 권한이 없습니다."},
        "body": {"data": None},
    }}},
}

def _err_404(domain: str, message: str) -> dict:
    """도메인별 404 응답 생성 헬퍼"""
    return {
        "description": "리소스 없음",
        "content": {"application/json": {"example": {
            "header": {"success": False, "code": f"{domain}_NOT_FOUND", "message": message},
            "body": {"data": None},
        }}},
    }

# 사용
responses={
    401: _ERR_401_UNAUTHORIZED,
    403: _ERR_403_FORBIDDEN,
    404: _err_404("POST", "게시글을 찾을 수 없습니다."),
}
```

### 7.4 Swagger 문서화 체크리스트

| 항목 | 방법 |
|------|------|
| Response Schema 표시 | `response_model=ApiResponse[T]` |
| Request Body 표시 | Pydantic 스키마에 `Field(description=...)` |
| 엔드포인트 설명 | `summary="..."`, `description="..."` |
| 에러 응답 표시 | `responses={401: ..., 403: ..., 404: ...}` |
| 필드 예시값 | `Field(..., examples=["USR_00000001"])` |
| 태그 그룹핑 | `tags=["posts"]` (router prefix와 일치) |

> **실제 예시**: `app/auth/router.py` 참조
