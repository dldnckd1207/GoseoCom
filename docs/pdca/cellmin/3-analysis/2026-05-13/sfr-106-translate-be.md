---
feature: sfr-106-translate-be
date: 2026-05-13
author: cellmin
phase: check
iteration: 1
---

# Check 분석 — SFR-106 고서 번역기 BE

## 종합 점수: 64.2 / 100 (보통)

| 영역 | 비중 | 점수 | 가중 점수 |
|------|------|------|-----------|
| 기능 완성도 | 20% | 88 | 17.6 |
| 코드 품질 | 20% | 82 | 16.4 |
| **테스트** | 20% | **0** | **0.0** |
| 보안 | 20% | 75 | 15.0 |
| 성능 | 10% | 80 | 8.0 |
| 문서화 | 10% | 72 | 7.2 |
| **합계** | | | **64.2** |

> 주요 이슈가 있습니다. `/pdca act`로 개선이 필요합니다.

---

## 1. 기능 완성도 (88/100)

### ✅ 달성된 성공 기준

- POST /api/v1/translate → 202 반환, book_id 포함
- BackgroundTask OCR → 번역 완료 후 book.status = COMPLETED
- GET /api/v1/translate/{book_id} → 상태/결과 반환
- 타인 book_id 조회 시 403
- image/* 외 파일 400, 파이프라인 실패 FAILED 기록
- OCR 텍스트 없음 → COMPLETED + page.status = NO_TEXT
- lint(ruff), mypy 통과, DB/시퀀스 확인 완료

### ⚠️ Minor 이슈

- **목록 API 경로 불일치**: Plan에 `GET /api/v1/translate`로 정의했으나 실제 구현은 `POST /api/v1/translate/list` (server-dev 컨벤션 준수, 의도적 변경이지만 Plan 문서 미업데이트)
- **외부 의존성 변경 미반영**: Design §11에 `google-generativeai`로 표기되어 있으나 실제로는 `google-genai`로 교체됨

---

## 2. 코드 품질 (82/100)

### ✅ 양호

- Router → Service → Repository 레이어 분리 명확
- 기존 프로젝트 패턴 (require_level, ApiResponse, PageData) 일관 적용
- `validation_alias="id"`로 ORM `id` → API `book_id` 변환 처리
- runner 내 독립 AsyncSession 생성 (요청 스코프 세션 미재사용)
- 예외 처리 안전 (`db.rollback()` in inner try)

### ⚠️ 이슈

- **이중 커밋 흐름**: `FileService.upload()`가 내부에서 `db.commit()`을 호출한 뒤, `TranslateService.start_translate()`도 `db.commit()` 호출. 파일 저장 성공 후 Book 생성 실패 시 orphan File row가 남을 수 있음 (Phase 1 허용 범위이나 Phase 2 이전 개선 권장)
- **`no_text` 케이스에서 `page.updated_by` 미설정**: runner의 `NO_TEXT` 브랜치에서 `page.updated_by = ai_user`가 누락됨

---

## 3. 테스트 (0/100) ← 주요 이슈

테스트 파일이 전혀 작성되지 않았습니다.

Design에서 명시한 테스트 전략:
- [ ] `run_pipeline()` 단위 테스트 (OCR/번역 mock)
- [ ] 정상 흐름: COMPLETED
- [ ] OCR 빈 텍스트: COMPLETED + NO_TEXT
- [ ] OCR 예외: FAILED
- [ ] Gemini 예외/파싱 실패: FAILED
- [ ] POST → 202 API 테스트
- [ ] 타인 book_id → 403
- [ ] 잘못된 파일 타입 → 400

---

## 4. 보안 (75/100)

### ✅ 양호

- `require_level(UserRole.USER)` 인증 강제
- `owner_user_id == payload["sub"]` 소유권 검증
- MIME 타입 검증 (`content_type.startswith("image/")`)
- 파일 크기 10MB 제한
- error_stack DB에만 저장, 클라이언트에 미노출

### ⚠️ 이슈

- **파일 시그니처 검증 없음**: `Content-Type` 헤더만 확인하므로 공격자가 헤더를 `image/jpeg`로 조작해 임의 파일 업로드 가능. magic bytes 검증 부재 (Phase 1 허용이나 프로덕션 전 보완 권장)

---

## 5. 성능 (80/100)

### ✅ 양호

- BackgroundTask 비동기 처리로 202 즉시 반환
- `asyncio.to_thread()` 동기 라이브러리 안전 호출
- `selectinload(Book.pages)` N+1 문제 없음
- 목록 쿼리 subquery 카운트 패턴 정상

### ⚠️ Minor

- 파일 내용 두 번 읽기: 검증(`image.read()`) + FileService(`file.read()`) → `seek(0)` 재읽기. 10MB 한도 내 허용 범위
- Gemini client 매 호출마다 `genai.Client()` 새 인스턴스 생성 → Phase 2에서 싱글톤/풀 고려

---

## 6. 문서화 (72/100)

### ✅ 양호

- Router summary/description 있음
- Plan/Design 문서 상세히 작성됨
- 에러 코드 명시적

### ⚠️ 이슈

- Design §11 외부 의존성: `google-generativeai` → `google-genai` 미업데이트
- Plan 목록 API 경로: `GET /api/v1/translate` → `POST /api/v1/translate/list` 미반영
- `BookListRequest.status` 타입: Design은 `str | None`, 실제 구현은 `Literal[...] | None` (구현이 더 좋으나 문서 불일치)

---

## Act 우선순위

| 순위 | 영역 | 작업 |
|------|------|------|
| 1 | **테스트** | runner 단위 테스트 + API 테스트 작성 |
| 2 | **코드 품질** | runner NO_TEXT 브랜치 `page.updated_by` 누락 수정 |
| 3 | **문서화** | Plan/Design 문서 불일치 항목 업데이트 |
| 4 | **보안** | 파일 시그니처(magic bytes) 검증 추가 (프로덕션 전) |
