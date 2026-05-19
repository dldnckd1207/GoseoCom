# Review: 커뮤니티 글 상세 페이지 Plan (#99)

**검토일:** 2026-04-30
**검토자:** Codex
**대상 문서:** `docs/pdca/cellmin/1-plan/2026-04-30/community-detail.md`

---

## 총평

요구사항 범위와 성공 기준은 구현 가능한 수준으로 정리되어 있다. Mock 기반 상세 페이지를 먼저 만들고, 이후 loader 교체로 API 전환을 고려한다는 방향도 적절하다.

다만 실제 코드 위치와 로그인 리다이렉트 방식이 문서 일부와 맞지 않아, 구현 전에 정리하지 않으면 작업자가 잘못된 경로 또는 다른 인증 흐름으로 구현할 가능성이 있다.

---

## 주요 확인 사항

### 1. 실제 소스 경로와 문서 경로 불일치

문서의 파일 구조는 `app/...` 기준으로 작성되어 있지만, 실제 소스는 `apps/client/app/...` 아래에 있다.

현재 실제 파일:

- `apps/client/app/routes/_layout.community.$id.tsx`
- `apps/client/app/views/community/mock.ts`
- `apps/client/app/shared/types/post.ts`

문서의 파일 구조 섹션은 아래처럼 실제 경로를 반영하는 편이 좋다.

```text
apps/client/app/
├── routes/
│   └── _layout.community.$id.tsx
├── views/community/
│   ├── CommunityDetailView.tsx
│   ├── mock.ts
│   └── mockComments.ts
└── shared/types/
    └── post.ts
```

### 2. 로그인 버튼 리다이렉트 기준 명확화 필요

성공 기준에는 로그인 버튼 이동이 `/login?redirect=/community/:id`로 되어 있다. 이 방향은 현재 로그인 구현과 맞다.

현재 `LoginView`는 query string의 `redirect` 값을 읽고, OAuth 버튼 클릭 시 `REDIRECT_AFTER_LOGIN_KEY`로 sessionStorage에 저장한다. 따라서 상세 페이지의 로그인 버튼은 다음 형태가 적절하다.

```ts
navigate(`/login?redirect=/community/${post.id}`);
```

또는 `Link`를 쓴다면:

```tsx
<Link to={`/login?redirect=/community/${post.id}`}>로그인하기</Link>
```

### 3. Post 타입 예시 코드 정리 필요

Plan의 Post 타입 확장 예시는 `content`, `viewCount`가 `type Post` 블록 밖에 있는 형태로 보인다. 구현자가 복사해서 참고하기 어렵기 때문에 완성된 타입으로 정리하는 편이 좋다.

권장 형태:

```ts
type Post = {
    id: string;
    title: string;
    tab: Exclude<PostTab, 'all'>;
    era: Exclude<PostEra, 'all'>;
    author: string;
    createdAt: string;
    content: string;
    viewCount: number;
};
```

### 4. `BOARD_CONFIG` 위치 결정 필요

Plan에서는 `BOARD_CONFIG`를 신규로 정의한다고만 되어 있다. Mock 데이터와 분리 가능한 권한 정책이므로 `views/community/config.ts`처럼 별도 파일에 두는 편이 더 명확하다.

단, 작업 범위를 최소화하려면 `views/community/mock.ts`에 함께 export해도 구현상 문제는 없다. 문서에는 둘 중 하나를 확정해서 적는 것이 좋다.

---

## 보완 권장

- 비로그인 댓글 작성 UI는 disabled 상태만 보여줄지, 로그인 이동 CTA를 함께 제공할지 명확히 하면 좋다.
- 댓글 작성은 "실제 저장 없음"으로 되어 있으므로 로그인 상태에서 제출 시 동작을 `preventDefault`만 할지, 입력값을 초기화할지 정리하면 구현 차이가 줄어든다.
- `/community/999` redirect는 `throw redirect('/community')` 방식으로 명시하면 React Router v7 loader 패턴과 맞다.

---

## 결론

Plan은 구현 착수 가능한 수준이다. 우선 수정해야 할 항목은 실제 소스 경로 반영, 로그인 리다이렉트 방식 명확화, Post 타입 예시 정리다.
