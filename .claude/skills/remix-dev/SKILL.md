---
name: remix-dev
description: React Router v7(framework mode)/TypeScript/Tailwind CSS 기반 프로젝트 개발 시 FSD 아키텍처, 구현 패턴, 컨벤션을 제공하는 skill. client 디렉토리의 코드를 작성/수정/디버깅할 때 사용. (Remix는 v7부터 React Router에 통합되었으며, skill 이름은 레거시 유지)
---

# React Router v7 (framework mode) 개발 가이드

> **[필수]** 이 skill의 컨벤션을 따르세요. <br />
> 컨벤션을 따르지 않은 코드는 프로젝트 규칙을 위반할 수 있습니다.

---

## FSD 아키텍처

```
app/
├── routes/           # 파일 기반 라우팅 (loader + action + UI 위임)
├── views/            # 페이지 뷰 컴포넌트 (Hook + Feature UI 조합)
├── widgets/          # 조합 UI (여러 페이지에서 공유: Header, Footer, Layout 등)
├── features/         # 기능별 모듈 (api, types, hooks, ui, index.ts)
├── entities/         # 공유 도메인 모델 (비즈니스 도메인 타입 + API + store)
└── shared/           # 공통 모듈 (api, types, stores, hooks, lib, ui, config, styles)
```

### 레이어 의존성 규칙

```
routes/ → views/ → widgets/, features/ → entities/ → shared/

금지:
- features 간 직접 import 금지 (entities 또는 shared를 통해서만)
- entities 간 직접 import 금지
- shared → entities/features 방향 import 금지
- routes/ 에 비즈니스 로직 금지 (View 위임 + loader/action만)
- views/ 에 직접 API 호출 금지 (hooks 또는 loader 데이터 경유)
```

### 3-Layer UI 계층

| 계층 | 위치 | 범위 |
|------|------|------|
| shared/ui | `shared/ui/` | 프로젝트 전체 (shadcn/ui + 유틸리티) |
| feature/ui | `features/*/ui/` | 해당 feature 내 (SearchForm, List 등) |
| widget | `widgets/` | 여러 feature/view 공유 (Header, Layout 등) |

### entities vs shared 구분

| 레이어 | 대상 | 예시 |
|--------|------|------|
| `entities/` | 여러 feature에서 공유하는 비즈니스 도메인 모델 | user, file |
| `shared/` | 인프라성 타입, 유틸리티, UI 컴포넌트 | PageRequest, apiClient, hooks, ui |

> **승격 기준:** feature에서 만든 타입/API가 2개 이상의 feature에서 사용되면 entities로 승격 검토.

### 핵심 규칙

- **서버 데이터:** `loader` 함수로 초기 데이터 로딩 → `useLoaderData()`로 소비
- **뮤테이션:** `action` 함수 + `<Form>` 또는 `useFetcher()`
- **클라이언트 전용 상태:** Zustand (auth, UI 전역 상태만)
- **클라이언트 사이드 재조회:** TanStack Query 허용 (실시간, polling 등 필요 시)
- **UI:** shadcn/ui + Tailwind CSS — 커스텀 CSS 최소화
- **폼 유효성:** React Hook Form + Zod

---

## 상세 가이드 (필요 시 참조)

| 작업 | 참조 문서 |
|------|----------|
| Route/loader/action/View/Feature 구현 | [references/patterns.md](references/patterns.md) — 구현 패턴 템플릿 + Golden Files |
| 코딩 컨벤션, 금지 규칙 | [references/coding-conv.md](references/coding-conv.md) — 네이밍, import, 타입, Anti-Patterns |
| API 연동 컨벤션 | [references/api-conv.md](references/api-conv.md) — 인증, 응답 형식, 에러 처리 |
| Fallback, 캐싱 전략 | [references/fallback.md](references/fallback.md) — 캐시 계층, 에러 경계, loader fallback |
| CSS/레이아웃 규칙 | [references/css-rules.md](references/css-rules.md) — 폰트 체계, layout.css, FSD 슬라이스 코로케이션, 반응형, 접근성 |
| 개발 체크리스트, 보안 | [references/checklist.md](references/checklist.md) — 새 기능 개발 시 확인 사항 |
