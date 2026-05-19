# Design: CSS 컨벤션 위반 수정 및 모바일 반응형 햄버거 메뉴

- **Feature:** css-convention-mobile-menu
- **Redmine:** #107
- **Date:** 2026-05-05
- **Author:** cellmin
- **Plan:** docs/pdca/cellmin/1-plan/2026-05-05/css-convention-mobile-menu.md

> **경로 기준:** 모든 파일 경로는 워크스페이스 루트(`haedok-ai/`) 기준.
> 클라이언트 앱 위치: `apps/client/` — 앱 소스: `apps/client/app/`

---

## 1. 아키텍처

### 변경 파일 목록

| 파일 | 유형 | 작업 |
|------|------|------|
| `apps/client/app/app.css` | 수정 | import 순서 + 폰트 크기 재정의 |
| `apps/client/app/shared/styles/layout.css` | **신규** | 공통 시맨틱 클래스 정의 |
| `apps/client/app/shared/ui/sheet.tsx` | **신규** | shadcn/ui Sheet 컴포넌트 (`npx shadcn add sheet`) |
| `apps/client/app/widgets/layout/Header.tsx` | 수정 | 시맨틱 구조 + 햄버거 + MobileDrawer 연결 |
| `apps/client/app/widgets/layout/MobileDrawer.tsx` | **신규** | Sheet 기반 모바일 드로어 UI |
| `apps/client/app/widgets/layout/Footer.tsx` | 수정 | `.container-main` 적용 |
| `apps/client/app/widgets/layout/PageLayout.tsx` | 수정 | 폰트 크기 + `.container-main` 적용 |

### 의존성 흐름

```
Header.tsx
├── useState(isOpen)          ← 드로어 열림 상태
├── MobileDrawer.tsx          ← Sheet 기반 드로어
│   └── ~/shared/ui/sheet     ← shadcn/ui Sheet
└── shared/config/navigation  ← NAV_LINKS (기존 공유)
```

---

## 2. CSS 설계

### 2-1. `apps/client/app/app.css` — import 순서 수정

```css
/* AS-IS (위반) */
@import "tailwindcss";
@import "tw-animate-css";        ← 2번째 (금지)
@import "shadcn/tailwind.css";
@import "@fontsource-variable/geist";

/* TO-BE */
@import "tailwindcss";
@import "shadcn/tailwind.css";
@import "@fontsource-variable/geist";
@import "./shared/styles/layout.css";    ← 추가 (공통 레이아웃, app.css와 같은 레벨)
@import "tw-animate-css";               ← 마지막으로 이동
```

### 2-2. `apps/client/app/app.css` — `@theme inline` 폰트 크기 재정의

현재 `@theme inline` 블록에 폰트 크기 변수가 없음. 아래 내용을 추가한다.

```css
@theme inline {
  /* 기존 color/radius 변수 유지 */
  ...

  /* 폰트 크기 재정의 (Tailwind 기본값 오버라이드) */
  --text-xs:   0.875rem;   /* 14px — 캡션, 최소 허용 */
  --text-sm:   1rem;       /* 16px — 부제목, 메타 */
  --text-base: 1.125rem;   /* 18px — 본문 기본 */
  --text-lg:   1.25rem;    /* 20px — 카드 제목, 헤더 메뉴 */

  /* 프로젝트 전용 시맨틱 크기 */
  --text-page-title:        2rem;       /* 32px */
  --text-page-title-mobile: 1.75rem;   /* 28px */
  --text-section-title:     1.5rem;    /* 24px */
  --text-card-title:        1.25rem;   /* 20px */
  --text-header-menu:       1.25rem;   /* 20px */
  --text-header-submenu:    1rem;      /* 16px */
  --text-body-lg:           1.25rem;   /* 20px */
  --text-body:              1.125rem;  /* 18px */
  --text-body-sm:           1rem;      /* 16px */
  --text-caption:           0.875rem;  /* 14px */
}
```

### 2-3. `apps/client/app/shared/styles/layout.css` — 신규 생성

이번 범위에서 필요한 최소 공통 클래스만 정의한다.
추후 반복 패턴이 발견되면 점진적으로 추가한다.

```css
/* shared/styles/layout.css */

/* 컨테이너 */
.container-main {
  @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8;
}

/* 페이지 래퍼 */
.page-wrapper {
  @apply min-h-screen bg-gray-50;
}
```

---

## 3. 컴포넌트 설계

### 3-1. `apps/client/app/widgets/layout/Header.tsx` — 구조 변경

**시맨틱 HTML 수정:**
```tsx
/* AS-IS */
<nav className="...sticky...">
  <div className="max-w-7xl ...">
    ...
  </div>
</nav>

/* TO-BE */
<header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
  <div className="container-main">
    <div className="flex justify-between items-center h-16">
      {/* 로고 */}
      <NavLink to="/" ...>...</NavLink>

      {/* 데스크탑 네비 (lg+에서만 표시) */}
      <nav className="hidden lg:flex items-center gap-1" aria-label="주 네비게이션">
        {visibleLinks.map(...)}
        {/* 사용자 영역 */}
      </nav>

      {/* 모바일 햄버거 버튼 (lg 미만에서만 표시) */}
      <button
        className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
        aria-label="메뉴 열기"
        aria-expanded={isOpen}
        aria-controls="mobile-menu"
        onClick={() => setIsOpen(true)}
      >
        <Menu className="w-6 h-6" aria-hidden />
      </button>
    </div>
  </div>

  {/* 모바일 드로어 */}
  <MobileDrawer
    isOpen={isOpen}
    onClose={() => setIsOpen(false)}
    user={user}
    visibleLinks={visibleLinks}
  />
</header>
```

**상태 관리:**
```tsx
const [isOpen, setIsOpen] = useState(false);
```

### 3-2. `apps/client/app/widgets/layout/MobileDrawer.tsx` — 신규 컴포넌트

shadcn/ui `Sheet`를 사용한 우측 슬라이드 드로어.

```tsx
// apps/client/app/widgets/layout/MobileDrawer.tsx
import { Form, NavLink } from 'react-router';

import { LogOut, User } from 'lucide-react';

import { cn } from '~/shared/lib/cn';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from '~/shared/ui/sheet';
import type { NavItem } from '~/shared/config/navigation';
import type { User as UserType } from '~/shared/types/auth';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  user: UserType | null;
  visibleLinks: NavItem[];
}

export function MobileDrawer({ isOpen, onClose, user, visibleLinks }: Props) {
  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex h-full w-72 flex-col" id="mobile-menu">
        <SheetHeader>
          <SheetTitle>메뉴</SheetTitle>
        </SheetHeader>

        {/* 네비게이션 링크 */}
        <nav aria-label="모바일 네비게이션" className="flex flex-col gap-1 mt-4">
          {visibleLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'px-4 py-3 rounded-lg font-medium transition-colors text-base',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100',
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* 사용자 영역 (구분선 아래) */}
        <div className="mt-auto pt-4 border-t border-gray-200">
          {user ? (
            <div className="flex flex-col gap-2">
              <span className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700">
                <User className="w-4 h-4" aria-hidden />
                {user.name}
              </span>
              <Form method="post" action="/auth/logout">
                <button
                  type="submit"
                  className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                  aria-label="로그아웃"
                  onClick={onClose}
                >
                  <LogOut className="w-4 h-4" aria-hidden />
                  로그아웃
                </button>
              </Form>
            </div>
          ) : (
            <NavLink
              to="/login"
              onClick={onClose}
              className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              로그인
            </NavLink>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

### 3-3. `apps/client/app/widgets/layout/PageLayout.tsx` — 폰트 크기 수정

`@theme inline`에 `--text-page-title` / `--text-page-title-mobile`을 등록하므로, 컴포넌트에서도 CSS 변수 기반 arbitrary value를 사용한다.

```tsx
/* AS-IS */
<h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">

/* TO-BE */
<h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">
```

> Tailwind v4 arbitrary value 문법: `text-[length:var(--custom-var)]`

---

## 4. 외부 의존성

| 패키지 | 버전 | 용도 | 설치 방법 |
|--------|------|------|-----------|
| `@base-ui/react` | 기존 | Sheet primitive | 이미 설치됨 |
| shadcn/ui Sheet | - | 드로어 UI | `cd apps/client && npx shadcn add sheet` |
| lucide-react | 기존 | Menu, X 아이콘 | 이미 설치됨 |

> `npx shadcn add sheet` 실행 시 `button.tsx`도 overwrite됨 — diff 확인 후 적용.

---

## 5. 반응형 브레이크포인트 전략

| 구간 | 햄버거 버튼 | 데스크탑 네비 | 드로어 |
|------|------------|-------------|-------|
| 0 ~ 1023px (모바일/태블릿) | `flex` | `hidden` | Sheet (right) |
| 1024px+ (데스크탑) | `hidden` | `flex` | 미사용 |

**기준 브레이크포인트:** `lg:` (1024px) — 컨벤션 기준 풀 네비게이션 기준점.

---

## 6. 접근성 설계

| 요소 | 적용 속성 | 목적 |
|------|----------|------|
| 햄버거 버튼 | `aria-label="메뉴 열기"` | 아이콘만 있는 버튼 식별 |
| 햄버거 버튼 | `aria-expanded={isOpen}` | 드로어 열림 상태 전달 |
| 햄버거 버튼 | `aria-controls="mobile-menu"` | 드로어와 연결 |
| 데스크탑 nav | `aria-label="주 네비게이션"` | 영역 식별 |
| 모바일 nav | `aria-label="모바일 네비게이션"` | 영역 식별 |
| Sheet | `id="mobile-menu"` | aria-controls 대상 |

---

## 7. 구현 순서

```bash
# 1. shadcn Sheet 설치 (반드시 apps/client 에서 실행)
cd apps/client && npx shadcn add sheet    # button.tsx overwrite → diff 확인 후 적용

# 2. 공통 레이아웃 CSS 생성
# apps/client/app/shared/styles/layout.css  (신규)

# 3. app.css 수정
# apps/client/app/app.css  — import 순서 + @theme inline 폰트 추가

# 4. MobileDrawer 컴포넌트 생성
# apps/client/app/widgets/layout/MobileDrawer.tsx  (신규)

# 5. Header 수정
# apps/client/app/widgets/layout/Header.tsx  — 시맨틱 구조 + 햄버거 + MobileDrawer 연결

# 6. Footer 수정
# apps/client/app/widgets/layout/Footer.tsx  — .container-main 적용

# 7. PageLayout 수정
# apps/client/app/widgets/layout/PageLayout.tsx  — 폰트 크기 + .container-main 적용

# ※ MobileDrawer는 Header 내부 전용 → index.ts 수정 불필요
```

---

## 8. 검증 체크리스트 (Do 완료 후 확인)

- [ ] 모바일(375px): 햄버거만 보임, 인라인 네비 숨김
- [ ] 햄버거 클릭 → 우측 Sheet 슬라이드 인
- [ ] Sheet 내 링크 클릭 → 닫힘 + 페이지 이동
- [ ] Sheet 바깥 클릭(오버레이) → 닫힘
- [ ] 데스크탑(1280px): 인라인 네비 표시, 햄버거 숨김
- [ ] `apps/client/app/app.css` tw-animate-css 마지막 import 확인
- [ ] `apps/client/app/shared/styles/layout.css` 존재 + import 확인
- [ ] `apps/client/app/widgets/layout/Header.tsx` `<header>` > `<nav>` 구조 확인
- [ ] TypeScript 타입 에러 없음 (`cd apps/client && npm run typecheck`)
- [ ] Lint 통과 (`cd apps/client && npm run lint`)
