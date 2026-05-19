# 개발 체크리스트

---

## 새 기능 개발 체크리스트

### Feature 모듈

- [ ] `features/{domain}/types/`에 타입 정의 (~Request, ~Response, ~SearchParams, ~FormData)
- [ ] `features/{domain}/api/`에 API 함수 작성 (apiClient 사용)
- [ ] `shared/lib/queryKeys.ts`에 Query Key 등록
- [ ] `features/{domain}/hooks/`에 조회 훅 (useQuery)
- [ ] `features/{domain}/hooks/`에 CUD 훅 (useMutation + invalidateQueries)
- [ ] `features/{domain}/hooks/`에 폼 훅 (복합 로직 시, RHF + Zod)
- [ ] `features/{domain}/components/`에 UI 컴포넌트 (Filter, Table, Form 등)
- [ ] `features/{domain}/utils/`에 데이터 변환 함수 (선택)
- [ ] `features/{domain}/index.ts`에 배럴 export (components + types만, hooks/api 제외)

### entities (공유 도메인 모델)

> 여러 feature에서 공유하는 도메인(`user`, `file` 등)은 `entities/`에 배치

- [ ] `entities/{domain}/types/`에 타입 정의
- [ ] `entities/{domain}/api/`에 API 함수 (선택)
- [ ] `entities/{domain}/index.ts`에 배럴 export

### Page

- [ ] `pages/{domain}/MyListPage.tsx` — 목록 (이벤트 핸들러 + UI 조합만)
- [ ] `pages/{domain}/MyDetailPage.tsx` — 상세/등록/수정 (폼 훅 연동)
- [ ] `app/router.tsx`에 라우트 등록 (lazy import)
- [ ] 새 `VITE_` 환경 변수 추가 시 `src/vite-env.d.ts` 타입 업데이트
- [ ] Page 200줄 이하 유지 (초과 시 Hook/Component 분리)

---

## Page 체크리스트

- [ ] Page에 비즈니스 로직이 없는가? (Hook에 위임)
- [ ] Page에 데이터 변환 함수가 없는가? (Hook/utils에 배치)
- [ ] `useState` 5개 미만인가? (초과 시 `useMyForm` Hook 분리)
- [ ] `useNavigate`는 Page에서 호출하는가? (폼 훅은 예외)
- [ ] 로딩/에러/빈 상태 분기 처리가 있는가?
- [ ] 에러 상태에서 `refetch()` 재시도 버튼을 제공하는가?
- [ ] 저장 버튼에 `disabled={isSaving || !form.formState.isDirty}` 적용했는가?

---

## Hook 체크리스트

- [ ] 모든 API 호출이 TanStack Query를 통하는가?
- [ ] `useQuery`: API 함수에서 `body.data` 추출 후 반환하는가?
- [ ] `useMutation`: onSuccess에서 `invalidateQueries` 호출?
- [ ] `useMutation`: onError에서 toast.error 표시?
- [ ] 폼 훅: React Hook Form + Zod 사용? (수동 if문 유효성 검사 금지)
- [ ] Query Key가 `queryKeys` 객체에 등록되어 있는가?

---

## 스타일 체크리스트

- [ ] 시맨틱 클래스 우선 사용 (`layout.css` 클래스 먼저 확인)?
- [ ] 인라인 Tailwind는 일회성 미세 조정에만?
- [ ] shadcn/ui 컴포넌트 우선 사용? (커스텀 UI 최소화)
- [ ] 접근성: 아이콘 버튼 `aria-label`, 클릭 행 `tabIndex` + `onKeyDown`?

---

## 코드 리뷰 체크리스트

- [ ] FSD 레이어 의존성 준수 (pages → features → entities → shared)
- [ ] features 간 Hook/Component/API import 없음 (타입/상수만 허용)
- [ ] `any` 타입 미사용
- [ ] `console.log` 미사용 (`warn`/`error`만 허용)
- [ ] import 순서 ESLint 규칙 준수
- [ ] named export 사용 (default export 금지, app/ 엔트리만 예외)
- [ ] 컴포넌트 코드 순서: Hooks → State → Query → Derived → Effects → Handlers → JSX
