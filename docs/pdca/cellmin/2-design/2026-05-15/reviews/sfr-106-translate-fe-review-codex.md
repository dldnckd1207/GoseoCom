# sfr-106-translate-fe Design 리뷰 - Codex

| 항목 | 내용 |
|------|------|
| 리뷰 대상 | `docs/pdca/cellmin/2-design/2026-05-15/sfr-106-translate-fe.md` |
| 기준 Plan | `docs/pdca/cellmin/1-plan/2026-05-15/sfr-106-translate-fe.md` |
| 기준 코드 | `apps/client/app/shared/api/server.ts`, `apps/client/app/shared/api/client.ts`, `apps/server/app/translate/router.py`, `apps/server/app/translate/schemas.py`, `apps/server/app/translate/pipeline/runner.py` |
| 리뷰 일자 | 2026-05-15 |

## 총평

Design은 React Router action에서 업로드와 번역 시작을 처리하고, 클라이언트에서 결과를 폴링하는 구조를 제안한다. 쿠키 인증이 필요한 multipart 업로드를 SSR action에서 처리하려는 방향은 현재 코드베이스와 잘 맞는다.

다만 실제 BE 상태 모델과 일부 코드 예시가 맞지 않는다. `NO_TEXT`를 Book terminal status로 가정한 점, Vite 환경에서 `process.env`를 사용한 점, `setInterval` 기반 폴링의 중첩 요청 가능성은 구현 전에 수정하는 것이 좋다.

## Findings

### High - `NO_TEXT`를 Book 상태로 처리하는 폴링 로직은 실제 BE와 맞지 않음

Design은 terminal status에 `NO_TEXT`를 포함하고, `data.status === "NO_TEXT"`일 때 `phase = "no_text"`로 전환한다.

그러나 실제 BE는 OCR 텍스트가 없을 때 다음처럼 처리한다.

- `page.status = "NO_TEXT"`
- `book.status = "COMPLETED"`

따라서 `data.status === "NO_TEXT"` 분기는 실행되지 않는다.

권장 수정:

```ts
const BOOK_TERMINAL = new Set(['COMPLETED', 'FAILED']);

if (data.status === 'COMPLETED') {
    setResult(data);
    const hasNoText = data.pages.some((page) => page.status === 'NO_TEXT');
    setPhase(hasNoText ? 'no_text' : 'completed');
}

if (data.status === 'FAILED') {
    setPhase('failed');
}
```

`no_text` 화면에서도 필요하면 `setResult(data)`를 유지해 원본 OCR/페이지 상태를 디버깅하거나 이후 UI 확장에 사용할 수 있다.

### Medium - `process.env`는 현재 client 코드 패턴과 맞지 않음

Design의 action 예시는 `process.env.VITE_API_BASE_URL`을 사용한다. 현재 client 코드에서는 `import.meta.env.VITE_API_BASE_URL`을 사용한다.

권장 수정:

```ts
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
```

또는 중복을 줄이려면 `serverFetch`의 BASE_URL을 재사용할 수 있는 helper를 분리하는 방식도 가능하다. 다만 이번 범위에서는 route action 내부 상수로 두는 것이 가장 작다.

### Medium - `setInterval` 폴링은 요청 중첩 가능성이 있음

현재 예시는 3초마다 무조건 `apiClient.get`을 실행한다. 네트워크 지연이나 서버 지연으로 이전 요청이 끝나기 전에 다음 interval이 실행되면 중복 요청과 상태 경합이 생길 수 있다.

권장 수정:
- `setTimeout` 재귀 방식으로 요청 완료 후 다음 polling 예약
- 또는 `isPollingRef`로 in-flight 상태일 때 다음 tick skip
- 새 파일 선택 시 기존 `bookId`, `result`, `error`, timeout/interval 정리

예시:

```ts
useEffect(() => {
    if (!bookId) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const poll = async () => {
        try {
            const data = await apiClient.get<BookResult>(API_ENDPOINTS.TRANSLATE_BOOK(bookId));
            if (cancelled) return;

            if (data.status === 'COMPLETED') {
                setResult(data);
                setPhase(data.pages.some((page) => page.status === 'NO_TEXT') ? 'no_text' : 'completed');
                return;
            }

            if (data.status === 'FAILED') {
                setPhase('failed');
                return;
            }

            timeoutId = setTimeout(poll, POLL_INTERVAL);
        } catch {
            if (!cancelled) setPhase('failed');
        }
    };

    poll();

    return () => {
        cancelled = true;
        if (timeoutId) clearTimeout(timeoutId);
    };
}, [bookId]);
```

### Medium - action 응답 타입과 fetcher 상태 전환 설계가 더 필요함

Design은 action이 `{ ok: true, bookId }` 또는 `{ ok: false, error }`를 반환한다고 가정하지만, `TranslateView`에서 `fetcher.state`, `fetcher.data`, `bookId`, `phase`를 어떻게 동기화할지 구체 예시가 부족하다.

권장 보강:
- `fetcher.state !== 'idle'`이면 `uploading`
- `fetcher.data?.ok === true`이면 `bookId` 저장 후 `translating`
- `fetcher.data?.ok === false`이면 `failed`와 error message 표시
- 새 파일 선택 시 이전 `result`, `error`, `bookId` 초기화

### Low - `PARTIALLY_COMPLETED`는 현재 BE 상태가 아님

Design의 terminal status에 `PARTIALLY_COMPLETED`가 포함되어 있지만, 현재 BE schema와 pipeline에는 해당 Book 상태가 없다.

권장 수정:
- Phase 1에서는 제거
- 미래 확장 목적이면 "현재 BE 미지원, Phase 2 후보"라고 별도 표기

### Low - 타입 정의에 literal union을 쓰면 구현 안정성이 높아짐

현재 타입 예시는 status를 `string`으로 둔다. BE 상태 목록이 고정되어 있으므로 union type으로 좁히면 UI 분기 누락을 줄일 수 있다.

권장 타입:

```ts
export type BookStatus = 'PENDING' | 'OCR_PROCESSING' | 'TRANSLATING' | 'COMPLETED' | 'FAILED';
export type BookPageStatus = 'PENDING' | 'COMPLETED' | 'NO_TEXT' | 'FAILED';

export type BookPageResult = {
    page_no: number;
    ocr_text: string | null;
    literal_text: string | null;
    interpretive_text: string | null;
    ocr_engine: string | null;
    translator_engine: string | null;
    status: BookPageStatus;
};

export type BookResult = {
    book_id: string;
    title: string;
    status: BookStatus;
    total_pages: number;
    pages: BookPageResult[];
};
```

### Low - 현재 placeholder UI의 기능 문구 정리가 필요함

현재 `TranslateView`에는 직접 텍스트 입력, PDF 지원, 다운로드 문구가 남아 있다. 이번 Design의 제외 범위와 맞추려면 구현 시 제거하거나 Phase 2 비활성 상태로 명확히 정리해야 한다.

## 권장 Design 보정안

1. Book terminal status는 `COMPLETED`, `FAILED`만 사용한다.
2. `NO_TEXT`는 `BookPageResult.status`에서 판단한다.
3. `process.env` 대신 `import.meta.env`를 사용한다.
4. 폴링은 요청 완료 후 다음 요청을 예약하는 방식으로 중첩을 방지한다.
5. 파일 선택 시 `accept` 외에 `file.type`과 `file.size`를 검사한다.
6. placeholder의 텍스트 입력/PDF/다운로드 문구를 이번 범위에 맞게 제거한다.

## 결론

Design의 큰 구조는 현재 client/server 코드와 잘 맞는다. 다만 `NO_TEXT` 처리와 폴링 구현 방식은 실제 동작에 직접 영향을 주므로 구현 전에 문서 보정이 필요하다.
