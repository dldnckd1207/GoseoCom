# Review — 커뮤니티 목록 페이지 Design (#98)

- **Reviewer:** Codex
- **Date:** 2026-04-28
- **Target:** `docs/pdca/cellmin/2-design/2026-04-28/community-list.md`

---

## Findings

### Medium — URL 쿼리 파라미터 정규화 정책이 부족함

- 대상 위치: `URL 쿼리스트링`, `필터 & 페이지네이션 로직`

Design은 `tab`, `era`, `page`의 기본값과 유효 값을 정의하고 있지만, 실제 URL에 잘못된 값이 들어온 경우의 처리 정책이 없다.

예:

- `?tab=unknown`
- `?era=bad`
- `?page=0`
- `?page=-1`
- `?page=abc`
- `?page=999`

현재 필터 코드 예시는 `tab`과 `era`가 이미 유효한 타입이라는 전제에 기대고 있다. 실제 구현에서는 `URLSearchParams.get()` 결과가 `string | null`이므로, 타입 가드와 fallback이 필요하다.

권장:

- `parseTab(value): PostTab`
- `parseEra(value): PostEra`
- `parsePage(value): number`

같은 작은 helper를 둔다.

추가로, `currentPage`가 보정될 때 URL도 `replace`로 보정할지 정책을 정한다. 공유 URL의 일관성을 생각하면 유효하지 않은 값은 `replace`로 정규화하는 편이 좋다.

### Medium — `/community/write`, `/community/:id` 라우트 존재 여부가 설계에 반영되지 않음

- 대상 위치: `글 작성하기 버튼`, 라우트 설계

`handleWriteClick`은 로그인 사용자에게 `/community/write`로 이동하도록 되어 있고, Plan은 게시글 행 클릭 시 `/community/:id` 이동을 성공 기준으로 둔다. 하지만 Design의 파일 구조에는 목록 라우트만 있다.

권장:

- 이번 #98에서 라우트 대상이 없어도 링크만 걸 것인지 명시한다.
- 아니면 다음 파일을 스텁으로 추가하는 것을 설계에 포함한다.
  - `routes/_layout.community.write.tsx`
  - `routes/_layout.community.$id.tsx`

### Medium — mock 데이터 20개는 페이지네이션 목업과 맞지 않음

- 대상 위치: `Mock 데이터`

Design은 mock 데이터를 20개로 계획한다. `PAGE_SIZE = 10`이면 총 2페이지다. 하지만 목업 `docs/designs/client/community.html`은 1, 2, 3 페이지 버튼을 보여준다.

권장:

- 목업과 동일한 페이지네이션 UI를 검증하려면 mock 데이터를 30개 이상으로 늘린다.
- 20개를 유지할 경우, 테스트 전략에서 "페이지 버튼은 데이터 개수에 따라 2개만 표시"라고 명시한다.

### Low — `useRouteLoaderData` 타입 단언을 줄일 수 있음

- 대상 위치: `라우트 파일`

예시 코드는 다음 형태다.

```tsx
const { user } = useRouteLoaderData('routes/_layout') as Awaited<ReturnType<typeof layoutLoader>>
```

동작은 가능하지만 타입 단언에 의존한다. React Router 타입을 활용하면 더 안전하게 작성할 수 있다.

권장 예시:

```tsx
const layoutData = useRouteLoaderData<typeof layoutLoader>('routes/_layout')
const user = layoutData?.user ?? null
```

### Low — 로그인 안내 모달의 후속 액션이 불명확함

- 대상 위치: `글 작성하기 버튼`

비로그인 클릭 시 alert만 띄우고 끝난다. Plan 요구사항에는 "로그인 안내 모달 표시"까지만 있으므로 틀린 설계는 아니다. 다만 기존 `_protected` 라우트는 확인 버튼에서 로그인 페이지로 이동하는 UX를 사용한다.

권장:

- 단순 안내만 할지, 확인 버튼 클릭 시 `/login?redirect=/community/write`로 보낼지 결정한다.
- 로그인 후 복귀 UX를 중요하게 보면 후자가 낫다.

---

## 좋은 점

- `_layout` 부모 loader의 `user`를 재사용하는 설계는 현재 앱 구조와 잘 맞다.
- mock 단계에서 별도 loader 없이 client-side 필터링을 하는 방식은 구현 범위를 줄인다.
- `tab`, `era`, `page`를 URL 상태로 둔 점은 새로고침과 공유 링크 요구사항에 적합하다.
- 타입을 `PostTab`, `PostEra`, `Post`로 분리하는 방향은 이후 API 응답 타입으로 확장하기 좋다.

---

## 제안 수정 요약

- URL 파라미터 parser/type guard와 fallback 정책을 추가한다.
- write/detail 라우트 범위를 명시한다.
- mock 데이터 개수와 페이지네이션 기대값을 맞춘다.
- `useRouteLoaderData` 타입 단언을 줄인다.
- 비로그인 작성 버튼의 로그인 이동 여부를 결정한다.

---

## 재검토 — 2026-04-28 수정본

### 반영 확인

- `/community/:id` 스텁 파일이 파일 구조에 추가됨.
- Mock 데이터가 총 30개로 조정되어 `PAGE_SIZE = 10` 기준 3페이지 검증이 가능해짐.

### 남은 확인 사항

#### Medium — URL 쿼리 파라미터 정규화 정책이 아직 필요함

- 대상 위치: `URL 쿼리스트링`, `필터 & 페이지네이션 로직`

수정본에도 `tab`, `era`, `page`의 기본값과 유효 값만 정의되어 있고, 잘못된 URL 값에 대한 처리 정책은 아직 없다.

예:

- `?tab=bad`
- `?era=unknown`
- `?page=abc`
- `?page=0`
- `?page=999`

권장:

```ts
const parseTab = (value: string | null): PostTab =>
    TAB_KEYS.includes(value as PostTab) ? value as PostTab : 'all'

const parseEra = (value: string | null): PostEra =>
    ERA_KEYS.includes(value as PostEra) ? value as PostEra : 'all'

const parsePage = (value: string | null): number => {
    const parsed = Number(value)
    return Number.isInteger(parsed) && parsed > 0 ? parsed : 1
}
```

그리고 `currentPage`가 `totalPages`를 초과해 보정될 때 URL도 `replace`로 정규화할지 결정한다. 공유 URL의 일관성을 생각하면 잘못된 값은 `replace`로 보정하는 편이 낫다.

#### Low — `useRouteLoaderData` 타입 단언을 줄이는 편이 좋음

- 대상 위치: `라우트 파일`

수정본은 여전히 다음 형태의 타입 단언을 사용한다.

```tsx
const { user } = useRouteLoaderData('routes/_layout') as Awaited<ReturnType<typeof layoutLoader>>
```

권장:

```tsx
const layoutData = useRouteLoaderData<typeof layoutLoader>('routes/_layout')
const user = layoutData?.user ?? null
```

이 방식은 loader data가 없을 가능성까지 처리하므로 구현 중 타입 안정성이 더 좋다.

#### Low — 비로그인 작성 버튼의 후속 액션을 명확히 하면 좋음

- 대상 위치: `글 작성하기 버튼`

수정본은 비로그인 사용자에게 alert만 표시한다. Plan 요구사항에는 부합한다. 다만 기존 `_protected` 라우트는 로그인 필요 안내 후 로그인 페이지로 이동하는 UX를 사용한다.

권장:

- 단순 안내만 할지 유지한다.
- 또는 확인 버튼 클릭 시 `/login?redirect=/community/write`로 이동하도록 설계한다.

로그인 후 복귀 UX를 중요하게 보면 후자가 더 자연스럽다.
