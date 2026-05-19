# Plan: CSS 컨벤션 위반 수정 및 모바일 반응형 햄버거 메뉴

- **Feature:** css-convention-mobile-menu
- **Redmine:** #107
- **Date:** 2026-05-05
- **Author:** cellmin
- **Level:** Dynamic

---

## 목표

remix-dev skill CSS 컨벤션을 기준으로 위반 사항을 수정하고,
모바일 환경에서 우측 슬라이드 드로어 방식의 햄버거 메뉴를 구현한다.

---

## 요구사항

### 기능 요구사항

1. **모바일 햄버거 메뉴**
   - 모바일(< lg): 우측 상단 햄버거(☰) 버튼 표시
   - 버튼 탭 시 우측에서 슬라이드 드로어 오픈
   - 드로어 내에 네비게이션 링크 + 사용자 정보/로그아웃 포함
   - 링크 클릭 시 드로어 자동 닫힘
   - 배경(오버레이) 탭으로 닫힘

2. **CSS 컨벤션 수정 (Critical)**
   - `app.css` import 순서 정렬 (tw-animate-css → 마지막)
   - `@theme inline` 폰트 크기 재정의 추가
   - `shared/styles/layout.css` 신규 생성

3. **시맨틱 HTML 수정**
   - `Header.tsx`: `<nav>` 최외곽 → `<header>` > `<nav>` 구조
   - `<nav>` aria-label 추가

4. **폰트 크기 수정**
   - `PageLayout.tsx`: `text-3xl sm:text-4xl` → 컨벤션 스케일 준수

5. **공통 클래스 추출**
   - `.container-main` 클래스를 `layout.css`에 정의
   - 3곳의 반복 패턴 제거

### 비기능 요구사항

- Mobile-First 원칙 준수 (기본 = 모바일, lg+ 확장)
- 접근성: aria-label (shadcn Sheet의 기본 포커스 트랩/ESC 동작에 위임)
- shadcn/ui 기존 패턴 일관성 유지

---

> **경로 기준:** 모든 파일 경로는 워크스페이스 루트(`haedok-ai/`) 기준.
> 클라이언트 앱 위치: `apps/client/` — 앱 소스: `apps/client/app/`

## 범위 (In Scope)

| 파일 | 작업 |
|------|------|
| `apps/client/app/app.css` | import 순서 + 폰트 크기 재정의 추가 |
| `apps/client/app/shared/styles/layout.css` | 신규 생성, 공통 시맨틱 클래스 정의 |
| `apps/client/app/widgets/layout/Header.tsx` | 시맨틱 구조 + 햄버거 드로어 구현 |
| `apps/client/app/widgets/layout/MobileDrawer.tsx` | 신규 생성, Sheet 기반 드로어 컴포넌트 |
| `apps/client/app/widgets/layout/Footer.tsx` | `.container-main` 적용 |
| `apps/client/app/widgets/layout/PageLayout.tsx` | 폰트 크기 수정 + `.container-main` 적용 |
| shadcn/ui Sheet | `cd apps/client && npx shadcn add sheet` |

## 범위 (Out of Scope)

- 다크모드 대응
- 드로어 내 검색 기능
- 애니메이션 커스터마이징 (shadcn 기본 사용)

---

## 성공 기준

- [ ] 모바일(375px)에서 햄버거 버튼만 표시, 네비 링크 숨김
- [ ] 햄버거 탭 → 우측 드로어 슬라이드 인
- [ ] 드로어 링크 클릭 → 드로어 닫힘 + 페이지 이동
- [ ] 데스크탑(1024px+)에서 기존 인라인 네비 정상 표시
- [ ] `apps/client/app/app.css` import 순서 컨벤션 준수
- [ ] `apps/client/app/shared/styles/layout.css` 존재 + `.container-main` 정의
- [ ] `apps/client/app/widgets/layout/Header.tsx` `<header>` > `<nav>` 구조 적용
- [ ] `apps/client/app/widgets/layout/PageLayout.tsx` 폰트 크기 컨벤션 준수
- [ ] ESC 키로 모바일 드로어 닫힘 (shadcn Sheet 기본 동작)
- [ ] 드로어 오픈 시 포커스가 드로어 내부로 이동 (shadcn Sheet 기본 동작)
- [ ] 드로어 닫힘 후 햄버거 버튼으로 포커스 복귀 (shadcn Sheet 기본 동작)
- [ ] `cd apps/client && npm run typecheck` 통과
- [ ] `cd apps/client && npm run lint` 통과

---

## 기술 스택

- React Router v7 (framework mode)
- Tailwind CSS v4 (Mobile-First)
- shadcn/ui Sheet 컴포넌트
- TypeScript
- lucide-react (Menu, X 아이콘)
