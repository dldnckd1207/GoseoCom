# Design — 로그인 페이지 + Frontend Auth 관리

**Feature:** login-auth  
**Author:** cellmin  
**Date:** 2026-04-19  
**Redmine:** #96  
**Plan:** docs/pdca/cellmin/1-plan/2026-04-19/login-auth.md

---

## 1. 아키텍처

SSR loader에서 `/api/v1/users/me`를 호출해 인증 여부를 판단한다.
결과를 `loaderData`로 컴포넌트에 전달하고, mount 시 Zustand authStore에 hydrate한다.
클라이언트 사이드 fetch는 401 시 `/auth/refresh` 자동 재시도 후 원 요청을 재전송한다.

```
SSR loader
    ↓ GET /api/v1/users/me (쿠키 자동 포함)
    ↓ 200 → loaderData로 user 반환 → 컴포넌트 mount 시 authStore hydrate
    ↓ 401 → /login redirect (_protected) 또는 그대로 진행 (_layout)

클라이언트 fetch (actions, 동적 데이터)
    ↓ 401 → POST /auth/refresh → 성공 시 원 요청 재전송
              실패 → /login redirect
```

---

## 2. 코드 구조

```
apps/client/app/
├── routes/
│   ├── _auth.tsx                  # 비로그인 전용 레이아웃 (로그인 시 / redirect)
│   ├── _auth.login.tsx            # /login 페이지
│   └── _layout.tsx                # 기존 — loader 추가 (/me 호출, 실패해도 무시)
│
├── views/
│   └── auth/
│       └── LoginView.tsx          # 로그인 카드 UI
│
├── widgets/
│   └── layout/
│       └── Header.tsx             # navigation.ts 기반 동적 렌더링 (수정)
│
└── shared/
    ├── api/
    │   ├── client.ts              # 클라이언트 fetch wrapper (401 → refresh → retry)
    │   └── server.ts              # SSR loader용 fetch (request 쿠키 포워딩)
    ├── stores/
    │   └── authStore.ts           # Zustand — user 캐싱, login/logout actions
    ├── hooks/
    │   └── useAuth.ts             # 순수 조회 only (isLoggedIn, user)
    ├── types/
    │   └── auth.ts                # User 타입 정의
    └── config/
        └── navigation.ts          # NAV_LINKS + minLevel
```

---

## 3. 타입 정의

```typescript
// shared/types/auth.ts
export type User = {
    user_id: string;
    email: string;
    name: string;
    profile_image_url: string | null;
    user_level: number;
};
```

---

## 4. shared/config/navigation.ts

```typescript
export type NavItem = {
    path: string;
    label: string;
    minLevel: number;   // 이 레벨 이상만 메뉴 노출
};

export const NAV_LINKS = [
    { path: '/translate', label: '번역하기', minLevel: 0 },
    { path: '/community', label: '커뮤니티', minLevel: 0 },
    { path: '/library',   label: '라이브러리', minLevel: 0 },
] satisfies NavItem[];
```

---

## 5. shared/api/server.ts (SSR loader용)

```typescript
// request.headers의 cookie를 포워딩하는 서버사이드 fetch 유틸
export async function serverFetch(
    request: Request,
    path: string,
    init?: RequestInit,
): Promise<Response>
```

---

## 6. shared/api/client.ts (클라이언트 fetch wrapper)

```typescript
// 401 → POST /auth/refresh → 성공 시 원 요청 재전송
// refresh 실패 시 authStore 초기화 후 /login redirect
export async function apiFetch(
    path: string,
    init?: RequestInit,
): Promise<Response>
```

---

## 7. shared/stores/authStore.ts

```typescript
// Zustand store
type AuthStore = {
    user: User | null;
    setUser: (user: User | null) => void;
    clear: () => void;
};
```

> **규칙:** API 호출 금지. loader에서 받은 데이터를 setUser로 저장하는 역할만 한다.

---

## 8. shared/hooks/useAuth.ts

```typescript
// 순수 조회 only — API 호출, 부수효과 금지
export function useAuth() {
    const user = useAuthStore((s) => s.user);
    return {
        user,
        isLoggedIn: user !== null,
    };
}
```

---

## 9. Route 파일 패턴

### routes/_auth.tsx
```typescript
import type { Route } from './+types/_auth';

export async function loader({ request }: Route.LoaderArgs) {
    // /me 호출 → 로그인 상태면 / redirect
}
export default function AuthLayout() { /* 중앙 카드 레이아웃 */ }
```

### routes/_auth.login.tsx
```typescript
import type { Route } from './+types/_auth.login';

export function meta(_: Route.MetaArgs) { /* 로그인 | 해독 AI */ }
export default function LoginRoute() { return <LoginView />; }
```

### routes/_layout.tsx (수정)
```typescript
import type { Route } from './+types/_layout';

export async function loader({ request }: Route.LoaderArgs) {
    // /me 호출 → 성공 시 user 반환, 실패 시 null 반환 (redirect 없음)
    return { user: User | null };
}
```

---

## 10. views/auth/LoginView.tsx

```
┌─────────────────────────────────┐
│         🔖 해독 AI              │
│    고서를 쉽고 빠르게 읽다       │
│                                 │
│  ┌───────────────────────────┐  │
│  │    카카오로 시작하기       │  │  ← 노란색 (#FEE500)
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │    Google로 시작하기      │  │  ← 흰 배경 + 테두리
│  └───────────────────────────┘  │
│                                 │
│  나중에 public/icons/ 로고 교체  │
└─────────────────────────────────┘
```

- Header/Footer 없는 독립 레이아웃
- 기존 스타일 준수: `rounded-lg`, `shadow-sm`, blue-600 포인트

---

## 11. CSS 규칙 (app.css 시맨틱 클래스)

로그인 페이지에서 2회 이상 사용되는 Tailwind 조합은 `app.css`에 등록:

```css
/* 소셜 로그인 버튼 공통 */
.btn-social {
    @apply w-full flex items-center justify-center gap-3
           py-3 px-4 rounded-lg font-medium transition-colors;
}
.btn-kakao  { @apply bg-[#FEE500] text-gray-900 hover:bg-[#F0D800]; }
.btn-google { @apply bg-white text-gray-700 border border-gray-300 hover:bg-gray-50; }

/* 인증 페이지 카드 */
.auth-card  { @apply bg-white rounded-2xl shadow-md p-8 w-full max-w-sm; }
```

---

## 12. Header.tsx 수정 방향

- `NAV_ITEMS` 상수 → `navigation.ts`의 `NAV_LINKS` import로 교체
- `user_level >= link.minLevel` 조건으로 메뉴 필터링
- 우측: 비로그인 → 로그인 버튼, 로그인 → 유저 이름/아바타

---

## 13. 의존성 추가

```bash
npm install zustand
```

---

## 14. 테스트 전략

- `npm run typecheck` 통과
- `npm run lint` 통과
- 수동 검증:
  - 미로그인 → `/` 접근 시 Header에 로그인 버튼 노출
  - 미로그인 → `/login` 접근 시 로그인 카드 렌더링
  - 로그인 상태 → `/login` 접근 시 `/` redirect
  - OAuth 버튼 클릭 시 `/auth/kakao`, `/auth/google` 이동
