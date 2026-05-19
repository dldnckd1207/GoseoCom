# 개발 체크리스트 + 보안

---

## 새 기능 개발 체크리스트

### 조회 (목록 + 상세)

- [ ] `shared/api/endpoints.ts`에 엔드포인트 등록 (`API_ENDPOINTS` 필수)
- [ ] `features/{domain}/types.ts`에 타입 정의 (`~Response`, `~SearchRequest`, `~DetailResponse`)
- [ ] `features/{domain}/api.ts`에 API 함수 작성 (`fetchList`/`fetchDetail`)
- [ ] `features/{domain}/hooks/use{Domain}List.ts` — URL searchParams + useNavigate (필터/페이징)
- [ ] `features/{domain}/ui/`에 UI 컴포넌트 (SearchForm, List/Table 등)
- [ ] `features/{domain}/index.ts`에 배럴 export (types + api + ui)
- [ ] `views/{domain}/{Domain}View.tsx` — 목록 View (`useLoaderData` + Hook + Feature UI 조합, 50-80줄)
- [ ] `views/{domain}/{Domain}DetailView.tsx` — 상세 View (`useLoaderData` + 수정 이동 + useFetcher 삭제)
- [ ] `routes/{domain}._index.tsx` — 목록 Route (`loader` + View 위임)
- [ ] `routes/{domain}.$id.tsx` — 상세 Route (`loader` + View 위임)
- [ ] 각 Route에 `ErrorBoundary` 선언

### CUD (생성 + 수정 + 삭제)

- [ ] `features/{domain}/types.ts`에 CUD 타입 추가 (`~CreateRequest`, `~UpdateRequest`, `~DeleteRequest`)
- [ ] `features/{domain}/api.ts`에 CUD API 함수 추가 (`fetchCreate`/`fetchUpdate`/`fetchDelete`)
- [ ] `features/{domain}/hooks/use{Domain}Form.ts` — React Hook Form + Zod + useFetcher
- [ ] 목록 View/Hook에 `handleDelete` 추가 (`useFetcher.submit` + confirm + toast)
- [ ] `views/{domain}/{Domain}FormView.tsx` — 등록/수정 폼 View (50-80줄)
- [ ] `routes/{domain}.create.tsx` — 등록 Route (`action` + View 위임)
- [ ] `routes/{domain}.$id.edit.tsx` — 수정 Route (`loader` + `action` + View 위임)

### entities (공유 도메인 모델)

> 여러 feature에서 공유하는 도메인(`user`, `file` 등)은 `entities/`에 배치

- [ ] `entities/{domain}/types.ts`에 타입 정의
- [ ] `entities/{domain}/api.ts`에 API 함수 (선택)
- [ ] `entities/{domain}/store.ts`에 Zustand 스토어 (선택)
- [ ] `entities/{domain}/index.ts`에 배럴 export

### 공통 확인사항

- [ ] import alias `~/` 사용 (`@/` 금지)
- [ ] named export만 사용 (`routes/` 파일만 default export 허용)
- [ ] 레이어 의존성 규칙 준수 (`features/` 간 직접 import 금지, `entities/` 간 직접 import 금지)
- [ ] 초기 데이터는 loader + `useLoaderData()` 사용 (Hook에서 직접 fetch 금지)
- [ ] 필터/페이징은 URL `searchParams` + `useNavigate()`로 관리
- [ ] `fetch` 직접 사용 금지 — `apiClient` 또는 공통 서비스 함수 사용
- [ ] 공통 UI는 `shared/ui/` 활용 (PaginationNav, StateDisplay 등)

---

## 보안 가이드

### XSS 방지 (사용자 입력 HTML 렌더링 시)

```typescript
import DOMPurify from 'dompurify';
export const sanitize = (html: string) => DOMPurify.sanitize(html);
```

> **dangerouslySetInnerHTML 사용 시 반드시 sanitize 처리.**

### 민감정보 마스킹

```typescript
export const mask = {
    phone: (v: string) => v.replace(/(\d{3})-(\d{4})-(\d{4})/, '$1-****-$3'),
    email: (v: string) => { const [l, d] = v.split('@'); return l.slice(0, 2) + '**@' + d; },
    name: (v: string) => v[0] + '*'.repeat(v.length - 2) + v[v.length - 1],
};
```

### 보안 체크리스트

- [ ] 사용자 입력 데이터 sanitize 처리 (HTML 렌더링 시)
- [ ] 에러 메시지에 민감 정보 노출 금지
- [ ] `console.log`에 개인정보 출력 금지
- [ ] 인증 필요 Route는 loader에서 `UNAUTHORIZED` 시 `redirect('/login')` 처리
- [ ] 프로덕션 빌드 시 소스맵 비활성화
