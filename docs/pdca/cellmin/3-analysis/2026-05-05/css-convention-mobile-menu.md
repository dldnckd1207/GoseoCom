# Check Analysis: CSS 컨벤션 위반 수정 및 모바일 반응형 햄버거 메뉴

- **Feature:** css-convention-mobile-menu
- **Redmine:** #107
- **Date:** 2026-05-05
- **Author:** cellmin
- **기준:** remix-dev skill 컨벤션

---

## 종합 점수: 92%

| 영역 | 비중 | 점수 | 환산 |
|------|------|------|------|
| 기능 완성도 | 25%* | 95 | 23.75 |
| 코드 품질 | 25%* | 88 | 22.00 |
| 보안 | 25%* | 95 | 23.75 |
| 성능 | 12.5%* | 90 | 11.25 |
| 문서화 | 12.5%* | 88 | 11.00 |
| **합계** | **100%** | — | **91.75 → 92%** |

> *테스트 영역은 Plan 범위 외(프로젝트 전반 테스트 부재)로 제외 후 나머지 비중 정규화.

---

## 1. 기능 완성도 — 95/100

### Plan 성공 기준 체크

| 항목 | 상태 |
|------|------|
| 모바일(375px) 햄버거만 표시, 네비 숨김 | ✅ `lg:hidden` / `hidden lg:flex` |
| 햄버거 탭 → 우측 Sheet 슬라이드 인 | ✅ shadcn Sheet `side="right"` |
| 드로어 링크 클릭 → 닫힘 + 이동 | ✅ `onClick={onClose}` |
| 배경(오버레이) 탭으로 닫힘 | ✅ shadcn Sheet 기본 동작 |
| 데스크탑(1024px+) 인라인 네비 표시 | ✅ `hidden lg:flex` |
| `app.css` import 순서 컨벤션 준수 | ✅ tw-animate-css 마지막 |
| `shared/styles/layout.css` + `.container-main` | ✅ 생성 완료 |
| `Header.tsx` `<header>` > `<nav>` 구조 | ✅ |
| `PageLayout.tsx` 폰트 크기 컨벤션 | ✅ CSS 변수 arbitrary value |
| ESC/포커스 접근성 | ✅ shadcn Sheet 기본 동작 |
| `typecheck` 통과 | ✅ |
| `lint` 통과 (수정 파일) | ✅ |

**감점 요인 (-5):** 로그아웃 버튼에 `onClick={onClose}`가 있으나, Form POST 제출 후 리다이렉트가 발생하므로 실질적으로 무의미. 기능 정확성 마이너 이슈.

---

## 2. 코드 품질 — 88/100

### FSD 아키텍처 준수 ✅

| 항목 | 평가 |
|------|------|
| `MobileDrawer.tsx` → `widgets/layout/` 위치 | ✅ |
| `layout.css` → `shared/styles/` 위치 | ✅ |
| `sheet.tsx` → `shared/ui/` 위치 | ✅ |
| MobileDrawer 의존성 방향 (widget → shared) | ✅ |
| Header → MobileDrawer (같은 slice 내 상대 경로) | ✅ |

### import 순서 (coding-conv.md) ✅

**Header.tsx:**
```
1. React (useState)
2. React Router (Form, NavLink)
3. Third-party (lucide-react)
6. Shared (~/shared/config, ~/shared/lib)
   상대경로 (./MobileDrawer)  ← ESLint auto-fix 위치
7. Types (import type)
```

**MobileDrawer.tsx:**
```
1+2. React Router (Form, NavLink)
3. Third-party (lucide-react)
6. Shared (~/shared/lib/cn, ~/shared/ui/sheet)
7. Types (import type)
```

### 발견된 이슈

**🟡 Minor #1 — Header.tsx:14 이중 빈 줄**
```tsx
import type { User as UserType } from '~/shared/types/auth';
                                    ← 빈 줄 2개
interface Props {
```
→ 빈 줄 1개로 정리 필요.

**🟡 Minor #2 — 로고 텍스트 `text-xl` 사용**
```tsx
// Header.tsx:29
className="flex items-center gap-2 text-xl font-semibold ..."
```
`@theme inline` 재정의 범위에 `text-xl`이 포함되지 않아 Tailwind 기본값(1.25rem)을 그대로 사용한다. 재정의된 `text-lg`도 1.25rem으로 동일해 시각적으로 동일하나, 의미론적으로 `text-lg`(= `--text-card-title` 20px)로 통일하는 것이 컨벤션 일관성에 유리하다.

**🟡 Minor #3 — MobileDrawer nav 링크 폰트 크기 미명시**
```tsx
'px-4 py-3 rounded-lg font-medium transition-colors'
```
`--text-header-menu`(20px) 또는 `text-lg` 명시가 없어 부모 상속값(SheetContent `text-sm`)에 의존한다. 컨벤션상 명시 권장.

### CSS 컨벤션 준수 ✅

| 항목 | 평가 |
|------|------|
| import 순서: tailwindcss → shadcn → font → layout.css → tw-animate-css | ✅ |
| `@layer base` 사용 (글로벌 리셋) | ✅ |
| `@layer components` 미사용 (금지) | ✅ |
| `layout.css` `@apply` 사용 (shared/styles/) | ✅ |
| Mobile-First 원칙 (기본 모바일, lg+ 확장) | ✅ |
| 시맨틱 HTML `<header>` > `<nav>` | ✅ |
| `aria-label`, `aria-expanded`, `aria-controls` 적용 | ✅ |
| `@theme inline` 폰트 크기 재정의 14종 추가 | ✅ |

---

## 3. 테스트 — 범위 외

프로젝트 전반에 테스트 파일 없음. 이번 작업 Plan에 테스트 항목 미포함. 비중 재배분 처리.

---

## 4. 보안 — 95/100

| 항목 | 평가 |
|------|------|
| 사용자 입력 없음 (네비게이션 UI) | — 해당 없음 |
| `user.name` 렌더링 → React 자동 이스케이프 | ✅ XSS 안전 |
| 로그아웃 Form POST 방식 유지 | ✅ CSRF 안전 |
| 민감정보 console.log 없음 | ✅ |

**감점 요인 (-5):** 미인증 사용자가 `/translate` 등 minLevel > 0 링크에 접근하는 가드는 기존 `_protected.tsx` route에서 처리. 이번 변경으로 새로운 취약점 없음.

---

## 5. 성능 — 90/100

| 항목 | 평가 |
|------|------|
| 드로어 상태 로컬 `useState` — 전역 스토어 불필요 | ✅ |
| `lg:hidden` / `hidden lg:flex` — CSS만으로 처리, 추가 JS 없음 | ✅ |
| shadcn Sheet → Portal 기반, DOM 오버헤드 최소화 | ✅ |
| SheetContent `data-[side=right]:h-full` 내장 → `h-full` 추가 불필요 | ✅ |
| SheetFooter `mt-auto` 내장 → 별도 처리 불필요 | ✅ |

**감점 요인 (-10):** `onClick={() => setIsOpen(true)}` 인라인 화살표 함수로 렌더마다 새 함수 생성. 현 규모에서 실질적 영향 없으나 `useCallback`으로 최적화 가능.

---

## 6. 문서화 — 88/100

| 항목 | 평가 |
|------|------|
| PDCA Plan 문서 | ✅ |
| PDCA Design 문서 | ✅ |
| Codex 리뷰 반영 | ✅ |
| 코드 내 의도 주석 (`{/* 데스크탑 네비게이션 (lg+) */}`) | ✅ |
| `layout.css` 주석 | ✅ |

**감점 요인 (-12):** `app.css` 폰트 크기 재정의 블록에 주석이 있으나, `text-xl` 이상의 Tailwind 기본값과 충돌 가능성(text-lg=text-xl=1.25rem)에 대한 경고 주석 없음.

---

## 개선 항목 (Act 대상)

| 우선순위 | 파일 | 이슈 | 작업 |
|----------|------|------|------|
| 🟡 Minor | `Header.tsx:14` | 이중 빈 줄 | 빈 줄 1개로 정리 |
| 🟡 Minor | `Header.tsx:29` | `text-xl` → `text-lg` 교체 | 컨벤션 일관성 |
| 🟡 Minor | `MobileDrawer.tsx:40` | nav 링크 폰트 크기 미명시 | `text-lg` 추가 |
| 🟡 Minor | `MobileDrawer.tsx:64` | 로그아웃 `onClick={onClose}` 불필요 | 제거 |

---

## 결론

**종합 92% — 품질 목표(90%) 달성.**

4개의 Minor 이슈만 존재하며 모두 CSS/스타일 일관성 관련. 기능, 보안, 아키텍처 측면에서 remix-dev 컨벤션을 충분히 준수하고 있음.
Act 단계에서 Minor 이슈를 수정하거나, 현 상태로 완료 처리해도 무방함.
