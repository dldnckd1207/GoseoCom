# Review: CSS 컨벤션 위반 수정 및 모바일 반응형 햄버거 메뉴 Design

- **Target:** `docs/pdca/cellmin/2-design/2026-05-05/css-convention-mobile-menu.md`
- **Reviewer:** Codex
- **Date:** 2026-05-05

---

## 총평

컴포넌트 분리 방향은 적절하다. `Header.tsx`는 상태와 데스크탑 네비게이션을 담당하고, 모바일 전용 UI를 `MobileDrawer.tsx`로 분리하는 구조도 유지보수에 유리하다.

다만 현재 설계에는 실제 경로 불일치, CSS import 경로 오류, 예시 코드의 누락 import와 미사용 import, 폰트 크기 결정 충돌이 있다. 이 부분을 정리하지 않으면 구현 직후 TypeScript 또는 ESLint에서 실패할 가능성이 높다.

---

## 주요 리뷰 의견

### 1. 변경 파일 경로가 실제 코드 위치와 다름

**Severity:** High

변경 파일 목록이 `app/...` 기준으로 작성되어 있다.

실제 파일은 `apps/client/app/...` 아래에 있다.

**권장 수정**

변경 파일 목록을 다음 기준으로 수정한다.

```text
apps/client/app/app.css
apps/client/app/shared/styles/layout.css
apps/client/app/shared/ui/sheet.tsx
apps/client/app/widgets/layout/Header.tsx
apps/client/app/widgets/layout/MobileDrawer.tsx
apps/client/app/widgets/layout/Footer.tsx
apps/client/app/widgets/layout/PageLayout.tsx
apps/client/app/widgets/layout/index.ts
```

---

### 2. `layout.css` import 상대 경로가 잘못됨

**Severity:** High

설계 문서의 TO-BE 예시는 다음과 같다.

```css
@import "../shared/styles/layout.css";
```

하지만 `app.css`는 `apps/client/app/app.css`에 있고, 신규 파일은 `apps/client/app/shared/styles/layout.css`에 생성될 예정이므로 상대 경로는 다음이 맞다.

```css
@import "./shared/styles/layout.css";
```

이 경로가 틀리면 CSS 빌드 단계에서 import를 해석하지 못한다.

---

### 3. `MobileDrawer.tsx` 예시 코드가 그대로는 lint/typecheck를 통과하지 못함

**Severity:** High

예시 코드에서 `cn(...)`을 사용하지만 `~/shared/lib/cn` import가 없다. 반대로 `X`, `NAV_LINKS`는 import만 있고 사용되지 않는다.

현재 프로젝트 ESLint 설정은 미사용 변수를 error로 처리한다.

**권장 수정**

예시 코드를 다음 방향으로 정리한다.

```tsx
import { Form, NavLink } from 'react-router';

import { LogOut, User } from 'lucide-react';

import { cn } from '~/shared/lib/cn';
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from '~/shared/ui/sheet';
```

`NAV_LINKS`는 props로 받은 `visibleLinks`를 사용하므로 제거한다.

---

### 4. `PageLayout.tsx` 폰트 크기 최종 결정이 문서 내에서 충돌함

**Severity:** Medium

설계 문서에는 다음 선택지가 모두 등장한다.

- CSS 변수 기반: `text-[length:--text-page-title-mobile]`
- Tailwind 유틸 기반: `text-2xl lg:text-[2rem]`
- 최종 결정: `text-[1.75rem] lg:text-[2rem]`

`@theme inline`에 시맨틱 토큰을 추가하는 설계와 최종 결정이 맞물리지 않는다. 컨벤션을 위한 토큰을 추가한다면 실제 사용도 토큰 기준으로 맞추는 편이 낫다.

**권장 수정**

최종 결정을 하나만 남긴다. 예시는 다음과 같다.

```tsx
<h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">
```

구현 전에 Tailwind v4에서 해당 arbitrary value 문법이 정상 생성되는지 확인한다.

---

### 5. `mt-auto`가 동작하기 위한 flex 전제가 누락됨

**Severity:** Medium

`MobileDrawer` 사용자 영역에 `mt-auto`가 있으나, 부모인 `SheetContent`가 flex column인지 문서에서 보장하지 않는다.

**권장 수정**

하단 정렬을 의도한다면 `SheetContent`에 flex 레이아웃을 명시한다.

```tsx
<SheetContent side="right" className="flex h-full w-72 flex-col" id="mobile-menu">
```

---

### 6. `npx shadcn add sheet` 실행 위치가 불명확함

**Severity:** Medium

`components.json`이 `apps/client/components.json`에 있으므로 루트에서 실행하면 의도와 다른 결과가 나올 수 있다.

**권장 수정**

구현 순서 1번을 다음처럼 변경한다.

```bash
cd apps/client
npx shadcn add sheet
```

---

### 7. `index.ts` export 필요성이 불명확함

**Severity:** Low

`MobileDrawer`가 `Header.tsx` 내부에서만 쓰인다면 `widgets/layout/index.ts`에 export할 필요는 낮다. 공개 API로 노출할 계획이 없다면 불필요한 export를 줄이는 편이 좋다.

**권장 수정**

둘 중 하나로 명확히 결정한다.

```text
- Header 내부 전용 컴포넌트라면 index.ts 수정 제외
- 외부 재사용 가능성이 있다면 index.ts export 유지
```

---

## 권장 반영 요약

- 설계 문서 전체 경로를 `apps/client/app/...`로 맞춘다.
- `app.css`의 `layout.css` import를 `./shared/styles/layout.css`로 수정한다.
- `MobileDrawer.tsx` 예시 코드의 import 목록을 실제 사용 기준으로 정리한다.
- `PageLayout.tsx` 폰트 크기 최종안을 하나만 남긴다.
- `SheetContent`에 flex column 전제를 명시한다.
- `shadcn` 실행 위치를 `apps/client`로 명시한다.

