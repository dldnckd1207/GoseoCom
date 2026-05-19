---
name: react-dev
description: React/Vite/TypeScript/Tailwind CSS 기반 프로젝트 개발 시 FSD 아키텍처, 구현 패턴, 컨벤션을 제공하는 skill. admin 디렉토리의 코드를 작성/수정/디버깅할 때 사용.
---

# React 개발 가이드

> **[필수]** 이 skill의 컨벤션을 따르세요. <br />
> 컨벤션을 따르지 않은 코드는 프로젝트 규칙을 위반할 수 있습니다.

---

## FSD 아키텍처

```
src/
├── app/              # 앱 설정 (providers, router, main)
├── pages/            # 라우트 페이지 (이벤트 핸들러 + UI 조합만)
├── features/         # 기능별 모듈 (api, hooks, components, types, utils)
├── entities/         # 공유 도메인 모델 (여러 feature에서 공유하는 비즈니스 모델)
└── shared/           # 공통 모듈 (api, ui, hooks, lib, store, types, layout)
```

### 레이어 의존성 규칙

```
pages/ → features/ → entities/ → shared/

금지:
- features 간 Hook/Component/API 직접 import 금지
- features 간 타입/상수 import는 허용 (런타임 의존성 없음)
- entities 간 직접 import 금지
- shared → entities/features/pages 방향 import 금지
- pages에 비즈니스 로직 금지 (hooks에 위임)
- pages에서 직접 API 호출 금지 (TanStack Query hooks 경유)
```

### entities vs shared 구분

| 레이어 | 대상 | 예시 |
|--------|------|------|
| `entities/` | 여러 feature에서 공유하는 비즈니스 도메인 모델 | user, file |
| `shared/` | 인프라성 타입, 유틸리티, UI 컴포넌트 | PageRequest, apiClient, hooks, ui |

> **승격 기준:** feature에서 만든 타입/API가 2개 이상의 feature에서 사용되면 entities로 승격 검토.

### 핵심 규칙

- 서버 상태: TanStack Query (`useQuery`/`useMutation`) — 데이터 페칭, 캐시 관리
- 클라이언트 상태: Zustand — 인증, 사이드바 등 전역 상태만
- UI: shadcn/ui + Tailwind CSS — 커스텀 CSS 최소화
- 폼: React Hook Form + Zod — validation 필요한 CUD 폼
- 라우팅: React Router — SPA
- API 응답 형식: `{ header, body: { data } }` — `extractData()`로 추출

---

## 상세 가이드 (필요 시 참조)

| 작업 | 참조 문서 |
|------|----------|
| Hook/Page 패턴 구현 | [references/patterns.md](references/patterns.md) — Hook 4종 + Page 패턴 + 데이터 변환 |
| 코딩 컨벤션, 금지 규칙 | [references/coding-conv.md](references/coding-conv.md) — 네이밍, import, 타입, CSS 유틸리티 |
| API 연동 컨벤션 | [references/api-conv.md](references/api-conv.md) — 응답 형식, Query Keys, HTTP Method |
| 개발 체크리스트 | [references/checklist.md](references/checklist.md) — 새 기능 개발 + 코드 리뷰 체크 |
| CSS/레이아웃 규칙 | [references/css-rules.md](references/css-rules.md) — 폰트 체계, layout.css, FSD 슬라이스 코로케이션, 반응형, 접근성 |
