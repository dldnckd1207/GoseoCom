# DB 사전 체크리스트

새 테이블을 생성하거나 컬럼을 추가/수정할 때 확인합니다.

---

## 새 테이블 생성 시

- [ ] 모듈/분류 결정 → 테이블명 확정 (`com_tn_` / `cms_tn_` / `ai_tn_` / `com_th_` / `cms_th_` / `ai_th_`)
- [ ] ID 전략 결정 → Normal(`_tn_`): ID-Gen, History(`_th_`): BIGSERIAL
- [ ] Normal 테이블: `TimestampMixin` 상속 확인
- [ ] 논리 삭제 필요 여부 → `SoftDeleteMixin` 상속 여부 결정
- [ ] History 테이블: append-only 확인 (UPDATE/DELETE 없음)
- [ ] 인덱스 정의 (`__table_args__`)
- [ ] FK 삭제 정책 확인 (RESTRICT / CASCADE / SET NULL)
- [ ] ID-Gen 테이블이면: PostgreSQL Sequence 등록 (`seq_{name}`)
- [ ] `id_generator.py`의 `_SEQ_MAP`에 PREFIX 추가
- [ ] `alembic/env.py`에서 모델 import 확인
- [ ] Alembic 마이그레이션 파일 생성 및 검토

---

## 컬럼 추가/수정 시

- [ ] 컬럼명 규칙 준수 (snake_case, `_at`/`_yn`/`_cd` 접미사)
- [ ] `NOT NULL` 컬럼 추가 시 기존 데이터 DEFAULT 값 설정
- [ ] 인덱스 필요 여부 검토 (검색/조회 조건으로 사용되는 컬럼)
- [ ] Alembic `upgrade()` + `downgrade()` 모두 작성

---

## ERD 도메인별 확인 사항

| 도메인 | 모듈 | 테이블 접두사 | 주요 확인 |
|--------|------|-------------|----------|
| User | `core/user/` | `com_tn_` | AI 시드 계정 `USR_00000000` 보호 |
| File | `core/files/` | `com_tn_` | `target_type` 다형 매핑 (FK 없음) |
| Auth | `auth/` | `com_th_` | LoginLog append-only |
| Board | `board/` | `cms_tn_`, `cms_th_` | `comment_count` 캐시 컬럼 동기화 |
| Translate | `translate/` | `ai_tn_`, `ai_th_` | `PageRevision` append-only (Phase 2) |
| Pipeline | `translate/pipeline/` | `ai_th_` | append-only |
| Admin Audit | `core/audit/` | `com_th_` | Phase 1 선반영, Phase 3 INSERT 시작 |

---

## Phase별 스키마 확인

| Phase | 상태 | 포함 테이블 |
|-------|------|------------|
| 1 | 완료 | 전체 15개 테이블 생성 완료 (`2227df8fb0d6`) |
| 2 | 예정 | `ai_th_page_revision` INSERT 시작, `share_token` 활용 |
| 3 | 예정 | `com_th_admin_audit_log` INSERT 시작, `apps/admin` 구현 |
