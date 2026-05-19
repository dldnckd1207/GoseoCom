# Design — 번역 페이지 구현 + 보호 Route 기반 구축

**Feature:** translate-page  
**Author:** cellmin  
**Date:** 2026-04-22 (리뷰 반영)
**Redmine:** #97  
**Plan:** docs/pdca/cellmin/1-plan/2026-04-22/translate-page.md

---

## 1. 아키텍처

`_protected.tsx`는 **인증 게이트 역할만** 담당하고 UI 레이아웃(Header/Footer)은 상위 `_layout.tsx`에 위임한다.
미인증 시 현재 경로를 `?redirect=` 쿼리로 `/login`에 전달하고,
`LoginView`가 마운트 시 sessionStorage에 저장한다.
OAuth 완료 후 `_layout.tsx`의 useEffect가 sessionStorage를 읽어 자동 복귀한다.

```
미인증 사용자 → /translate
    ↓ _protected.tsx loader → redirect('/login?redirect=/translate')
    ↓ LoginView useEffect → sessionStorage.setItem('redirectAfterLogin', '/translate')
    ↓ OAuth 완료 → /
    ↓ _layout.tsx useEffect → navigate('/translate') + sessionStorage 삭제

레이어 구조:
_layout.tsx (Header/Footer 렌더링)
  └── _protected.tsx (인증 게이트 — Outlet만 렌더링)
        └── _protected.translate.tsx → TranslateView
```

---

## 2. 코드 구조

```
apps/client/app/
├── routes/
│   ├── _protected.tsx              # 신규 — 인증 게이트 (Outlet만, Header/Footer 없음)
│   ├── _protected.translate.tsx    # 신규 — /translate route
│   ├── _auth.tsx                   # 수정 — ?redirect 파라미터 처리 + 루프 방지
│   └── _layout.tsx                 # 수정 — sessionStorage redirect 감지 추가
│
└── views/
    ├── translate/
    │   └── TranslateView.tsx       # 신규 — 번역 페이지 UI
    └── auth/
        └── LoginView.tsx           # 수정 — 마운트 시 sessionStorage 저장
```

---

## 3. routes/_protected.tsx (신규)

Header/Footer 없이 인증 게이트 역할만 수행. 상위 `_layout.tsx`가 이미 Header/Footer를 렌더링한다.

```tsx
import type { Route } from './+types/_protected';

export async function loader({ request }: Route.LoaderArgs) {
    const pathname = new URL(request.url).pathname;
    try {
        const user = await serverFetch<User>(request, API_ENDPOINTS.ME);
        return { user };
    } catch (err) {
        if (err instanceof ApiError && err.status === 401)
            throw redirect(`/login?redirect=${encodeURIComponent(pathname)}`);
        if (err instanceof TypeError)
            throw redirect(`/login?redirect=${encodeURIComponent(pathname)}`);
        throw err;
    }
}

// Header/Footer는 상위 _layout.tsx가 담당 — 여기선 Outlet만
export default function ProtectedLayout() {
    return <Outlet />;
}
```

---

## 4. routes/_protected.translate.tsx (신규)

```tsx
import type { Route } from './+types/_protected.translate';

export function meta(_: Route.MetaArgs) {
    return [{ title: '번역하기 | 해독 AI' }];
}

export default function TranslateRoute() {
    return <TranslateView />;
}
```

---

## 5. routes/_auth.tsx (수정)

로그인 상태일 때 `?redirect=` 파라미터로 이동. **Open Redirect 방지** 및 **루프 방지** 검증 추가.

```tsx
export async function loader({ request }: Route.LoaderArgs) {
    const url = new URL(request.url);
    const raw = url.searchParams.get('redirect') ?? '/';
    // 상대 경로만 허용 (Open Redirect 방지) + /login 루프 방지
    // pathname만 추출해 쿼리스트링 포함 여부와 무관하게 안전하게 처리
    const safeRaw = raw.startsWith('/') && !raw.startsWith('//') ? raw : '/';
    const redirectTo = safeRaw === '/login' ? '/' : safeRaw;
    try {
        await serverFetch<User>(request, API_ENDPOINTS.ME);
        throw redirect(redirectTo);
    } catch (err) {
        if (err instanceof Response) throw err;
        if (err instanceof ApiError && (err.status === 401 || err.code === 'NETWORK_ERROR')) return null;
        if (err instanceof TypeError) return null;
        throw err;
    }
}
```

---

## 6. views/auth/LoginView.tsx (수정)

`useSearchParams`로 `?redirect` 읽기 → **useEffect에서** sessionStorage 저장 (SSR 안전).

```tsx
export function LoginView() {
    const [searchParams] = useSearchParams();
    const redirectPath = searchParams.get('redirect') ?? '';

    // SSR 안전: useEffect는 클라이언트에서만 실행
    // _auth.tsx와 동일한 검증 재적용 — /login 루프 방지
    useEffect(() => {
        if (!redirectPath) return;
        const isSafe = redirectPath.startsWith('/') && !redirectPath.startsWith('//') && redirectPath !== '/login';
        if (!isSafe) return;
        try {
            sessionStorage.setItem('redirectAfterLogin', redirectPath);
        } catch {
            // sessionStorage 미지원 환경(Safari private 등) — 홈으로 fallback
        }
    }, [redirectPath]);

    return (
        // onClick 제거 — useEffect에서 이미 저장됨
        <a href={`${BASE_URL}/auth/kakao`}>카카오로 시작하기</a>
        <a href={`${BASE_URL}/auth/google`}>Google로 시작하기</a>
    );
}
```

---

## 7. routes/_layout.tsx (수정)

기존 logout 감지 useEffect에 sessionStorage redirect 감지 추가. redirect를 먼저 처리.

> **우선순위 정책:** sessionStorage redirect가 1순위, logout 알림이 2순위.
> 둘이 동시에 존재하는 경우(`/?logout=true` + sessionStorage)는 정상 플로우에서 발생하지 않으나,
> 발생 시 redirect가 실행되고 logout 모달은 스킵된다.

```tsx
useEffect(() => {
    // 1순위: 로그인 후 redirect 처리 (sessionStorage)
    try {
        const redirectPath = sessionStorage.getItem('redirectAfterLogin');
        if (redirectPath) {
            sessionStorage.removeItem('redirectAfterLogin');
            navigate(redirectPath, { replace: true });
            return;
        }
    } catch {
        // sessionStorage 미지원 환경 — 무시
    }

    // 2순위: 로그아웃 알림
    if (searchParams.get('logout') === 'true') {
        openModal({
            type: 'alert',
            message: '로그아웃 되었습니다.',
            buttons: [{ label: '확인', onClick: () => navigate('/', { replace: true }) }],
        });
    }
}, [searchParams, navigate]);
```

---

## 8. views/translate/TranslateView.tsx (신규)

### 레이아웃 구성 (목업 기반)

```
TranslateView
├── 페이지 헤더 (제목 + 설명)
├── 파일 업로드 카드
│   └── 드래그앤드롭 영역
│       - "준비 중" 배지 표시 (cursor-not-allowed, 비활성 스타일)
│       - 클릭 시 openModal('서비스 준비 중')
├── 번역 영역 (2열 그리드, lg:grid-cols-2)
│   ├── 원본 텍스트 카드
│   │   ├── 카드 헤더 (FileText 아이콘 + 제목)
│   │   ├── textarea (h-96, resize-none)
│   │   └── "AI 번역 시작" 버튼 → openModal 서비스 준비중
│   └── 번역 결과 카드
│       ├── 카드 헤더 (Sparkles 아이콘 + 다운로드 버튼 UI)
│       └── 결과 영역 (빈 상태 안내 텍스트)
└── 사용 안내 섹션 (파란 배경 카드)
```

### 파일 업로드 영역 — 비활성 처리

클릭/드롭 미구현이므로 사용자 혼란 방지를 위해 명확한 비활성 UI 제공:
- `opacity-60 cursor-not-allowed` 스타일
- "준비 중" 배지 (`badge` 형태)
- 클릭 시 `openModal({ type: 'alert', message: '파일 업로드 기능은 서비스 준비 중입니다.' })`

### 서비스 준비중 모달

```tsx
const handleTranslate = () => {
    openModal({ type: 'alert', message: '서비스 준비 중입니다. 곧 이용하실 수 있습니다.' });
};
```

---

## 9. 리뷰 반영 사항 (2차 리뷰 포함)

| 이슈 | 해결 방법 |
|------|----------|
| `_protected.tsx` Header/Footer 중복 | Outlet만 렌더링, Header/Footer 제거 |
| sessionStorage SSR 안전성 | onClick → useEffect로 이동 |
| redirect 루프 (`/login?redirect=/login`) | `_auth.tsx` + `LoginView` 양쪽에서 검증 |
| Open Redirect | `startsWith('/')` + `!startsWith('//')` 검증 |
| sessionStorage 미지원 | try-catch 래핑, fallback은 홈 |
| 파일 업로드 UI 혼란 | 비활성 스타일 + 클릭 시 안내 모달 |
| LoginView redirect 재검증 | `_auth.tsx`와 동일 검증 useEffect에서 재적용 |
| redirect + logout 동시 존재 정책 | redirect 1순위, logout 스킵 — 문서 명시 |

---

## 10. 테스트 전략

- `npm run typecheck` 통과
- `npm run lint` 통과
- 수동 검증:
  - 미로그인 → `/translate` → `/login?redirect=/translate` redirect 확인
  - 이미 로그인 상태 → `/login?redirect=/translate` → `/translate` 자동 redirect
  - 로그인 완료 후 → `/translate` 자동 복귀
  - `/login?redirect=/login` → `/`로 안전하게 redirect
  - "AI 번역 시작" 클릭 → 모달 표시
  - 파일 업로드 영역 클릭 → 준비중 모달 표시
  - Header/Footer 중복 렌더링 없음 확인
