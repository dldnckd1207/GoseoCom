# Haedok AI — Server

> **[필수] 이 디렉토리의 코드를 작성/수정/디버깅하기 전에 반드시 `/server-dev` skill을 실행하세요.**
> skill 없이 코드를 작성하면 프로젝트 컨벤션을 위반할 수 있습니다.
>
> DB 작업(테이블/컬럼/마이그레이션) 시에는 `/db-dev` skill도 함께 실행하세요.

---

## 기술 스택

- **Runtime:** Python 3.12+
- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2.x (async)
- **DB:** PostgreSQL 16+
- **Migration:** Alembic
- **Package Manager:** uv
- **Linter/Formatter:** ruff
- **Type Checker:** mypy (strict)

---

## URL 구조

| 경로 | 용도 |
|------|------|
| `/api/v1/**` | 클라이언트(사용자) API |
| `/auth/**` | OAuth 인증 (Google, Kakao) |
| `/docs` | Swagger UI (개발 환경) |

- 인증: JWT httpOnly 쿠키 (`access_token` + `refresh_token`)

---

## 도메인 구조

| 도메인 | 모듈 경로 | 테이블 | Phase |
|--------|-----------|--------|-------|
| User | `app/core/user/` | `com_tn_user`, `com_tn_user_oauth`, `com_tn_user_token` | 1 |
| File | `app/core/files/` | `com_tn_file`, `com_tn_file_map` | 1 |
| Auth | `app/auth/` | `com_th_login_log` | 1 |
| Board | `app/board/` | `cms_tn_board`, `cms_tn_post`, `cms_tn_comment`, `cms_th_post_history` | 1 |
| Translate | `app/translate/` | `ai_tn_book`, `ai_tn_book_page`, `ai_th_page_revision` | 1~2 |
| Pipeline | `app/translate/pipeline/` | `ai_th_pipeline_run` | 1 |
| Admin Audit | `app/core/audit/` | `com_th_admin_audit_log` | 3 |

---

## 핵심 컨벤션 (요약)

- HTTP Method: GET 조회, POST 생성, PUT 수정, DELETE 삭제 (`PATCH` 금지)
- 인증: `require_level(UserRole.X)` Dependency
- ID: `await next_id("PREFIX_", db)` — PostgreSQL Sequence
- 에러: `raise HTTPException(status_code=..., detail={"code": "...", "message": "..."})`
- `commit()`은 Service에서, `flush()`는 Repository에서 호출

---

## 빌드 및 실행

```bash
# 개발 서버
cd apps/server && uv run uvicorn app.main:app --reload

# 마이그레이션
uv run alembic upgrade head

# 테스트
uv run pytest

# 린트
uv run ruff check .
uv run mypy .
```

---

## 환경 변수

`.env` 파일 참조. DB, JWT, OAuth, CORS 등 설정.
