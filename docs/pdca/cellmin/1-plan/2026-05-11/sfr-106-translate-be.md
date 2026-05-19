---
feature: sfr-106-translate-be
date: 2026-05-11
updated: 2026-05-14
author: cellmin
phase: plan
---

# Plan — SFR-106 고서 번역기 BE (이미지 1장)

## 1. 목표 및 범위

고서 이미지 1장을 업로드하면 OCR → 번역까지 자동으로 처리하는 백엔드 파이프라인을 구현한다.
사용자는 202 응답으로 즉시 book_id를 받고, 이후 폴링으로 결과를 조회한다.

**포함:**
- POST `/api/v1/uploads` — 일반 파일 업로드 (SRS §3.4, 신규 구현)
- POST `/api/v1/translate` — file_id 기반 번역 파이프라인 시작 (202)
- GET `/api/v1/translate/{book_id}` — 상태/결과 조회
- POST `/api/v1/translate/list` — 내 번역 목록 (페이지네이션 + status 필터)
- OCR: Google Vision API
- 번역: Gemini Flash (`gemini-2.5-flash`)
- 파일 저장: 기존 `FileService` 재사용 (`settings.file_local_path` 기준)
- 비동기 실행: FastAPI BackgroundTasks

**미포함 (Phase 2):**
- PDF 다중 페이지 처리
- PaddleOCR
- S3 파일 저장
- 즐겨찾기, 공유 토큰, 요약/키워드

## 2. 대상 사용자

USER 권한 이상의 로그인 사용자. 본인이 생성한 Book만 조회 가능.

## 3. 핵심 요구사항

| ID | 요구사항 |
|----|---------|
| TBR-01 | USER 이상 권한만 번역 요청 가능 |
| TBR-02 | 번역 요청 대상 파일은 image/* 전용, 최대 10MB. 위반 시 400 반환 (`POST /api/v1/uploads`는 타입 무관 범용 업로드) |
| TBR-06 | 결과/목록 조회는 본인 소유 Book만 허용 |
| TBR-07 | BackgroundTask로 비동기 실행, 202 즉시 반환 |
| TBR-08 | 파이프라인 실행 이력을 ai_th_pipeline_run에 기록 |

## 4. 비즈니스 규칙

- `book.owner_user_id == payload["sub"]` 소유권 검증
- BackgroundTask runner는 `book_id`, `file_local_path`, `pipeline_run_id`만 받고, 내부에서 새 `AsyncSession`을 생성한다 (요청 스코프 세션 재사용 금지)
- 파일 업로드는 `POST /api/v1/uploads`로 선행 후 반환된 `file_id`로 번역 요청
- `file_id`로 `FileRepository`에서 `File` 조회 → 소유권(`created_by == payload["sub"]`), MIME(`image/*`), 크기(10MB) 재검증
- `File.local_path`를 runner에 전달
- 파이프라인 실패 시 `book.status = FAILED`, `pipeline_run_id`로 대상 `PipelineRun` row를 조회해 `error_msg` 저장
- 번역 결과: `literal_text` (직역) + `interpretive_text` (의역) 분리 저장
- OCR 텍스트가 없으면 번역 건너뜀 → `book.status = COMPLETED`, `book_page.status = NO_TEXT`
- 외부 API 키 미설정 시 `book.status = FAILED`, `pipeline_run.error_msg`에 설정 오류 기록
- 업로드 API 크기 초과: `400 FILE_SIZE_EXCEEDED` (범용 업로드, 타입 미검증)
- 번역 요청 시 이미지 아닌 파일: `400 INVALID_IMAGE_TYPE`
- 번역 요청 시 크기 초과: `400 IMAGE_SIZE_EXCEEDED`

## 5. 성공 기준

- [ ] POST /api/v1/uploads → file_id 반환
- [ ] POST /api/v1/translate (file_id) → 202 반환, book_id 포함
- [ ] BackgroundTask에서 OCR → 번역 완료 후 book.status = COMPLETED
- [ ] GET /api/v1/translate/{book_id} → 상태 및 번역 결과 반환
- [ ] POST /api/v1/translate/list → 페이지네이션 목록 반환 (status 필터 동작)
- [ ] 타인 book_id 조회 시 403 반환
- [ ] 이미지 아닌 파일로 번역 요청 시 400 반환
- [ ] 타인 file_id로 번역 요청 시 403 반환
- [ ] 10MB 초과 file_id로 번역 요청 시 400 반환
- [ ] 파이프라인 실패 시 FAILED 상태 + 에러 메시지 기록
- [ ] OCR 텍스트 없음 시 COMPLETED + page.status = NO_TEXT
- [ ] lint(ruff) + type check(mypy) 통과
- [ ] 기존 DB/시퀀스 상태 확인 완료 (ai_tn_book, seq_book 등 이미 존재)
