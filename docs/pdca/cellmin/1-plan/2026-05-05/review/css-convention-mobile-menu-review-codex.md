# Review: CSS 컨벤션 위반 수정 및 모바일 반응형 햄버거 메뉴 Plan

- **Target:** `docs/pdca/cellmin/1-plan/2026-05-05/css-convention-mobile-menu.md`
- **Reviewer:** Codex
- **Date:** 2026-05-05

---

## 총평

계획의 목표와 성공 기준은 명확하다. 모바일 햄버거 메뉴, CSS 컨벤션 수정, 시맨틱 HTML 정리, 공통 레이아웃 클래스 추출이 같은 범위 안에서 잘 묶여 있다.

다만 현재 문서는 실제 모노레포 구조와 경로가 맞지 않아 Do 단계에서 잘못된 위치에 파일을 생성하거나 수정할 위험이 있다. 구현 전에 경로와 검증 명령을 `apps/client` 기준으로 정리하는 것이 필요하다.

---

## 주요 리뷰 의견

### 1. 대상 파일 경로가 실제 구조와 다름

**Severity:** High

문서의 In Scope 경로가 모두 `app/...`로 작성되어 있다.

```text
app/app.css
app/shared/styles/layout.css
app/widgets/layout/Header.tsx
```

실제 코드 위치는 다음과 같다.

```text
apps/client/app/app.css
apps/client/app/shared/styles/layout.css
apps/client/app/widgets/layout/Header.tsx
```

구현자가 문서만 보고 작업하면 루트에 `app/` 디렉터리를 새로 만들거나 파일을 찾지 못할 수 있다.

**권장 수정**

In Scope 표와 성공 기준의 파일 경로를 모두 `apps/client/app/...` 기준으로 변경한다.

---

### 2. shadcn 명령 실행 위치가 명시되지 않음

**Severity:** Medium

`shadcn/ui Sheet` 컴포넌트 추가가 범위에 포함되어 있지만, 모노레포 구조에서 어느 디렉터리에서 실행해야 하는지 명시되어 있지 않다.

현재 `components.json`은 `apps/client/components.json`에 있으므로 실행 위치가 중요하다.

**권장 수정**

다음처럼 명령을 명확히 적는다.

```bash
cd apps/client
npx shadcn add sheet
```

---

### 3. 검증 명령이 성공 기준에 부족함

**Severity:** Medium

성공 기준에는 TypeScript 타입 에러 없음이 포함되어 있지만 실제 실행 명령이 없다. 설계 문서에는 `npm run typecheck`가 있으나, Plan에도 작업 완료 기준으로 명확히 들어가는 편이 좋다.

**권장 수정**

성공 기준에 다음을 추가한다.

```text
- [ ] `cd apps/client && npm run typecheck` 통과
- [ ] 필요 시 `cd apps/client && npm run lint` 통과
```

---

### 4. 접근성 요구사항이 다소 추상적임

**Severity:** Low

비기능 요구사항에 `keyboard navigation`이 있으나, Sheet가 제공하는 기본 동작에 기대는 것인지 별도 검증이 필요한지 불분명하다.

**권장 수정**

검증 항목에 다음을 추가하면 Do 단계에서 확인하기 쉽다.

```text
- [ ] ESC 키로 모바일 드로어 닫힘
- [ ] 드로어 오픈 시 포커스가 드로어 내부로 이동
- [ ] 드로어 닫힘 후 햄버거 버튼으로 포커스 복귀
```

---

## 권장 반영 요약

- 모든 대상 경로를 `apps/client/app/...`로 수정한다.
- `shadcn` 실행 위치를 `apps/client`로 명시한다.
- Plan 성공 기준에 `typecheck`와 가능하면 `lint` 명령을 추가한다.
- 접근성 성공 기준을 키보드 동작 단위로 구체화한다.

