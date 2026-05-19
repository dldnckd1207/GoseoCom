# community-api-connect Design 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/2-design/2026-05-04/community-api-connect.md` |
| 기준 문서 | `docs/pdca/cellmin/2-design/2026-04-29/sfr-101.md`, `apps/server/app/board/*`, 현재 FE 코드 |
| 리뷰 일자 | 2026-05-04 |
| 리뷰어 | Codex |

## 총평

Design 문서는 현재 Mock 기반 커뮤니티 화면을 React Router loader/action과 BE REST API로 전환하는 흐름을 잘 잡고 있다. 타입, endpoint, board_code 매핑, 목록/상세 loader, 댓글 action까지 구현 단위가 구체적이다.

다만 몇 가지 설계는 그대로 구현하면 런타임 또는 타입 문제가 생길 가능성이 있다. 특히 질문 게시글 상세 접근 차단은 현재 순서대로라면 403을 accessDenied 화면으로 바꾸기 전에 loader가 실패할 수 있고, `all` 탭은 전체 페이지네이션이 정확하지 않다.

## 발견 사항

### High - 질문 게시글 상세 접근 차단이 loader 실패로 이어질 수 있음

상세 loader 설계는 `post`와 `commentsData`를 `Promise.all`로 먼저 조회한 뒤 `post.board_code`를 기준으로 `accessDenied`를 계산한다.

```ts
const [post, commentsData] = await Promise.all([
    serverFetch<PostDetail>(request, API_ENDPOINTS.POST(id)),
    serverFetch<PageResult<CommentItem>>(request, API_ENDPOINTS.POST_COMMENTS_LIST(id), ...)
]);
```

BE의 `GET /api/v1/posts/{post_id}`와 `POST /api/v1/posts/{post_id}/comments/list`는 `require_level(UserRole.GUEST)`와 게시판 권한 정책을 거친다. 질문 게시판이 비회원 조회 불가라면 두 API 중 하나가 403을 반환할 수 있으며, 이 경우 `accessDenied`를 계산하기 전에 loader가 에러로 종료된다.

권장 보완:

- `ApiError` 403을 catch해서 `{ post: null, comments: [], accessDenied: true }` 형태의 전용 상태를 반환
- 또는 상세 접근 전에 게시판 권한을 확인할 수 있는 별도 정보가 없다면 403 전용 ErrorBoundary/route state를 설계
- View는 `post`가 없을 수 있는 accessDenied 상태를 처리하도록 타입을 분리

### High - `all` 탭 페이지네이션이 실제 total/page와 맞지 않음

`all` 탭 설계는 접근 가능한 게시판별로 `page: 1, size: 20`을 조회하고 합산한 뒤 `allPosts.length`를 `total`로 반환한다. 이 방식은 각 게시판의 1페이지 안에서만 최신순 병합이 가능하며, 게시판별 20개 이후 데이터는 전체 탭 2페이지에서 누락될 수 있다.

권장 보완:

- MVP로 `all` 탭은 "최신 20개 모음"이라고 명시하고 페이지네이션을 비활성화
- 또는 `page * size`만큼 게시판별 over-fetch 후 병합/slice하고, `total`은 각 응답의 `total` 합산으로 계산
- 어느 방식을 선택하든 loader 반환 `total`, `page`, `size` 의미를 문서에 명시

### Medium - `BOARD_CODE_MAP[t]` 타입 추론 문제 가능성

`const tabs = user ? ['translate', 'question', 'free'] : ['translate', 'free'];`는 일반적으로 `string[]` 또는 넓은 union으로 추론될 수 있다. 이 상태에서 `BOARD_CODE_MAP[t]`는 인덱싱 타입 오류가 날 수 있다.

권장 보완:

```ts
const tabs: Array<Exclude<PostTab, 'all'>> = user
    ? ['translate', 'question', 'free']
    : ['translate', 'free'];
```

또는 `BOARD_CODE_MAP`의 key 타입을 별도 `BoardTab`으로 정의해 loader와 config에서 공유하는 편이 좋다.

### Medium - 댓글 action 에러 UX가 부족함

댓글 action은 빈 content만 처리하고, 비로그인/403/네트워크 오류는 `serverFetch` 예외로 라우트 에러가 될 수 있다. 사용자 입력 기반 action이므로 View에서 표시 가능한 오류 응답으로 바꾸는 설계가 필요하다.

권장 보완:

- action에서 `ApiError`를 catch해 `{ ok: false, error: err.message }` 반환
- 401/403은 "로그인이 필요합니다." 또는 "작성 권한이 없습니다."로 표시
- View에서 `fetcher.data?.error`를 textarea 하단에 렌더링

### Medium - 댓글 작성 성공 후 입력값 초기화 조건 필요

`useFetcher().Form`은 revalidation을 수행하지만 controlled textarea를 자동 초기화하지 않는다. 현재 상세 화면은 `useState` 기반 입력값을 가지고 있으므로 성공 응답을 감지해 `setComment('')`를 호출하는 설계가 필요하다.

권장 보완:

```ts
useEffect(() => {
    if (fetcher.data?.ok) setComment('');
}, [fetcher.data]);
```

### Low - 상세 accessDenied 타입이 `post` 필수 구조와 충돌할 수 있음

현재 View는 로그인 링크에 `post.id`를 사용한다. 403 catch 방식으로 전환하면 `post`를 가져오지 못하는 상태가 생길 수 있으므로 `post` nullable 타입 또는 `postId` 별도 반환이 필요하다.

권장 보완:

```ts
return { post: null, postId: id, comments: [], user, accessDenied: true };
```

### Low - 날짜 포맷 헬퍼 중복 가능성

문서는 각 View 파일에 인라인 헬퍼를 두도록 한다. 이번 범위가 두 View라면 허용 가능하지만, 이후 작성/마이페이지 등에서도 같은 포맷이 필요하면 `shared/lib/date`로 분리하는 편이 낫다. 현재 작업에서는 과한 추상화 없이 인라인 유지도 가능하다.

## 확인 완료 항목

- BE `PostSummaryResponse`, `PostDetailResponse`, `CommentResponse` 필드는 문서의 FE 타입 설계와 대체로 일치
- BE `PageData` 구조는 `{ items, total, page, size }`로 문서의 `PageResult<T>`와 일치
- `POST /api/v1/posts/list`, `GET /api/v1/posts/{post_id}`, `POST /api/v1/posts/{post_id}/comments/list`, `POST /api/v1/posts/{post_id}/comments` 경로가 현재 서버 코드와 일치
- 현재 FE는 목록/상세 모두 Mock import를 사용 중이므로 문서의 제거 방향이 타당함
- `serverFetch`가 `ApiWrappedResponse<T>`에서 `body.data`를 반환하므로 loader 타입 설계와 호환됨

## 권장 보완

- 상세 loader에 403 처리 흐름을 명시하고 View 타입을 nullable 상태까지 포함
- `all` 탭 정책을 "최신 모음" 또는 "정확한 병합 페이지네이션" 중 하나로 확정
- 댓글 action의 `ApiError` catch 및 fetcher error 렌더링 추가
- 댓글 작성 성공 후 textarea 초기화 조건 추가
- `tabs` 배열 타입을 `Array<Exclude<PostTab, 'all'>>`로 명시

## 결론

Design 문서는 API 연결 작업의 큰 구조는 적절하다. 다만 상세 403 처리와 `all` 탭 페이지네이션은 그대로 구현하면 요구사항과 실제 동작이 어긋날 수 있으므로, 구현 전에 설계 문서에 반영하는 것을 권장한다.
