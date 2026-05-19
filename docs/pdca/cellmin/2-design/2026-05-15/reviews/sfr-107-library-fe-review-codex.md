# sfr-107-library-fe Design 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/2-design/2026-05-15/sfr-107-library-fe.md` |
| 기준 Plan | `docs/pdca/cellmin/1-plan/2026-05-15/sfr-107-library-fe.md` |
| 기준 코드 | `apps/client/app/routes/_protected.tsx`, `apps/client/app/views/community/CommunityListView.tsx`, `apps/client/app/shared/api/endpoints.ts`, `apps/server/app/translate/router.py`, `apps/server/app/translate/schemas.py`, `apps/server/app/translate/repository.py` |
| 리뷰 일자 | 2026-05-15 |

## 총평

Design은 현재 React Router 라우트 구성과 `serverFetch` 기반 loader 패턴을 잘 따른다. 파일 구조, 타입 정의, endpoint 추가 방향도 적절하며, `CommunityListView`의 탭과 페이지네이션 패턴을 재사용하려는 접근도 무난하다.

다만 진행중 탭을 `status=PENDING`으로 단순화한 결정은 Plan의 "PENDING + OCR_PROCESSING + TRANSLATING" 요구사항과 다르다. 또한 `API_ENDPOINTS`는 이미 현재 코드에 추가되어 있어 신규 작업 범위에서 제외해도 된다. 상세 뷰에서는 페이지 정렬과 null 텍스트 표시 정책을 추가로 정의하는 편이 안전하다.

## Findings

### High - 진행중 탭 설계가 Plan 요구사항을 축소함

Design은 진행중 탭을 `status=PENDING`으로 요청한다고 정의한다.

하지만 Plan의 진행중 탭은 `PENDING + OCR_PROCESSING + TRANSLATING` 묶음이다. 실제 BE가 단일 status만 허용한다는 제약은 맞지만, `PENDING`만 조회하면 이미 OCR 또는 번역 단계로 넘어간 항목은 진행중 탭에서 사라진다.

영향:
- 사용자가 방금 시작한 번역이 상태 전환 후 진행중 탭에서 보이지 않을 수 있다.
- "진행중"이라는 탭 이름과 실제 조회 결과가 다르다.
- Plan 성공 기준의 "status 필터 적용되어 목록 갱신"은 통과해도 사용자 관점의 진행중 목록은 불완전하다.

권장 수정:
- Design에 명시적으로 "Phase 1에서는 `PENDING`만 표시"라고 쓰고 UX 한계를 적는다.
- 정확한 진행중 탭이 필요하면 BE `BookListRequest`를 `statuses: BookStatus[]` 형태로 확장하는 설계를 추가한다.
- FE 복수 요청 병합은 페이지네이션과 total 산정이 깨지기 쉬우므로 권장하지 않는다.

### Medium - `API_ENDPOINTS` 추가 항목은 현재 코드에 이미 존재함

Design은 `shared/api/endpoints.ts`에 `TRANSLATE_LIST`, `TRANSLATE_DETAIL`을 추가한다고 적는다.

현재 코드에는 이미 다음 항목이 있다.

```ts
TRANSLATE_LIST: '/api/v1/translate/list',
TRANSLATE_DETAIL: (id: string) => `/api/v1/translate/${id}`,
```

권장 수정:
- 파일 구조의 `endpoints.ts` 항목을 "확인 또는 기존 항목 사용"으로 변경한다.
- 실제 구현 범위는 `shared/types/translate.ts`, 라우트 2개, view 2개로 좁힌다.

### Medium - 상세 pages 정렬을 FE에서 보장해야 함

Design은 상세 loader가 `BookDetail`을 그대로 반환하고, View가 페이지별 섹션을 렌더링한다고 되어 있다.

현재 BE `get_by_id_with_pages()`는 `selectinload(Book.pages)`를 사용한다. relationship 또는 query order가 명시되어 있지 않다면 pages 배열 순서를 API 계약으로 보기 어렵다.

권장 수정:

```ts
const pages = [...book.pages].sort((a, b) => a.page_no - b.page_no);
```

또는 BE에서 `page_no` ordering을 보장하는 것으로 설계를 보강한다. FE 구현만으로 닫으려면 View에서 정렬하는 편이 가장 작다.

### Medium - null 텍스트 표시 정책이 필요함

`BookPage` 타입은 `ocr_text`, `literal_text`, `interpretive_text`를 `string | null`로 정의한다. 진행중, 실패, `NO_TEXT` 페이지에서는 null이 정상적으로 올 수 있다.

권장 보강:
- null 또는 빈 문자열이면 `아직 결과가 없습니다.` 같은 placeholder를 표시한다.
- `page.status === 'NO_TEXT'`일 때 OCR 영역에 "인식된 텍스트가 없습니다."를 표시한다.
- `book.status`가 진행중이면 상세 페이지에서도 아직 처리 중임을 표시한다.

### Low - BookPage status 타입을 좁히면 UI 분기가 안정적임

Design의 `BookPage.status`는 `string`이다. 실제 BE 주석상 page status는 `PENDING | COMPLETED | NO_TEXT | FAILED`다.

권장 타입:

```ts
export type BookPageStatus = 'PENDING' | 'COMPLETED' | 'NO_TEXT' | 'FAILED';

export interface BookPage {
    page_no: number;
    ocr_text: string | null;
    literal_text: string | null;
    interpretive_text: string | null;
    status: BookPageStatus;
}
```

### Low - 페이지네이션 URL 정규화 규칙을 명시하면 기존 패턴과 맞음

`CommunityListView`는 invalid tab 또는 page 초과 시 URL을 정규화한다. Library도 같은 사용자 경험을 제공하려면 Design에 다음 규칙을 추가할 수 있다.

- 알 수 없는 `tab`은 `all`로 fallback하고 URL에서 제거
- `page > totalPages`이면 마지막 페이지로 replace
- 탭 변경 시 `page` query 제거

## 권장 Design 보정안

1. 진행중 탭 정책을 Plan과 맞춘다. 정확한 진행중 목록이 필요하면 BE 다중 status 필터를 추가한다.
2. `endpoints.ts`는 이미 추가된 항목 사용으로 정리한다.
3. 상세 페이지 렌더링 전 `pages`를 `page_no` 오름차순 정렬한다.
4. `BookPageStatus` union type을 추가한다.
5. null 텍스트, `NO_TEXT`, 진행중 상세 상태의 표시 문구를 정의한다.
6. Library 목록도 Community 목록처럼 invalid query 정규화 규칙을 둔다.

## 결론

Design의 큰 구조는 현재 코드베이스와 잘 맞는다. 구현 전에 진행중 탭의 의미를 확정하고, 상세 페이지의 pages 정렬과 null 결과 표시를 보강하면 SFR-107 구현 기준으로 충분히 안정적이다.
