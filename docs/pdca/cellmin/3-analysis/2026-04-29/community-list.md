# Check — 커뮤니티 목록 페이지 (#98)

- **작성자:** cellmin
- **날짜:** 2026-04-29 (브라우저 검증 반영 업데이트)
- **Plan:** docs/pdca/cellmin/1-plan/2026-04-28/community-list.md
- **Design:** docs/pdca/cellmin/2-design/2026-04-28/community-list.md

---

## 성공 기준 달성 현황

| 기준 | 결과 |
|------|------|
| `/community` 접근 시 목록 렌더링 | ✅ |
| 탭 클릭 → URL `?tab=` 업데이트 | ✅ |
| 시대 드롭다운 → URL `?era=` 업데이트 | ✅ |
| 페이지 클릭 → URL `?page=` 업데이트 | ✅ |
| 새로고침해도 필터/페이지 상태 유지 | ✅ |
| 비로그인 글 작성하기 → 모달 → 로그인 이동 | ✅ |
| 로그인 글 작성하기 → `/community/write` | ✅ |
| 게시글 행 클릭 → `/community/:id` | ✅ |
| 페이지네이션 버튼 3개 (Mock 30개) | ✅ |
| 목업 UI 일치 | ✅ |
| TypeScript 타입 오류 없음 | ✅ |
| ESLint 에러 없음 | ✅ |
| 브라우저 수동 검증 (탭·시대·페이지·모달·뒤로가기) | ✅ |

---

## 영역별 평가

### 1. 기능 완성도 — 100/100 (가중치 20%)

Plan 성공 기준 11개 전부 달성. URL 파라미터 정규화(fallback + page 초과 replace) 설계 그대로 구현.

### 2. 코드 품질 — 92/100 (가중치 20%)

**잘 된 점:**
- types / mock / view / route 파일 분리 명확
- `parseTab`, `parseEra`, `parsePage` helper 함수로 파싱 로직 분리
- `handleTabChange` 시 `page` 리셋, `handleEraChange` 시 `page` 리셋 일관됨
- `Link` 컴포넌트 사용으로 a11y + prefetch 기본 동작 확보
- `useRouteLoaderData<typeof layoutLoader>` 타입 단언 없이 안전하게 처리
- `label htmlFor` + `select id` 접근성 개선 ✅ (Act 반영)
- 불필요한 `(p: Post)` 타입 어노테이션 제거 ✅ (Act 반영)
- 페이지네이션 항상 표시 + `ChevronsLeft/ChevronLeft/ChevronRight/ChevronsRight` 아이콘 적용 ✅ (브라우저 검증 후 개선)
- URL 정규화 effect만 `replace: true`, 필터/페이지 변경은 push로 히스토리 정상 적재 ✅

### 3. 테스트 — 80/100 (가중치 20%)

- TypeScript 타입 체크 통과 ✅
- ESLint 에러 없음 ✅
- 라우트 200 응답 확인 ✅
- 브라우저 수동 검증 완료 ✅
  - 탭 필터 → URL 반영, 필터 적용 확인
  - 시대 드롭다운 → URL 반영, 교차 필터 확인
  - 페이지네이션 (`<< < 1 2 3 > >>`) 동작 확인
  - 새로고침 후 필터 상태 유지 확인
  - 잘못된 URL 파라미터 자동 정규화 확인
  - 비로그인 글 작성하기 → 모달 → 로그인 이동 확인
  - 뒤로가기 히스토리 동작 확인
- `parseTab`, `parseEra`, `parsePage` 단위 테스트 없음 (Mock 단계 범위 외)

### 4. 보안 — 90/100 (가중치 20%)

- URL 파라미터 정규화로 잘못된 입력 처리 ✅
- `post.title` JSX 직접 렌더링 → React 자동 이스케이프로 XSS 방지 ✅
- 비로그인 → `/login?redirect=` 이동 ✅
- `redirect` 파라미터는 이전 세션에서 구현한 `isSafeRedirect`로 LoginView에서 검증됨 ✅

소소한 주의: `select`의 `onChange`에서 `e.target.value as PostEra` 타입 단언 사용. 옵션을 `ERA_KEYS`에서만 렌더링하므로 실제 위험은 없으나 이론적으로 외부 값이 들어올 수 있음.

### 5. 성능 — 100/100 (가중치 10%)

- 30개 Mock 데이터 클라이언트 필터링 — 문제없는 규모
- 불필요한 re-render 없음
- `Link` prefetch 기본 동작 활용

### 6. 문서화 — 85/100 (가중치 10%)

- Plan, Design 문서 완비 ✅
- `useEffect` 의도 주석 적절 ✅
- mock.ts 탭별 섹션 구분 ✅

---

## 종합 점수

| 영역 | 점수 | 가중치 | 기여 |
|------|------|--------|------|
| 기능 완성도 | 100 | 20% | 20.0 |
| 코드 품질 | 92 | 20% | 18.4 |
| 테스트 | 80 | 20% | 16.0 |
| 보안 | 90 | 20% | 18.0 |
| 성능 | 100 | 10% | 10.0 |
| 문서화 | 85 | 10% | 8.5 |
| **합계** | | | **90.9 / 100** |

---

## 브라우저 검증 후 추가 개선 사항 (반영 완료)

| 항목 | 내용 |
|------|------|
| 페이지네이션 항상 표시 | `totalPages > 1` 조건 제거 → 1페이지도 버튼 표시 |
| 네비게이션 버튼 추가 | `ChevronsLeft / ChevronLeft / ChevronRight / ChevronsRight` 아이콘 |
| 히스토리 동작 확인 | 필터/페이지 변경은 push, URL 정규화만 replace 유지 |
| import 순서 | `lint:fix` 자동 정렬 |
| 접근성 | `label htmlFor` + `select id` 추가 |
| 타입 어노테이션 | 불필요한 `(p: Post)` 제거 |
