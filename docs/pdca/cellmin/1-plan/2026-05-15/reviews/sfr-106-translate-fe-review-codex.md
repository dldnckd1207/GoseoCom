# sfr-106-translate-fe Plan 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/1-plan/2026-05-15/sfr-106-translate-fe.md` |
| 기준 문서/코드 | `docs/pdca/cellmin/4-reports/2026-05-14/sfr-106-translate-be.md`, `apps/server/app/translate/*`, `apps/client/app/shared/api/*`, `apps/client/app/views/translate/TranslateView.tsx` |
| 리뷰 일자 | 2026-05-15 |

## 총평

Plan은 `/translate` placeholder를 실제 API 플로우로 전환하는 범위를 명확히 잡고 있다. 업로드, 번역 시작, 상태 폴링, 결과 표시를 Phase 1 범위로 제한한 점도 BE 완료 범위와 대체로 맞다.

다만 BE의 실제 상태 모델과 Plan의 상태 정의가 일부 다르다. 특히 `NO_TEXT`는 Book 상태가 아니라 BookPage 상태로 반환되며, Book 자체는 `COMPLETED`가 된다. 이 부분을 보정하지 않으면 FE 구현자가 폴링 종료 조건과 안내 메시지 조건을 잘못 잡을 수 있다.

## Findings

### High - `NO_TEXT` 상태 위치가 실제 BE 응답과 다름

Plan은 번역 상태값을 `PENDING -> PROCESSING -> COMPLETED / FAILED / NO_TEXT`로 정의하고, F-3/F-6/성공 기준에서도 `NO_TEXT`를 번역 상태처럼 다룬다.

하지만 실제 BE pipeline은 OCR 텍스트가 없을 때 `page.status = "NO_TEXT"`로 저장하고 `book.status = "COMPLETED"`로 완료 처리한다.

영향:
- FE가 `book.status === "NO_TEXT"`를 기다리면 해당 분기가 실행되지 않는다.
- 텍스트 없음 케이스가 일반 완료 화면으로 떨어질 수 있다.
- 성공 기준의 `NO_TEXT 시 안내 메시지 표시` 조건을 구현자가 잘못 해석할 수 있다.

권장 수정:
- Book 상태값: `PENDING`, `OCR_PROCESSING`, `TRANSLATING`, `COMPLETED`, `FAILED`
- Page 상태값: `PENDING`, `COMPLETED`, `NO_TEXT`, `FAILED`
- `NO_TEXT` 안내 조건: `book.status === "COMPLETED"` 이후 `pages.some((page) => page.status === "NO_TEXT")`

### Medium - `PROCESSING` 상태명이 BE와 맞지 않음

Plan의 상태값에는 `PROCESSING`이 있으나 실제 BE Book 상태는 `OCR_PROCESSING`, `TRANSLATING`으로 단계가 나뉜다.

권장 수정:
- `PROCESSING` 대신 `OCR_PROCESSING` / `TRANSLATING`을 명시
- UI 상태는 두 상태를 모두 "번역 중" 또는 "이미지 인식 중/번역 중"으로 매핑한다고 적기

### Medium - 클라이언트 파일 검증 기준 보강 필요

Plan은 이미지 아닌 파일 선택을 `accept="image/*"`로 사전 차단한다고 정의한다. 그러나 `accept`는 브라우저 파일 선택 UI 힌트에 가깝고, 클라이언트 검증을 완전히 보장하지 않는다.

BE는 번역 요청 시 image MIME과 10MB 제한을 재검증한다. FE도 사용자 경험을 위해 동일 기준을 사전 검증하는 편이 좋다.

권장 수정:
- `file.type.startsWith("image/")` 검사 추가
- `file.size <= 10 * 1024 * 1024` 검사 추가
- 실패 시 API 호출 전 안내 메시지 표시

### Low - 기존 placeholder 문구와 제외 범위 충돌 가능

현재 `TranslateView`에는 텍스트 직접 입력, PDF 지원, 다운로드 문구가 보인다. Plan의 제외 범위는 텍스트 직접 입력과 다운로드를 제외하고, BE 번역 요청도 image 전용이다.

권장 수정:
- 이번 구현에서 직접 입력 textarea 제거 또는 명확히 비활성화
- "PDF 파일 지원" 문구 제거
- 다운로드 버튼/문구는 Phase 2로 숨김 처리

## 권장 Plan 보정안

```md
**Book 상태값**: `PENDING` -> `OCR_PROCESSING` -> `TRANSLATING` -> `COMPLETED` / `FAILED`
**Page 상태값**: `PENDING` / `COMPLETED` / `NO_TEXT` / `FAILED`

F-3 | 폴링 | `GET /api/v1/translate/{book_id}` 3초 간격, Book `COMPLETED`/`FAILED` 시 중단
F-6 | 에러/안내 처리 | 업로드 실패, 번역 실패(`book.status=FAILED`), OCR 텍스트 없음(`page.status=NO_TEXT`) 각 케이스 안내
N-2 | 이미지 아닌 파일 및 10MB 초과 파일은 클라이언트에서 사전 차단
```

## 결론

Plan의 범위와 API 방향은 적절하다. 구현 전에 상태값 정의와 `NO_TEXT` 처리 위치를 BE 기준으로 보정하면, Design과 구현의 혼선을 줄일 수 있다.
