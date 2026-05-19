# sfr-107-library-fe Plan 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/1-plan/2026-05-15/sfr-107-library-fe.md` |
| 기준 문서/코드 | `docs/pdca/cellmin/4-reports/2026-05-14/sfr-106-translate-be.md`, `apps/server/app/translate/*`, `apps/client/app/shared/api/*`, `apps/client/app/routes/_protected.tsx` |
| 리뷰 일자 | 2026-05-15 |

## 총평

Plan은 로그인 사용자의 번역 이력 목록과 상세 결과 조회 범위를 명확히 잡고 있다. `/library`와 `/library/:id`를 `_protected` 하위 라우트로 구현하는 방향도 현재 클라이언트 구조와 맞다.

다만 진행중 탭 요구사항은 현재 BE 목록 API가 단일 `status` 필터만 받는다는 제약과 충돌한다. 또한 FAILED 상태의 오류 메시지는 현재 상세 응답에 별도 오류 필드가 없어 구체 메시지 표시가 불가능하다. 구현 전에 이 두 지점을 명확히 정리하는 것이 좋다.

## Findings

### High - 진행중 탭의 복수 상태 필터가 현재 BE API와 맞지 않음

Plan은 진행중 탭을 `PENDING + OCR_PROCESSING + TRANSLATING` 묶음으로 정의한다.

하지만 실제 BE `BookListRequest.status`는 단일 `BookStatus | None`만 받는다. `POST /api/v1/translate/list` 한 번으로 세 상태를 동시에 요청할 수 없다.

영향:
- `status=PENDING`만 사용하면 `OCR_PROCESSING`, `TRANSLATING` 상태 항목이 진행중 탭에서 누락된다.
- FE에서 세 번 요청해 합치면 페이지네이션의 `total`, `page`, 정렬 기준이 불명확해진다.
- 구현자가 "복수 요청 또는 BE 단일 필터" 중 임의 선택을 하게 되어 Plan 성공 기준이 흔들릴 수 있다.

권장 수정:
- Phase 1에서 정확한 진행중 탭이 필요하면 BE에 다중 status 필터를 추가한다.
- BE 변경 없이 진행한다면 Plan에 `진행중 = PENDING만 표시`라고 명시하고 누락 가능성을 수용한다.
- 또는 탭을 `전체 / 완료 / 실패 / 대기중`처럼 단일 status 기준으로 재정의한다.

### Medium - FAILED 오류 메시지 표시 요구사항은 현재 응답 필드만으로 충족 불가

Plan은 `/library/:id`에서 `FAILED` 상태 시 오류 메시지를 표시한다고 정의한다.

현재 BE `BookResponse`에는 다음 필드만 있다.

```ts
book_id
title
status
total_pages
pages
```

실패 사유나 오류 메시지 필드는 없다. 따라서 FE는 "번역 처리 중 오류가 발생했습니다" 같은 일반 메시지만 표시할 수 있다.

권장 수정:
- Plan에 "구체 실패 사유가 아닌 일반 안내 메시지 표시"라고 명시한다.
- 구체 오류가 필요하면 BE `BookResponse`에 `error_message` 또는 pipeline run 오류 요약 필드를 추가하는 별도 범위가 필요하다.

### Medium - 상세 페이지의 페이지 정렬 기준 명시 필요

Plan은 페이지별 OCR 원문 / 직역 / 의역 표시를 요구하지만, 정렬 기준을 명시하지 않는다.

BE repository는 `selectinload(Book.pages)`로 pages를 로드한다. 관계 정의에 order가 없다면 응답 배열 순서가 항상 `page_no` 오름차순이라고 보장하기 어렵다.

권장 수정:
- FE에서 `pages`를 `page_no` 오름차순으로 정렬해 표시한다고 Plan에 명시한다.
- 또는 BE 관계/쿼리에서 page ordering을 보장한다고 명시한다.

### Low - 비로그인 리다이렉트 성공 기준 표현 보정 필요

Plan은 비로그인 시 `/login`으로 리다이렉트한다고 적는다.

현재 `_protected` 레이아웃은 loader에서 `redirectTo` 값을 반환한 뒤, 클라이언트에서 로그인 필요 모달을 띄우고 확인 시 `navigate(..., { replace: true })`로 이동한다. 즉 서버 loader의 즉시 `throw redirect()` 방식은 아니다.

권장 수정:
- 성공 기준을 "비로그인 시 로그인 필요 안내 후 `/login?redirect=/library`로 이동"으로 구체화한다.

## 권장 Plan 보정안

```md
### /library (목록)
2. 상태 탭 필터: 전체 / 완료 / 진행중
   - 전체: 필터 없음
   - 완료: status=COMPLETED
   - 진행중:
     - Phase 1 선택지 A: BE 다중 status 필터 추가 후 PENDING/OCR_PROCESSING/TRANSLATING 조회
     - Phase 1 선택지 B: BE 변경 없이 status=PENDING만 조회하며, 처리 중 상태 누락 가능성을 허용

### /library/:id (상세)
4. FAILED 상태 시 일반 오류 안내 메시지 표시
5. pages는 page_no 오름차순으로 표시

### 성공 기준
- [ ] 비로그인 시 로그인 필요 안내 후 /login?redirect=/library 로 이동
```

## 결론

Plan의 라우트와 API 방향은 적절하다. 구현 전에 진행중 탭의 정확도와 BE 변경 여부를 결정하고, FAILED 메시지의 수준을 "일반 안내"로 제한하면 구현 혼선을 줄일 수 있다.
