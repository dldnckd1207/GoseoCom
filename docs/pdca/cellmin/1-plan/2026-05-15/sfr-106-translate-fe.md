# Plan: 고서 번역기 FE — API 연동 (sfr-106-translate-fe)

**작성자**: cellmin  
**날짜**: 2026-05-15  
**관련 이슈**: Redmine #106 (FE)  
**연관 완료**: sfr-106-translate-be (91.0점, archive)

---

## 1. 배경 및 목표

sfr-106-translate-be(BE) 완료에 따라 `/translate` 페이지를 실제 API와 연동한다.  
현재 TranslateView는 전체 placeholder 상태 ("서비스 준비 중" 모달).  
이미지 업로드 → 번역 시작 → 폴링 → 결과 표시까지 전체 플로우를 구현한다.

번역 목록(`POST /api/v1/translate/list`)은 #101 라이브러리에서 처리 — 이번 범위 제외.

---

## 2. 연동 API

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/api/v1/uploads` | 이미지 파일 업로드 → `file_id` 반환 |
| POST | `/api/v1/translate` | `file_id` 전달 → 202 + `book_id` |
| GET | `/api/v1/translate/{book_id}` | 상태/결과 폴링 |

**Book 상태값**: `PENDING` → `OCR_PROCESSING` → `TRANSLATING` → `COMPLETED` / `FAILED`  
**Page 상태값**: `PENDING` / `COMPLETED` / `NO_TEXT` / `FAILED`  
> `NO_TEXT`는 Book이 아닌 Page 상태. Book은 항상 `COMPLETED`로 종료되며, `pages.some(p => p.status === 'NO_TEXT')`로 감지.

**결과 필드**: `literal_text` (직역), `interpretive_text` (의역)

---

## 3. 요구사항

### 기능 요구사항

| # | 항목 | 설명 |
|---|------|------|
| F-1 | 이미지 업로드 | `image/*` 파일 선택 → `POST /api/v1/uploads` → `file_id` 획득 |
| F-2 | 번역 시작 | `file_id`로 `POST /api/v1/translate` → `book_id` 획득 |
| F-3 | 폴링 | `GET /api/v1/translate/{book_id}` 3초 간격, Book `COMPLETED`/`FAILED` 시 중단 |
| F-4 | 결과 표시 | `literal_text`(직역) + `interpretive_text`(의역) 구분 표시 |
| F-5 | 진행 상태 표시 | 업로드 중 / 이미지 인식 중(`OCR_PROCESSING`) / 번역 중(`TRANSLATING`) / 완료 / 실패 상태를 UI로 표현 |
| F-6 | 에러/안내 처리 | 업로드 실패, 번역 실패(`book.status=FAILED`), OCR 텍스트 없음(`page.status=NO_TEXT`) 각 케이스 안내 |
| F-7 | 재시도 | 번역 완료 후 새 이미지로 다시 번역 가능 |

### 비기능 요구사항

| # | 항목 |
|---|------|
| N-1 | `npm run lint` + `npm run typecheck` 통과 |
| N-2 | 이미지 아닌 파일 및 10MB 초과 파일은 클라이언트에서 사전 차단 (`accept="image/*"` + `file.type` + `file.size` 검사) |
| N-3 | 폴링은 컴포넌트 언마운트 시 자동 중단 |
| N-4 | 업로드/번역 진행 중 중복 제출 방지 |

### 제외 범위

- 텍스트 직접 입력 번역 (BE API 미지원) — 기존 textarea 및 관련 문구 제거
- PDF 파일 지원 문구 — 제거 (이미지 전용)
- 다운로드 기능 — Phase 2 (버튼 숨김 처리)
- 번역 목록 / 이력 — #101 라이브러리에서 처리

---

## 4. 변경 파일 (예상)

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `apps/client/app/routes/_protected.translate.tsx` | 수정 | loader 제거 불필요, action 추가 검토 |
| `apps/client/app/views/translate/TranslateView.tsx` | 수정 | placeholder → 실제 업로드/폴링/결과 구현 |
| `apps/client/app/shared/api/endpoints.ts` | 수정 | UPLOADS, TRANSLATE, TRANSLATE_DETAIL 엔드포인트 추가 |
| `apps/client/app/shared/types/translate.ts` | 신규 | Book, TranslateResult 타입 |

---

## 5. 성공 기준

- [ ] 이미지 파일 선택 → 업로드 → 번역 시작 → 폴링 → 결과 표시 전체 플로우 동작
- [ ] 직역 / 의역 구분 표시
- [ ] 번역 중 스피너/상태 메시지 표시
- [ ] FAILED 시 에러 메시지 표시
- [ ] NO_TEXT 시 안내 메시지 표시
- [ ] 컴포넌트 언마운트 시 폴링 중단 (메모리 누수 없음)
- [ ] 이미지 아닌 파일 및 10MB 초과 파일 사전 차단
- [ ] 번역 완료 후 새 이미지로 재번역 가능
- [ ] `npm run lint` + `npm run typecheck` 통과
