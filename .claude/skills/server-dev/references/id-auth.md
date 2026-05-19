# ID 생성 전략 + 권한 체계

---

## 1. ID 생성 전략

```
형식: {PREFIX}_{8자리숫자}
예: USR_00000001, BRD_00000001, POST_00000001
```

### 1.1 사용법

```python
from app.core.common.id_generator import next_id

# Service에서 사용
id = await next_id("USR_", db)   # → "USR_00000001"
```

### 1.2 ID PREFIX 목록

| 테이블 | PREFIX | 예시 | 도메인 |
|--------|--------|------|--------|
| `com_tn_user` | `USR_` | `USR_00000001` | User |
| `com_tn_user_oauth` | `OAUTH_` | `OAUTH_00000001` | User |
| `com_tn_user_token` | `UTKN_` | `UTKN_00000001` | User |
| `com_tn_file` | `FILE_` | `FILE_00000001` | File |
| `com_tn_file_map` | `FMAP_` | `FMAP_00000001` | File |
| `cms_tn_board` | `BRD_` | `BRD_00000001` | Board |
| `cms_tn_post` | `POST_` | `POST_00000001` | Board |
| `cms_tn_comment` | `CMT_` | `CMT_00000001` | Board |
| `ai_tn_book` | `BOOK_` | `BOOK_00000001` | Translate |
| `ai_tn_book_page` | `BPAGE_` | `BPAGE_00000001` | Translate |

> **History 테이블** (`_th_`) — `BIGSERIAL` Auto Increment (ID-Gen 불필요)

### 1.3 예약 ID

| 값 | 의미 |
|----|------|
| `USR_00000000` | AI 시드 계정 — 자동 답변 댓글 작성자. 삭제/수정 불가 |

### 1.4 새 PREFIX 등록 시

`app/core/common/id_generator.py`의 `_SEQ_MAP` + Alembic 마이그레이션에 시퀀스 추가 필요.

---

## 2. 권한 체계

### 2.1 UserRole Enum

```python
from app.core.common.enums import UserRole

class UserRole(int, Enum):
    GUEST        = 0    # 비로그인 (토큰 없어도 접근 가능)
    USER         = 10   # 일반 사용자 (신규 가입 기본값)
    ADMIN        = 70   # 앱 관리자 (게시판/댓글/게시글 관리, Phase 3)
    SYSTEM_ADMIN = 100  # 시스템 관리자 (로그/설정/파이프라인, Phase 3)
```

### 2.2 require_level 사용법

```python
from app.core.common.decorators.require_level import require_level
from app.core.common.enums import UserRole

# 패턴 1: dependencies= (payload 필요 없을 때)
@router.get("/boards", dependencies=[require_level(UserRole.GUEST)])
async def list_boards():
    ...

# 패턴 2: 직접 주입 (payload["sub"] 등 JWT 클레임 필요할 때)
@router.post("/posts")
async def create_post(
    payload: dict = require_level(UserRole.USER),
    ...
):
    user_id = payload["sub"]   # USR_XXXXXXXX
    user_level = payload.get("level", 10)
```

### 2.3 API 엔드포인트 권한 기준

| 작업 | 최소 레벨 | 예시 |
|------|----------|------|
| 조회 (공개) | `GUEST` | 게시글 목록/상세 |
| 조회 (로그인 필요) | `USER` | 내 라이브러리 |
| 생성/수정/삭제 (본인) | `USER` | 게시글 작성, 번역 요청 |
| 관리자 작업 | `ADMIN` | 게시판 관리, 게시글 강제 삭제 |
| 시스템 작업 | `SYSTEM_ADMIN` | 파이프라인 재실행, 설정 변경 |

### 2.4 JWT 토큰 정책

| 항목 | 값 | 설정 위치 |
|------|-----|----------|
| Access Token 만료 | 60분 | `settings.jwt_access_token_expire_minutes` |
| Refresh Token 만료 | 30일 | `settings.jwt_refresh_token_expire_days` |
| Rotation Grace Period | 30초 | `ROTATION_GRACE_SECONDS` (`auth/service.py`) |
| 알고리즘 | HS256 | `settings.jwt_algorithm` |

**JWT Access Token 클레임:**

```python
{
    "sub": "USR_00000001",   # 사용자 ID
    "level": 10,             # UserRole 값 (0/10/70/100)
    "blocked": False,        # block_yn 값
    "exp": ...,              # 만료 시각
    "type": "access"
}
```

**Refresh Token Rotation 정책:**
- Refresh Token 사용 시 → 새 토큰 발급 + 이전 토큰 `is_revoked=true`
- 이미 `is_revoked=true`인 토큰 재사용 → Grace Period(30초) 초과 시 해당 유저 **전체 세션 무효화** (탈취 감지)
- 만료 토큰은 스케줄러가 주기적으로 hard delete

**계정 상태별 로그인 처리:**

| 상태 | 처리 | 에러 코드 |
|------|------|----------|
| `use_yn=false` | 로그인 거부 | `ACCOUNT_DISABLED` |
| `block_yn=true` | 로그인 허용, JWT에 `blocked=true` 포함 | — |
| `block_yn=true` + USER 이상 접근 | `require_level`에서 차단 | `ACCOUNT_BLOCKED` |

**GUEST 레벨 주의사항:**
- 토큰 없으면 `{}` 반환 (비로그인 처리)
- 토큰 있지만 만료/변조된 경우도 `{}` 반환 (비로그인으로 처리, 에러 아님)

---

### 2.5 핵심 비즈니스 규칙 (권한)

| ID | 규칙 |
|----|------|
| UBR-04 | `use_yn=false` 계정은 로그인 거부 |
| UBR-05 | `block_yn=true` 계정은 로그인은 가능하나 USER 이상 서비스 이용 제한 |
| BBR-01 | 게시글 작성은 USER 이상만 가능 |
| BBR-05 | 게시글/댓글 수정·삭제는 본인 또는 ADMIN 이상만 가능 |
| TBR-01 | 번역기는 USER 이상만 사용 가능 |
| TBR-06 | 번역 수정은 본인 소유 Book만 가능 (`book.owner_user_id == 요청자`) |
