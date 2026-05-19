# CSS / 레이아웃 규칙

---

## 폰트 크기 체계 (`app/app.css` @theme inline)

Tailwind v4 기본 스케일을 `@theme inline`으로 재정의하여, 프로젝트 전체 최소 폰트 크기를 **14px**로 설정.

| Tailwind 클래스 | CSS 변수 | 크기 | 용도 |
|----------------|----------|------|------|
| `text-xs` | `--text-xs` | 14px (0.875rem) | 캡션, 보조 텍스트 (최소 허용) |
| `text-sm` | `--text-sm` | 16px (1rem) | 부제목, 메타 텍스트 |
| `text-base` | `--text-base` | 18px (1.125rem) | **본문 기본** (`body`에 적용) |
| `text-lg` | `--text-lg` | 20px (1.25rem) | 카드 제목, 헤더 메뉴 |

프로젝트 전용 CSS 변수 (`app/app.css` `@theme inline`):

| 카테고리 | CSS 변수 | 크기 | 매핑 |
|---------|----------|------|------|
| 제목 | `--text-page-title` | 32px | = `text-2xl` |
| | `--text-page-title-mobile` | 28px | 모바일용 |
| | `--text-section-title` | 24px | = `text-xl` |
| | `--text-card-title` | 20px | = `text-lg` |
| 메뉴 | `--text-header-menu` | 20px | 헤더 네비게이션 |
| | `--text-header-submenu` | 16px | 헤더 서브메뉴 |
| | `--text-side-menu-title` | 20px | 사이드 메뉴 제목 |
| | `--text-side-menu` | 18px | 사이드 메뉴 |
| 본문 | `--text-body-lg` | 20px | = `text-lg` |
| | `--text-body` | 18px | = `text-base` |
| | `--text-body-sm` | 16px | = `text-sm` |
| | `--text-caption` | 14px | = `text-xs` |
| 버튼/폼 | `--text-btn-lg` / `--text-btn` / `--text-btn-sm` | 18 / 16 / 14px | 버튼 크기별 |
| | `--text-input` / `--text-label` | 16px | 폼 요소 |
| 특수 | `--text-stat-value` | 36px | = `text-3xl` |
| | `--text-badge` | 14px | 뱃지 |

> **규칙:** `html { font-size: 16px }` (rem 기준), `body { text-base }` = 18px 시각적 기본.
> 14px 미만 폰트는 사용하지 않음. `text-[11px]`, `text-[12px]` 등 임의 크기 금지.

---

## layout.css 주요 클래스 목록

시맨틱 역할에 따라 공통 CSS 클래스를 `layout.css`에 `@apply`로 정의한다.
컴포넌트 내부의 일회성 레이아웃은 Tailwind 유틸리티를 직접 사용하되, **논리적 영역에는 시맨틱 식별자 클래스를 반드시 부여**한다.

> **참고:** 아래 클래스 목록은 기준 가이드이며, 프로젝트 진행에 따라 실제 필요한 클래스를 추가한다. 2개 이상의 View에서 동일한 Tailwind 조합이 반복되면 `layout.css`에 시맨틱 클래스로 등록한다.

| 카테고리 | 클래스명 | 용도 |
|----------|---------|------|
| 컨테이너 | `.container-main`, `.container-page`, `.container-section` | 최대폭 + 패딩 컨테이너 |
| 페이지 래퍼 | `.page-wrapper`, `.page-section-alt` | 페이지/섹션 배경 래퍼 |
| 레이아웃 | `.layout-with-sidebar`, `.sidebar`, `.main-content` | 사이드바 레이아웃 |
| 히어로 | `.hero-title`, `.hero-subtitle`, `.hero-search-bar`, `.hero-search-select` | 히어로 영역 |
| 슬라이드 | `.slide-indicator`, `.slide-indicator-dot` | 슬라이드 인디케이터 |
| 캐러셀 | `.carousel-viewport`, `.carousel-track`, `.carousel-arrow` | CSS 캐러셀 |
| 섹션 제목 | `.section-title` | 섹션 타이틀 |
| 카드 | `.card`, `.card-padded`, `.card-search`, `.card-stats`, `.card-header-*` | 카드 변형 |
| 카드 아이템 | `.card-item`, `.card-item-thumbnail`, `.card-item-body`, `.card-item-title` | 목록형 카드 |
| 버튼 | `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-outline`, `.btn-search` | 버튼 변형 |
| 폼 | `.input`, `.select`, `.select-wrapper`, `.select-icon` | 폼 요소 |
| 필터 | `.filter-panel`, `.filter-row`, `.filter-collapse-wrapper`, `.checkbox-chip` | 검색 필터 |
| 테이블 | `.table-wrapper`, `.table`, `.table-header`, `.th`, `.tr`, `.td` | 테이블 |
| 탭 | `.tabs`, `.tab-list`, `.tab`, `.tab-active` | 탭 네비게이션 |
| 그리드 | `.grid-cards`, `.grid-dashboard`, `.search-grid` | 반응형 그리드 |
| 뱃지 | `.badge`, `.badge-primary`, `.badge-secondary` | 뱃지 |
| 상태 | `.state-loading`, `.state-empty`, `.state-error` | 상태 표시 |
| 통계 | `.stats-item`, `.stats-value`, `.stats-label`, `.stats-grid` | 통계 카드 |
| 파일 | `.file-list`, `.file-list-item`, `.file-list-header` | 첨부파일 목록 |
| 사이드 네비 | `.side-nav`, `.side-nav-item`, `.side-nav-item-active` | 서브 네비게이션 |
| 모달 | `.modal-overlay`, `.modal-body`, `.modal-actions` | 모달 |
| 유틸리티 | `.flex-between`, `.flex-center`, `.flex-gap` | 플렉스 단축 |
| 기타 | `.page-title`, `.total-count`, `.breadcrumb`, `.result-header` | 공통 UI |

---

## 스타일링 방법 선택 기준

| 상황 | 방법 | 예시 |
|------|------|------|
| 공통 레이아웃 | `@apply` (layout.css 또는 슬라이스 CSS) | `.container-main`, `.card`, `.btn-primary`, `.auth-*` |
| 컴포넌트 스타일 | Tailwind 유틸리티 직접 | `className="flex items-center gap-2"` |
| 재사용 UI | shadcn/ui 컴포넌트 | `<Button variant="primary">` |
| 조건부 스타일 | `cn()` 유틸리티 | `cn('btn', isActive && 'bg-blue-500')` |

> **원칙:** CSS 추상화보다 **컴포넌트 추상화**를 선호한다. 반복 패턴은 shadcn/ui 컴포넌트로.

---

## @layer & @apply 규칙

| @layer | 허용 여부 | 이유 |
|--------|:---------:|------|
| `@layer base` | O | 글로벌 리셋, 기본 스타일 (`*`, `body`) |
| `@layer components` | **X (금지)** | CSS 추상화보다 shadcn/ui 컴포넌트 추상화 우선 |
| `@layer utilities` | **X (금지)** | 팀 합의 후에만 허용 |

> **`@apply` 사용 범위:** `shared/styles/layout.css` 및 슬라이스별 CSS 파일(`features/*/styles/*.css`, `views/*/styles/*.css`, `widgets/*/styles/*.css`, `entities/*/styles/*.css`)의 시맨틱 클래스 정의에 사용. 컴포넌트 내부에서는 Tailwind 유틸리티를 JSX에서 직접 사용.

---

## 반응형 브레이크포인트

**Mobile-First 원칙:** 기본 스타일은 모바일 대상, 브레이크포인트로 상향 확장.

| 접두사 | 최소 너비 | 대상 | 주요 변경점 |
|--------|-----------|------|-------------|
| (없음) | 0px | 모바일 | 1열 레이아웃, 햄버거 메뉴 |
| `sm:` | 640px | 작은 태블릿 | 2열 그리드, 패딩/폰트 확대 |
| `md:` | 768px | 태블릿 | 헤더 상단바 표시, 타이포그래피 확대 |
| `lg:` | 1024px | 데스크탑 | 풀 네비게이션, 사이드바, 3열 그리드 |
| `xl:` | 1280px | 큰 데스크탑 | 4열 그리드 |

---

## 클래스 정렬 순서

```
1. 레이아웃 (display, position, flex, grid)
2. 박스 모델 (width, height, padding, margin)
3. 타이포그래피 (font, text)
4. 비주얼 (background, border, shadow, rounded)
5. 상호작용 (cursor, transition, hover)
```

---

## CSS 슬라이스 코로케이션 (FSD 기반 분리)

시맨틱 클래스는 **소유 슬라이스의 `styles/` 디렉토리**에 둔다. 다수 슬라이스가 공유하는 진짜 공통 클래스만 `shared/styles/layout.css`에 정의한다.

### CSS 파일 위치 패턴

| 파일 위치 | 소유 레이어 | 적용 기준 |
|----------|------------|---------|
| `shared/styles/layout.css` | shared | 2개 이상 슬라이스에서 공유하는 공통 클래스 |
| `features/{slice}/styles/{slice}.css` | features | 해당 feature에서만 사용하는 전용 클래스 |
| `views/{slice}/styles/{slice}.css` | views | 해당 view 페이지에서만 사용하는 전용 클래스 |
| `widgets/{slice}/styles/{slice}.css` | widgets | 해당 widget에서만 사용하는 전용 클래스 |
| `entities/{slice}/styles/{slice}.css` | entities | 해당 entity 도메인 전용 클래스 |

> **클래스 prefix 관례:** 슬라이스 CSS 파일 내 클래스명은 슬라이스명을 prefix로 사용한다 (예: `auth` 슬라이스 → `.auth-*`, `intro` 뷰 → `.intro-*`). 소유권을 클래스명에서 즉시 식별 가능하게 한다.

### app.css import 순서

```css
@import 'tailwindcss';
@import '../shared/styles/layout.css';   /* 1순위: 공통 베이스 */
/* 슬라이스 CSS (views → features → widgets 순서 권장) */
@import '../{layer}/{slice}/styles/{slice}.css';
@import 'tw-animate-css';               /* 마지막: 애니메이션 유틸리티 */
```

> **규칙:** 모든 글로벌 CSS는 `app/app.css` 한 곳에서 명시적으로 import한다. 컴포넌트에서 직접 import 금지 (cascade 순서 보장).  
> **경로:** 상대 경로(`../`) 사용. CSS에서는 alias(`@/`)가 환경에 따라 동작이 다를 수 있음.  
> **FSD 의존성:** `shared/styles/` 내부에서 상위 레이어 CSS를 import하면 의존성 방향 위반 — aggregator 방식 금지.

### 새 슬라이스 CSS 추가 시

1. 슬라이스 디렉토리에 `styles/<슬라이스명>.css` 생성
2. `app/app.css`에 import 한 줄 추가 — `shared/styles/layout.css` 다음, `tw-animate-css` 앞

---

## 시맨틱 HTML & 접근성

### 시맨틱 태그

```html
<header>                    <!-- 헤더 -->
<nav>                       <!-- 네비게이션 -->
<main>                      <!-- 메인 콘텐츠 -->
<section>                   <!-- 의미 있는 섹션 -->
<article>                   <!-- 독립적인 콘텐츠 -->
<aside>                     <!-- 보조 콘텐츠 -->
<footer>                    <!-- 푸터 -->
<form role="search">        <!-- 검색 영역 (<search> 대신 호환성 우선) -->
```

### 접근성 필수 사항

| 요소 | 규칙 | 예시 |
|------|------|------|
| 이미지 | `alt` 속성 필수 | `<img alt="고서 이미지: 훈민정음 해례본" />` |
| 폼 요소 | `label` 연결 | `<label htmlFor="id">` + `<input id="id">` |
| 아이콘 버튼 | `aria-label` | `<button aria-label="검색">` |
| 영역 | `aria-label` | `<section aria-label="장비 검색">` |
| 로딩 상태 | `role="status"` + `aria-live="polite"` | 스크린리더 알림 |
| 에러 상태 | `role="alert"` + `aria-live="assertive"` | 즉시 알림 |
| 키보드 | `tabIndex` + `onKeyDown` | Enter/Space로 행 클릭 |
| 스킵 네비 | `sr-only focus:not-sr-only` | 본문으로 바로가기 |
