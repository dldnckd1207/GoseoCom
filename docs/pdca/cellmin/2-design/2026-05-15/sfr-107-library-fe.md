# Design: SFR-107 고서 목록 페이지 FE (/library)

**Date:** 2026-05-15

---

## 1. 파일 구조

```
apps/client/app/
├── routes/
│   ├── _protected.library.tsx           # 목록 라우트 (loader + meta)
│   └── _protected.library.$id.tsx      # 상세 라우트 (loader + meta)
├── views/
│   └── library/
│       ├── LibraryView.tsx              # 목록 뷰
│       └── LibraryDetailView.tsx        # 상세 뷰
└── shared/
    ├── api/endpoints.ts                 # TRANSLATE_LIST, TRANSLATE_DETAIL (기존 항목 사용)
    └── types/translate.ts               # BookListItem 추가 (BookResult, BookPageResult, BookPageStatus 기존 사용)
```

---

## 2. 타입 정의 (shared/types/translate.ts)

```ts
// 신규 추가
export type BookListItem = {
    book_id: string;
    title: string;
    status: BookStatus;
    created_at: string;
};

// 기존 타입 그대로 사용
// BookStatus, BookPageStatus, BookPageResult, BookResult — translate.ts에 이미 존재
// BookPageResult.status: BookPageStatus ('PENDING' | 'COMPLETED' | 'NO_TEXT' | 'FAILED')
```

---

## 3. API 엔드포인트

```ts
// endpoints.ts — 이미 존재하는 항목 사용
TRANSLATE_LIST: '/api/v1/translate/list',
TRANSLATE_DETAIL: (id: string) => `/api/v1/translate/${id}`,
```

---

## 4. 탭 → status 매핑

| 탭 | URL param | status 파라미터 |
|----|-----------|----------------|
| 전체 | (없음) | (없음) |
| 완료 | `completed` | `COMPLETED` |
| 대기중 | `pending` | `PENDING` |
| 실패 | `failed` | `FAILED` |

> OCR_PROCESSING / TRANSLATING은 짧은 전환 상태로 "전체" 탭에서만 노출됨.
> BE API가 단일 status만 허용하므로 FE에서 1:1 매핑으로 처리.

---

## 5. 라우트 로직

### _protected.library.tsx
```ts
loader:
  - url.searchParams.get('tab') → 'all' | 'completed' | 'pending' | 'failed'
  - url.searchParams.get('page') → 숫자
  - tab 기반 status 결정
  - POST /api/v1/translate/list → items, total, page, size
  - return { items, total, page, size, currentTab }
```

### _protected.library.$id.tsx
```ts
loader:
  - params.id → book_id
  - GET /api/v1/translate/:id → BookDetail
  - return { book }
```

---

## 6. 뷰 컴포넌트 설계

### LibraryView
- 페이지 헤더 + 새 번역 버튼 (Link to /translate)
- 탭 (전체 / 완료 / 대기중 / 실패) — CommunityListView 탭 패턴 동일
- 목록 카드 (title, status badge, created_at)
- 페이지네이션 — CommunityListView 패턴 동일

### LibraryDetailView
- 뒤로가기 버튼 (Link to /library)
- 책 제목 + 상태 badge + 전체 페이지 수
- pages → page_no 오름차순 정렬 후 렌더링
- 페이지별 섹션: OCR 원문 / 직역 / 의역 3열 (모바일: 세로 스택)
- null 텍스트 표시 정책: `"-"` 표시 (빈 문자열/null 모두 동일 처리)
- FAILED 상태 → "처리 중 오류가 발생했습니다. 다시 시도해주세요." 고정 안내

---

## 7. Status Badge 색상

| Status | 색상 |
|--------|------|
| PENDING | amber (대기중) |
| OCR_PROCESSING / TRANSLATING | blue (처리중) |
| COMPLETED | green |
| FAILED | red |

---

## 8. 테스트 전략

- loader 함수: 단위 테스트 생략 (통합 테스트로 커버)
- 주요 경로: 목록 → 상세 이동 수동 검증
- 비로그인 리다이렉트: _protected 레이아웃에서 처리되므로 별도 테스트 불필요
