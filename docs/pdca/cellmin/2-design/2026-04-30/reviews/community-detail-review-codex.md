# Review: 커뮤니티 글 상세 페이지 Design (#99)

**검토일:** 2026-04-30
**검토자:** Codex
**대상 문서:** `docs/pdca/cellmin/2-design/2026-04-30/community-detail.md`

---

## 총평

loader에서 데이터와 권한을 처리하고 View는 props 기반 렌더링만 담당하도록 나눈 구조는 적절하다. API 전환 시 loader만 교체한다는 목표에도 잘 맞는다.

다만 예시 코드 일부가 현재 코드베이스와 정확히 맞지 않는다. 특히 `getUser(request)` 함수는 존재하지 않고, 로그인 리다이렉트 설명이 현재 `LoginView`의 동작과 다르게 읽힐 수 있다.

---

## 주요 확인 사항

### 1. 실제 소스 경로 반영 필요

문서의 아키텍처 섹션은 상대 경로만 적고 있어 큰 문제는 아니지만, 실제 프로젝트 루트 기준으로는 `apps/client/app/...` 아래에 구현해야 한다.

현재 실제 상세 라우트 스텁:

```text
apps/client/app/routes/_layout.community.$id.tsx
```

구현 대상 파일을 명확히 적으면 Plan 문서와 Design 문서 간 혼선을 줄일 수 있다.

### 2. `getUser(request)`는 실제 코드에 없음

Design 예시에는 다음 코드가 있다.

```ts
const user = await getUser(request);
```

현재 코드베이스에는 `getUser` 헬퍼가 없고, 기존 라우트들은 아래 패턴을 사용한다.

```ts
try {
    const user = await serverFetch<User>(request, API_ENDPOINTS.ME);
    return { user };
} catch (err) {
    if (err instanceof ApiError && err.status === 401) return { user: null };
    return { user: null };
}
```

상세 라우트 설계에도 실제 import와 `try/catch` 예시를 넣는 편이 좋다.

필요 import:

```ts
import { redirect, useLoaderData } from 'react-router';

import { ApiError } from '~/shared/api/client';
import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { serverFetch } from '~/shared/api/server';

import type { User } from '~/shared/types/auth';
```

### 3. 로그인 리다이렉트 설명 보정 필요

Design에는 "로그인 버튼 -> `/login` + sessionStorage에 `REDIRECT_AFTER_LOGIN_KEY` 저장"이라고 되어 있다.

하지만 현재 구현은 로그인 페이지에 진입할 때 바로 sessionStorage에 저장하지 않는다. `LoginView`가 `/login?redirect=...`의 query 값을 읽고, OAuth 버튼 클릭 시 sessionStorage에 저장한다.

따라서 상세 페이지의 버튼 동작은 다음처럼 설계하는 편이 현재 구조와 맞다.

```tsx
<Link to={`/login?redirect=/community/${post.id}`}>로그인하기</Link>
```

상세 페이지에서 직접 sessionStorage를 쓰는 구현은 기존 인증 흐름과 책임이 겹칠 수 있다.

### 4. `BOARD_CONFIG` 위치는 확정 권장

문서에는 `views/community/mock.ts` 또는 별도 상수라고 되어 있다. 권한 정책은 Mock 게시글 데이터와 성격이 다르므로 별도 파일을 권장한다.

권장:

```text
apps/client/app/views/community/config.ts
```

예시:

```ts
import type { PostTab } from '~/shared/types/post';

export const BOARD_CONFIG: Record<
    Exclude<PostTab, 'all'>,
    { label: string; requiresLogin: boolean }
> = {
    translate: { label: '번역', requiresLogin: false },
    question: { label: '질문', requiresLogin: true },
    free: { label: '자유', requiresLogin: false },
};
```

### 5. 댓글 작성 UI 동작 정의 필요

Design은 로그인 여부에 따른 textarea/button 상태를 설명하지만, 로그인 사용자가 댓글 작성 버튼을 눌렀을 때의 UI-only 동작이 명확하지 않다.

아래 중 하나로 정리하면 구현 차이를 줄일 수 있다.

- `onSubmit`에서 `preventDefault`만 수행한다.
- `preventDefault` 후 입력값을 초기화한다.
- 저장 미지원 안내 모달 또는 메시지를 보여준다.

현재 요구사항이 "실제 저장 없음"이므로 가장 단순한 방식은 `preventDefault`만 수행하는 것이다.

---

## 보완 권장

- `meta({ data })`는 현재 설계처럼 optional 처리하는 것이 적절하다.
- `params.id`는 redirect 후에는 존재한다고 볼 수 있지만, `const postId = params.id; if (!postId) throw redirect('/community');`처럼 먼저 좁히면 non-null assertion을 줄일 수 있다.
- 댓글이 없는 게시글에 대한 empty state 문구를 UI 설계에 추가하면 좋다.
- accessDenied 화면에도 "목록으로" 이동 링크를 제공할지 명확히 정하면 사용성이 좋아진다.

---

## 결론

Design의 구조는 적절하다. 구현 전에는 `getUser` 예시를 실제 `serverFetch` 패턴으로 바꾸고, 로그인 버튼은 `/login?redirect=/community/${post.id}`로 이동하도록 명확히 정리하는 것이 좋다.
