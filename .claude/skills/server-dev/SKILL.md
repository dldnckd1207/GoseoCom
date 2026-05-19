---
name: server-dev
description: Haedok AI Server(FastAPI/Python 3.12/SQLAlchemy/PostgreSQL) 개발 시 아키텍처, 구현 패턴, 컨벤션을 제공하는 skill. apps/server/ 디렉토리의 코드를 작성/수정/디버깅할 때 사용.
---

# Haedok AI Server 개발 가이드

> **[필수]** `apps/server/` 디렉토리의 코드를 작성/수정/디버깅할 때 반드시 이 skill의 컨벤션을 따르세요.

---

## 핵심 아키텍처

### 요청-응답 흐름

```
HTTP Request
  → FastAPI Router
  → require_level(UserRole.X) Dependency (인증/권한)
  → Router 함수 (get_db Dependency → AsyncSession)
  → Service (비즈니스 로직)
  → Repository (DB 쿼리, SQLAlchemy async)
  → PostgreSQL
  → Pydantic Response 스키마 반환
```

### 모듈 구조

```
apps/server/app/
├── auth/          # 인증 (OAuth, JWT, Refresh Token Rotation)
├── board/         # 게시판/게시글/댓글
├── core/          # 핵심 공통
│   ├── common/    # ID 채번, Enum, 데코레이터
│   ├── files/     # 파일 업로드/다운로드
│   ├── settings/  # 앱 설정
│   ├── user/      # 사용자 모델
│   └── security.py
├── translate/     # OCR + 번역 파이프라인 (고서 해독)
├── db/            # SQLAlchemy Base, Session, Mixin
├── config.py
└── main.py
```

### 새 도메인 파일 구조

```
app/{domain}/
├── __init__.py
├── models.py      # SQLAlchemy ORM 모델 (Base 상속)
├── schemas.py     # Pydantic 스키마 (Request/Response)
├── repository.py  # DB 쿼리 (AsyncSession)
├── service.py     # 비즈니스 로직
└── router.py      # FastAPI APIRouter
```

### 핵심 규칙

- HTTP Method: GET 단건조회(path param만), POST 목록조회·생성, PUT 수정, DELETE 삭제 (`PATCH` 사용 금지)
- 인증: `require_level(UserRole.X)` Dependency 사용
- DB 세션: `Depends(get_db)` → `AsyncSession`
- ID 채번: `await next_id("PREFIX_", db)` (PostgreSQL Sequence)
- 모든 DB 조작은 `async` / `await`

---

## 상세 가이드 (필요 시 참조)

| 작업 | 참조 문서 |
|------|----------|
| API 컨벤션 (응답 포맷, HTTP Method) | [references/api-conv.md](references/api-conv.md) — `{ header, body: { data } }` 포맷, 코드 체계 |
| 새 도메인 CRUD 구현 | [references/templates.md](references/templates.md) — Router/Service/Repository/Model/Schema 전체 템플릿 |
| ID 채번, 권한 레벨 | [references/id-auth.md](references/id-auth.md) — ID PREFIX 목록, UserRole, require_level |
| 예외 처리 | [references/exception.md](references/exception.md) — HTTPException 패턴, 공통 에러 코드 |
| 개발 체크리스트 | [references/checklist.md](references/checklist.md) — 새 도메인 개발 시 확인 사항 |
