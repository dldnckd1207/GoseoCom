# Review: 커뮤니티 글 작성 화면 UI 정렬 Design (#100)

**검토일:** 2026-05-14  
**검토자:** Codex  
**대상 문서:** `docs/pdca/cellmin/2-design/2026-05-14/community-write.md`  
**기준 문서:** `docs/pdca/cellmin/1-plan/2026-05-11/community-write.md`, 현재 FE 코드

---

## 총평

Design 문서는 Plan에서 확정한 범위를 실제 구현 단위로 잘 풀고 있다. 변경 파일을 FE 3개로 한정하고, `?board` 파싱 → `defaultBoard` 결정 → 라디오 버튼 기본 선택 → action submit contract 유지 흐름도 현재 React Router 구조와 맞다.

특히 비로그인 redirect에서 `pathname + search`를 유지하는 설계, `boards` 빈 배열 fallback, 목록 탭에서 작성 화면으로 현재 board를 전달하는 설계는 Plan의 보강 사항을 잘 반영한다.

다만 그대로 구현하면 일부 UX 또는 상태 동기화 문제가 생길 수 있는 지점이 있다. 핵심은 `defaultChecked`가 첫 렌더에만 적용된다는 점, 숨김 radio의 키보드 포커스 표시 기준, 그리고 현재 `CommunityListView`의 비로그인 흐름이 `openModal` 확인 버튼 안에서 navigate된다는 점이다.

---

## 발견 사항

### Medium - `defaultChecked`는 같은 라우트 내 query 변경에 재동기화되지 않을 수 있음

Design은 radio input에 다음 방식으로 기본 선택값을 적용한다.

```tsx
defaultChecked={b.board_code === defaultBoard}
```

이 방식은 초기 렌더에는 단순하고 적절하다. 다만 같은 `/community/write` 라우트 안에서 `?board`만 바뀌고 컴포넌트가 재사용되는 경우, uncontrolled radio의 선택 상태가 loader의 새 `defaultBoard`와 자동으로 동기화되지 않을 수 있다.

구현 안정성을 높이려면 아래 중 하나를 Design에 명시하는 것이 좋다.

- 라디오 그룹 또는 `Form`에 `key={defaultBoard}`를 부여해 `defaultBoard` 변경 시 다시 마운트한다.
- `useState(defaultBoard)` 기반 controlled radio로 구현하고, `defaultBoard` 변경 시 state를 동기화한다.

이번 화면은 작성 페이지 진입 시 기본값을 정하는 목적이 강하므로, 최소 변경으로는 `key={defaultBoard}` 방식이 충분하다.

### Medium - 숨김 radio의 키보드 포커스 표시 기준이 빠져 있음

`sr-only peer` radio와 `peer-checked` 스타일 조합은 접근성 방향이 좋다. 하지만 실제 버튼처럼 보이는 `span`에 focus-visible 스타일이 없으면 키보드 사용자가 현재 포커스 위치를 파악하기 어렵다.

예시:

```tsx
<span className="
  px-4 py-2 rounded-lg font-medium transition-colors
  bg-gray-100 text-gray-700
  peer-checked:bg-blue-600 peer-checked:text-white
  peer-focus-visible:ring-2 peer-focus-visible:ring-blue-600 peer-focus-visible:ring-offset-2
">
```

Design의 접근성 설명에 focus-visible ring 기준을 추가하는 것을 권장한다.

### Low - 비로그인 작성 버튼 흐름은 현재 `openModal` 구조를 명시하는 편이 좋음

Design의 `CommunityListView` 변경 예시는 비로그인 redirect도 같은 URL 규칙을 사용한다고 설명한다. 방향은 맞다.

다만 현재 실제 코드는 비로그인 상태에서 즉시 `navigate`하지 않고 `openModal`을 띄운 뒤 확인 버튼에서 `/login?redirect=...`로 이동한다. 구현자가 헷갈리지 않도록 "비로그인 modal 확인 버튼의 navigate URL도 동일한 redirect 값으로 변경"이라고 명시하는 편이 좋다.

권장 예시:

```ts
const writePath = currentTab === 'all'
    ? '/community/write'
    : `/community/write?board=${currentTab}`;

if (!user) {
    openModal({
        type: 'alert',
        message: '로그인이 필요한 서비스입니다.',
        buttons: [{ label: '확인', onClick: () => navigate(`/login?redirect=${encodeURIComponent(writePath)}`) }],
    });
    return;
}

navigate(writePath);
```

### Low - board code를 URL에 넣을 때 encode 기준을 맞추면 더 안전함

현재 board code가 `translation`, `questions`, `free`처럼 안전한 값이면 문제가 없다. 그래도 URL query를 직접 문자열 보간하는 대신 `URLSearchParams` 또는 `encodeURIComponent(currentTab)`를 쓰는 기준을 두면 이후 board code 형식이 바뀌어도 안전하다.

예시:

```ts
const writePath = currentTab === 'all'
    ? '/community/write'
    : `/community/write?board=${encodeURIComponent(currentTab)}`;
```

---

## 확인 완료 항목

- `defaultBoard`를 loader 반환값에 추가하는 방식은 Plan의 N-2와 맞다.
- action submit contract는 `board_code`, `title`, `content` 그대로 유지된다.
- 비로그인 loader redirect에서 `pathname + search`를 redirect query로 넘기는 방식은 현재 `LoginView`의 `useSearchParams().get('redirect')` 흐름과 호환된다.
- `isSafeRedirect`는 `/community/write?board=...` 형태를 허용하므로 로그인 후 복귀 경로로 사용할 수 있다.
- `boards.length === 0` 시 안내 메시지와 제출 버튼 비활성화를 처리하는 설계는 Plan의 F-7과 맞다.
- `max-w-4xl`, 카드 헤더 분리, 시대 필드 제외 후 글 유형 전체 폭 배치는 목업 정렬 목표와 맞다.

---

## 권장 보완

- radio 기본 선택 동기화를 위해 `key={defaultBoard}` 또는 controlled state 기준 추가
- `peer-focus-visible:ring-*` 스타일 기준을 접근성 항목에 추가
- 비로그인 작성 버튼은 현재 `openModal` 확인 버튼 안의 navigate URL을 바꾸는 방식이라고 명시
- `?board=${currentTab}` 생성 시 `encodeURIComponent` 또는 `URLSearchParams` 사용 기준 추가

---

## 결론

Design 문서는 구현 착수 가능한 수준이다. 위 보완 사항은 구조를 바꾸는 내용이 아니라 구현 안정성과 접근성 품질을 높이는 세부 기준이다. 특히 `defaultChecked` 재동기화와 focus-visible 스타일은 구현 전에 문서에 반영해두는 것을 권장한다.
