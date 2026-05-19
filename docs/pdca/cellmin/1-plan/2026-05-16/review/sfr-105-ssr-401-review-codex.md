# sfr-105-ssr-401 Plan 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/1-plan/2026-05-16/sfr-105-ssr-401.md` |
| 관련 Design | `docs/pdca/cellmin/2-design/2026-05-16/sfr-105-ssr-401.md` |
| 기준 코드 | `apps/client/app/shared/api/server.ts`, `apps/client/app/routes/_protected.library._index.tsx`, `apps/client/app/routes/_protected.translate.tsx`, `apps/client/app/routes/auth.logout.tsx`, `apps/server/app/auth/router.py` |
| 리뷰 일자 | 2026-05-16 |

## 총평

Plan의 문제 정의와 방향은 적절하다. SSR loader에서 access token 만료 시 refresh를 시도하고, 새 쿠키를 브라우저에 심기 위해 redirect 응답으로 `Set-Cookie`를 전달하는 접근은 현재 구조에서 현실적인 해결책이다.

다만 "serverFetch 1개 파일만 변경"이라는 범위는 현재 route 코드와 맞지 않는다. 일부 loader/action이 `serverFetch`에서 던진 `Response`를 catch 후 일반 에러 결과로 바꾸고 있어, refresh redirect가 실제 브라우저까지 전달되지 않을 수 있다. 또한 다중 `Set-Cookie` 처리와 query string 보존이 성공 기준에 포함되어야 한다.

## Findings

### High - `serverFetch` 단독 수정 범위가 실제 route catch 구조와 충돌함

Plan은 수정 범위를 `apps/client/app/shared/api/server.ts` 1개 파일로 제한하고, 개별 route loader 수정은 범위 외로 둔다.

하지만 현재 코드에는 broad catch가 존재한다.

- `apps/client/app/routes/_protected.library._index.tsx`: `catch { ... }`로 모든 예외를 목록 로딩 실패 상태로 변환
- `apps/client/app/routes/_protected.translate.tsx`: `catch (err)`에서 `Response` redirect도 일반 실패 응답으로 변환 가능

이 상태에서 `serverFetch`가 `throw redirect(...)`를 해도 해당 route가 이를 삼켜버리면 브라우저 redirect가 발생하지 않는다.

권장 수정:

- Plan 범위를 "serverFetch + Response redirect를 삼키는 일부 route catch 보정"으로 확장한다.
- route catch에서는 다음 패턴을 명시한다.

```ts
} catch (err) {
    if (err instanceof Response) throw err;
    // 기존 에러 처리
}
```

### High - 다중 `Set-Cookie` 전달 성공 기준이 빠져 있음

BE refresh는 `access_token`, `refresh_token`을 모두 쿠키로 내려준다. refresh token rotation 구조이므로 두 쿠키가 모두 브라우저에 전달되어야 다음 요청과 이후 refresh가 안정적으로 동작한다.

Plan의 성공 기준은 "자동 갱신 후 정상 렌더링"만 있어 첫 요청 렌더링은 통과해도 refresh token rotation 누락을 놓칠 수 있다.

권장 수정:

- 성공 기준에 "`access_token`과 `refresh_token`의 `Set-Cookie`가 모두 브라우저 응답에 전달됨"을 추가한다.
- 구현 메모에 `headers.get('set-cookie')` 단일 조회가 아니라 `getSetCookie()`와 `Headers.append('Set-Cookie', ...)`를 사용한다고 명시한다.

### Medium - 현재경로 redirect가 query string 보존을 요구하지 않음

Plan은 `/login?redirect=현재경로`라고 표현하지만, Design 예시는 pathname만 사용한다. `/library?tab=failed&page=2` 같은 SSR 페이지에서 query가 사라지면 사용자가 보던 상태로 돌아가지 못한다.

권장 수정:

- "현재경로"를 `pathname + search`로 정의한다.
- 성공 기준에 query string 보존 케이스를 추가한다.

### Medium - refresh 성공이나 `Set-Cookie` 누락 시의 실패 정책이 필요함

refresh 응답이 2xx인데 `Set-Cookie`가 없으면 현재 URL로 redirect해도 다음 요청에서 다시 401이 발생할 수 있다. 이 경우 무한 redirect 루프가 될 수 있으므로 Plan 수준에서 실패 처리 기준이 필요하다.

권장 수정:

- refresh 성공 후 전달할 `Set-Cookie`가 없으면 `/login?redirect=...`로 보낸다.
- 또는 명시적 에러로 처리하되, 자기 자신으로 redirect하지 않는다는 조건을 둔다.

### Low - 테스트 전략이 수동 검증에 치우쳐 있음

토큰 갱신 흐름은 헤더 전달과 redirect throw 전파가 핵심이다. 수동 테스트만으로는 route catch가 redirect를 삼키는 문제나 `Set-Cookie` 두 개 전달 여부를 놓치기 쉽다.

권장 테스트:

- `401 -> refresh 200 -> 현재 URL redirect + access/refresh Set-Cookie 모두 포함`
- `401 -> refresh 401 -> /login?redirect=pathname+search`
- route catch가 `Response`를 rethrow하는지 확인
- refresh 2xx + `Set-Cookie` 없음이면 무한 redirect하지 않음

## 권장 Plan 보정안

1. 범위를 `serverFetch` 단독에서 `serverFetch + redirect Response를 삼키는 route catch 보정`으로 수정한다.
2. 다중 `Set-Cookie` 전달을 명시 성공 기준에 추가한다.
3. redirect 파라미터는 `pathname + search`를 보존한다고 정의한다.
4. refresh 성공이나 쿠키 누락 시 자기 자신으로 redirect하지 않는 실패 정책을 추가한다.
5. 수동 테스트 외에 redirect 헤더와 route catch 전파를 검증하는 테스트를 추가한다.

## 결론

Plan의 방향은 맞지만 현재 코드베이스 기준으로는 범위가 너무 좁다. route catch 보정과 다중 `Set-Cookie` 전달을 Plan에 포함해야 실제 SSR 401 refresh 문제를 안정적으로 닫을 수 있다.
