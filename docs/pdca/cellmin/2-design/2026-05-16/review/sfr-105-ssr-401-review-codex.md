# sfr-105-ssr-401 Design 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/2-design/2026-05-16/sfr-105-ssr-401.md` |
| 기준 Plan | `docs/pdca/cellmin/1-plan/2026-05-16/sfr-105-ssr-401.md` |
| 기준 코드 | `apps/client/app/shared/api/server.ts`, `apps/client/app/shared/api/endpoints.ts`, `apps/client/app/routes/_protected.library._index.tsx`, `apps/client/app/routes/_protected.translate.tsx`, `apps/client/app/routes/auth.logout.tsx`, `apps/server/app/auth/router.py` |
| 리뷰 일자 | 2026-05-16 |

## 총평

Design의 핵심 방향은 적절하다. SSR 환경에서는 refresh 성공 후 서버 내부에서 원 요청을 재시도해도 브라우저 쿠키를 갱신할 수 없으므로, `Set-Cookie`를 포함한 redirect로 브라우저가 새 쿠키를 받고 현재 URL을 다시 요청하게 하는 방식이 맞다.

다만 구현 예시는 현재 코드와 대조했을 때 그대로 적용하기 어렵다. `Set-Cookie`를 단일 헤더로 읽는 방식, route catch에서 redirect `Response`가 삼켜지는 문제, query string 누락, 쿠키 누락 시 무한 redirect 가능성이 보정되어야 한다.

## Findings

### High - `refreshRes.headers.get('set-cookie')`는 다중 쿠키 전달에 부적합함

Design은 refresh 성공 후 다음 코드를 제안한다.

```ts
const setCookie = refreshRes.headers.get('set-cookie');
throw redirect(request.url, {
    headers: setCookie ? { 'set-cookie': setCookie } : {},
});
```

현재 BE refresh는 `access_token`, `refresh_token` 두 쿠키를 모두 설정한다. 기존 logout action도 FastAPI의 다중 `Set-Cookie`를 전달하기 위해 `res.headers.getSetCookie?.()`와 `headers.append('Set-Cookie', v)`를 사용한다.

단일 `get('set-cookie')` 방식은 다음 문제가 있다.

- 첫 번째 쿠키만 전달될 수 있다.
- 여러 쿠키가 하나의 문자열로 병합되면 브라우저가 올바르게 해석하지 못할 수 있다.
- refresh token rotation에서 새 refresh token이 누락되면 이후 refresh가 실패할 수 있다.

권장 수정:

```ts
const setCookieHeaders = refreshRes.headers.getSetCookie?.() ?? [];
if (setCookieHeaders.length === 0) {
    throw redirect(loginRedirect);
}

const headers = new Headers({ Location: request.url });
setCookieHeaders.forEach((value) => headers.append('Set-Cookie', value));
throw new Response(null, { status: 302, headers });
```

React Router `redirect()`를 유지하려면 `Headers` 객체를 만들어 append한 뒤 전달한다.

### High - route catch가 redirect `Response`를 삼킬 수 있음

Design은 `serverFetch` 단독 수정이라고 정의한다. 그러나 현재 route 중 일부는 broad catch를 사용한다.

- `apps/client/app/routes/_protected.library._index.tsx`는 모든 예외를 `번역 이력을 불러오지 못했습니다.` 상태로 변환한다.
- `apps/client/app/routes/_protected.translate.tsx`는 `ApiError`가 아닌 예외를 `번역 시작에 실패했습니다.`로 변환한다.

이 경우 `serverFetch`가 `throw redirect(...)`를 해도 redirect가 상위로 전파되지 않는다.

권장 수정:

- Design의 수정 대상에 redirect `Response`를 catch하는 route 보정을 포함한다.
- 모든 `serverFetch` catch에서 다음 가드를 먼저 둔다.

```ts
if (err instanceof Response) throw err;
```

### Medium - login redirect가 query string을 보존하지 않음

Design은 `new URL(request.url).pathname`만 redirect 파라미터에 넣는다.

```ts
const pathname = new URL(request.url).pathname;
const loginRedirect = `/login?redirect=${encodeURIComponent(pathname)}`;
```

이러면 `/library?tab=failed&page=2`에서 세션 만료 시 로그인 후 `/library`로만 돌아간다.

권장 수정:

```ts
const url = new URL(request.url);
const currentPath = `${url.pathname}${url.search}`;
const loginRedirect = `/login?redirect=${encodeURIComponent(currentPath)}`;
```

### Medium - refresh 성공 후 `Set-Cookie` 없음이면 무한 redirect 가능성이 있음

현재 예시는 refresh가 `ok`이면 `Set-Cookie` 유무와 관계없이 현재 URL로 redirect한다. 쿠키가 비어 있으면 다음 요청도 같은 만료 access token으로 들어오고, 다시 refresh와 현재 URL redirect가 반복될 수 있다.

권장 수정:

- refresh 성공 후 `Set-Cookie`가 0개이면 `/login?redirect=...`로 보낸다.
- 테스트에 "refresh 200 but Set-Cookie 없음" 케이스를 추가한다.

### Medium - multipart upload action의 401도 별도 고려가 필요함

`_protected.translate.tsx`의 업로드 1단계는 multipart 때문에 `serverFetch`를 우회하고 직접 `fetch`를 사용한다. Design 범위가 `serverFetch`만이면 업로드 요청의 401은 자동 refresh 대상이 아니다.

현재 문서의 목표가 "SSR loader"로 한정되어 있으면 범위 외라고 명시하면 된다. 하지만 `/translate` 접근 또는 action까지 성공 기준에 포함한다면 multipart 직접 fetch에도 같은 refresh 정책이 필요하다.

권장 수정:

- 이번 범위가 loader only인지, action까지 포함하는지 명확히 나눈다.
- action까지 포함한다면 직접 fetch 경로도 `Response` rethrow 및 refresh 처리 대상에 포함한다.

### Low - JSON 파싱 전 non-JSON 오류 응답 처리 기준이 없음

기존 `serverFetch`도 같은 문제가 있지만, 401 처리 추가 후에도 400/403/404/500 응답에서 항상 `ApiWrappedResponse` JSON이라고 가정한다.

현재 BE 계약상 대부분 wrapped response라면 허용 가능하지만, proxy 오류나 HTML 오류 응답이 오면 `res.json()`에서 다른 예외가 발생한다.

권장 수정:

- 이번 범위에서는 기존 동작 유지로 명시한다.
- 별도 개선으로 `content-type` 또는 JSON parse 실패 시 `ApiError`로 감싸는 방안을 남긴다.

## 권장 구현 스케치

```ts
if (res.status === 401) {
    const url = new URL(request.url);
    const currentPath = `${url.pathname}${url.search}`;
    const loginRedirect = `/login?redirect=${encodeURIComponent(currentPath)}`;

    const refreshRes = await fetch(`${BASE_URL}${API_ENDPOINTS.AUTH_REFRESH}`, {
        method: 'POST',
        headers: { cookie },
    });

    if (!refreshRes.ok) {
        throw redirect(loginRedirect);
    }

    const setCookieHeaders = refreshRes.headers.getSetCookie?.() ?? [];
    if (setCookieHeaders.length === 0) {
        throw redirect(loginRedirect);
    }

    const headers = new Headers({ Location: request.url });
    setCookieHeaders.forEach((value) => headers.append('Set-Cookie', value));
    throw new Response(null, { status: 302, headers });
}
```

route catch 보정:

```ts
} catch (err) {
    if (err instanceof Response) throw err;
    // 기존 에러 처리
}
```

## 테스트 보강안

1. access token 만료 + refresh token 유효: 현재 URL로 302, `access_token`/`refresh_token` `Set-Cookie` 모두 포함
2. refresh token 만료: `/login?redirect=pathname%2Bsearch`로 302
3. `/library?tab=failed&page=2`에서 query string 보존
4. broad catch route에서 redirect `Response`가 rethrow됨
5. refresh 200 + `Set-Cookie` 없음: 현재 URL 무한 redirect가 아니라 로그인으로 이동

## 결론

Design은 해결 방향은 맞지만 구현 예시를 그대로 적용하면 쿠키 누락과 redirect 전파 실패가 발생할 수 있다. 다중 `Set-Cookie` 처리, route catch rethrow, query string 보존, 쿠키 누락 실패 처리를 반영하면 구현 가능한 설계가 된다.
