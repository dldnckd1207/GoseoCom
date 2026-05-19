---
name: db-dev
description: Haedok AI 데이터베이스 컨벤션. 테이블/컬럼 생성·수정 시 명명 규칙, ID 전략, 공통 컬럼, Alembic 마이그레이션 규칙을 제공하는 skill. DB 작업 시 반드시 사용.
---

# Haedok AI 데이터베이스 컨벤션

> **[필수]** DB 테이블/컬럼을 생성/수정할 때 반드시 이 skill의 컨벤션을 따르세요.
> DB 환경: **PostgreSQL 16+ / SQLAlchemy 2.x / Alembic**

---

## 1. 테이블 명명 패턴

```
[모듈 3자]_[유형 1자][분류 1자]_[테이블명]
```

| 접두사 | 의미 | 용도 | 예시 |
|--------|------|------|------|
| `com_tn_` | Common Normal | 공통 마스터/업무 | `com_tn_user`, `com_tn_file` |
| `com_th_` | Common History | 공통 이력/로그 | `com_th_login_log`, `com_th_admin_audit_log` |
| `cms_tn_` | CMS Normal | 게시판 업무 | `cms_tn_board`, `cms_tn_post`, `cms_tn_comment` |
| `cms_th_` | CMS History | 게시판 이력 | `cms_th_post_history` |
| `ai_tn_` | AI Normal | AI/번역 업무 | `ai_tn_book`, `ai_tn_book_page` |
| `ai_th_` | AI History | AI/번역 이력 | `ai_th_page_revision`, `ai_th_pipeline_run` |

### 전체 테이블 목록

| 테이블명 | ID 전략 | 도메인 | Phase |
|---------|---------|--------|-------|
| `com_tn_user` | ID-Gen (`USR_`) | User | 1 |
| `com_tn_user_oauth` | ID-Gen (`OAUTH_`) | User | 1 |
| `com_tn_user_token` | ID-Gen (`UTKN_`) | User | 1 |
| `com_tn_file` | ID-Gen (`FILE_`) | File | 1 |
| `com_tn_file_map` | ID-Gen (`FMAP_`) | File | 1 |
| `com_th_login_log` | BIGSERIAL | Auth | 1 |
| `cms_tn_board` | ID-Gen (`BRD_`) | Board | 1 |
| `cms_tn_post` | ID-Gen (`POST_`) | Board | 1 |
| `cms_tn_comment` | ID-Gen (`CMT_`) | Board | 1 |
| `cms_th_post_history` | BIGSERIAL | Board | 1 |
| `ai_tn_book` | ID-Gen (`BOOK_`) | Translate | 1 |
| `ai_tn_book_page` | ID-Gen (`BPAGE_`) | Translate | 1 |
| `ai_th_page_revision` | BIGSERIAL | Translate | 2 |
| `ai_th_pipeline_run` | BIGSERIAL | Pipeline | 1 |
| `com_th_admin_audit_log` | BIGSERIAL | Admin Audit | 3 |

---

## 2. 컬럼 명명 규칙

| 규칙 | 예시 |
|------|------|
| 소문자 + snake_case | `user_id`, `board_name` |
| PK | `id` |
| FK | `{참조테이블단수}_id` | `board_id`, `user_id`, `owner_user_id` |
| 일시 접미사 `_at` | `created_at`, `deleted_at`, `left_at` |
| 여부 접미사 `_yn` | `use_yn`, `del_yn`, `notice_yn` |
| 코드 접미사 `_cd` | (현재 미사용, 필요 시 적용) |

---

## 3. ID 생성 전략

| 테이블 유형 | PK 전략 | 형식 |
|------------|---------|------|
| Normal (`_tn_`) | ID-Gen (PostgreSQL Sequence) | `{PREFIX}_{8자리}` |
| History (`_th_`) | BIGSERIAL Auto Increment | `1, 2, 3 ...` |

**ID-Gen 구현**: `app/core/common/id_generator.py`의 `next_id(prefix, db)` 함수

---

## 4. 공통 컬럼 (Mixin)

### Normal 테이블 (`tn_`) 필수

```python
# app/db/mixins.py
class TimestampMixin:
    created_at: TIMESTAMPTZ  # DEFAULT NOW()
    created_by: VARCHAR(20)  # 생성자 user_id
    updated_at: TIMESTAMPTZ  # DEFAULT NOW()
    updated_by: VARCHAR(20)  # 수정자 user_id
```

### 논리 삭제 (필요한 테이블)

```python
class SoftDeleteMixin:
    del_yn:     BOOLEAN      # DEFAULT false
    deleted_at: TIMESTAMPTZ  # nullable
    deleted_by: VARCHAR(20)  # nullable
```

### History 테이블 (`th_`) — append-only

- `TimestampMixin`, `SoftDeleteMixin` 사용 금지
- `created_at` 컬럼만 포함
- INSERT만, UPDATE/DELETE 없음

---

## 5. 기타 컨벤션

| 항목 | 규칙 |
|------|------|
| Enum 표현 | `VARCHAR(N)` (PostgreSQL ENUM 타입 미사용) |
| Boolean | `BOOLEAN`, 기본값 명시 |
| 시간대 | UTC 저장 (`TIMESTAMPTZ`), 표시 단계에서 변환 |
| JSONB | Phase 2+ 키워드/요약 등 비정형 데이터 |
| 문자열 | VARCHAR(N) — 길이 명시 필수 |
| 긴 텍스트 | `TEXT` (게시글 본문, OCR 결과 등) |
| 인덱스 | `ix_` 접두사, FK 컬럼은 반드시 인덱스 |

---

## 참조 문서

- `references/sql-templates.md` — SQLAlchemy 모델 + DDL 템플릿
- `references/migration.md` — Alembic 마이그레이션 규칙
- `references/checklist.md` — 사전 체크리스트
