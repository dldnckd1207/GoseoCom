# 예외 처리 패턴

---

## 1. HTTPException 표준 형식

모든 에러 응답은 아래 형식을 따른다:

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."},
)
```

`detail`은 항상 `{"code": "...", "message": "..."}` 딕셔너리.

---

## 2. 공통 에러 코드

### 인증/권한

| status | code | 상황 |
|--------|------|------|
| 401 | `UNAUTHORIZED` | 토큰 없음 |
| 401 | `TOKEN_EXPIRED` | 토큰 만료 |
| 401 | `INVALID_TOKEN` | 토큰 형식 오류 |
| 403 | `FORBIDDEN` | 권한 부족 |
| 403 | `WITHDRAWN_USER` | 탈퇴 후 90일 이내 재가입 시도 |
| 403 | `ACCOUNT_DISABLED` | `use_yn=false` 계정 |

### 리소스

| status | code | 패턴 |
|--------|------|------|
| 404 | `{DOMAIN}_NOT_FOUND` | 리소스 없음 (예: `POST_NOT_FOUND`, `BOARD_NOT_FOUND`) |
| 409 | `{DOMAIN}_ALREADY_EXISTS` | 중복 (예: `BOARD_CODE_ALREADY_EXISTS`) |
| 422 | FastAPI 기본 | Pydantic 유효성 검사 실패 (별도 처리 불필요) |

### 비즈니스

| status | code | 상황 |
|--------|------|------|
| 403 | `NOT_OWNER` | 본인 소유 아닌 리소스 수정/삭제 시도 |
| 400 | `BOARD_ATTACH_NOT_ALLOWED` | 첨부 불가 게시판에 파일 첨부 시도 |
| 400 | `FILE_SIZE_EXCEEDED` | 파일 크기 초과 |
| 400 | `FILE_TYPE_NOT_ALLOWED` | 허용되지 않은 MIME 타입 |
| 400 | `BOOK_NOT_OWNER` | 본인 소유 아닌 Book 수정 시도 |

---

## 3. Service 예외 처리 패턴

### 리소스 조회 (404 표준)

```python
async def get_detail(self, post_id: str) -> PostResponse:
    entity = await self.repo.get_by_id(post_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."},
        )
    return PostResponse.model_validate(entity)
```

### 소유권 검증

```python
async def update(self, post_id: str, req: PostUpdateRequest, user_id: str, user_level: int) -> PostResponse:
    entity = await self.repo.get_by_id(post_id)
    if not entity:
        raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시글을 찾을 수 없습니다."})

    # 본인 또는 ADMIN 이상
    if entity.user_id != user_id and user_level < UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "수정 권한이 없습니다."},
        )
    ...
```

### 중복 검증

```python
async def create_board(self, req: BoardCreateRequest, created_by: str) -> BoardResponse:
    existing = await self.repo.get_by_code(req.board_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "BOARD_CODE_ALREADY_EXISTS", "message": "이미 사용 중인 게시판 코드입니다."},
        )
    ...
```

---

## 4. 주의사항

- `raise Exception(...)` 사용 금지 — 반드시 `HTTPException`
- 에러 메시지는 사용자에게 노출됨을 고려 (내부 스택트레이스 포함 금지)
- `detail` 필드에 문자열 직접 사용 금지 — 반드시 `{"code": ..., "message": ...}` 딕셔너리
