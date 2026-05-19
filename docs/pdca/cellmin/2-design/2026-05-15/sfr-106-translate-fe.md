# Design: 고서 번역기 FE — API 연동 (sfr-106-translate-fe)

**작성자**: cellmin  
**날짜**: 2026-05-15  
**기준 Plan**: `docs/pdca/cellmin/1-plan/2026-05-15/sfr-106-translate-fe.md`

---

## 1. 아키텍처 개요

```
TranslateView
  ├── useFetcher → action (SSR)
  │     ├── fetch(multipart) → POST /api/v1/uploads → file_id
  │     └── serverFetch(JSON) → POST /api/v1/translate → book_id
  │
  └── useEffect + setTimeout 재귀 (client)
        └── apiClient.get → GET /api/v1/translate/{book_id}
              ├── COMPLETED → pages.some(NO_TEXT) ? no_text : completed
              ├── FAILED    → phase = 'failed'
              └── 진행 중   → setTimeout(poll, 3000)
```

**핵심 결정:**
- **업로드/번역 시작**: `action` (SSR) — 쿠키 인증 보장, 2단계 API를 서버에서 순차 처리
- **폴링**: `useEffect + setTimeout 재귀` — TanStack Query 미설치, 요청 완료 후 다음 예약으로 중첩 방지
- `serverFetch`는 `Content-Type: application/json` 고정이므로 업로드는 직접 `fetch` + 쿠키 전달 사용

---

## 2. 파일별 설계

### 2-1. `apps/client/app/shared/api/endpoints.ts`

```ts
UPLOADS: '/api/v1/uploads',                            // 신규
TRANSLATE: '/api/v1/translate',                        // 신규
TRANSLATE_LIST: '/api/v1/translate/list',              // 신규 — 이번 UI 범위 제외, 상수만 추가 (#101 라이브러리 연계)
TRANSLATE_DETAIL: (id: string) => `/api/v1/translate/${id}`,  // 신규
```

---

### 2-2. `apps/client/app/shared/types/translate.ts` (신규)

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

export type FileUploadResult = {
    file_id: string;
    url_path: string;
};
```

---

### 2-3. `apps/client/app/routes/_protected.translate.tsx`

**action 추가:**

```ts
export async function action({ request }: Route.ActionArgs) {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;

    if (!file || file.size === 0) {
        return { ok: false, error: '파일을 선택해주세요.' };
    }

    // 1단계: 파일 업로드 (multipart — serverFetch 미사용, 직접 fetch)
    const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
    const cookie = request.headers.get('cookie') ?? '';
    const uploadForm = new FormData();
    uploadForm.append('file', file);

    let fileId: string;
    try {
        const uploadRes = await fetch(`${BASE_URL}${API_ENDPOINTS.UPLOADS}`, {
            method: 'POST',
            headers: { cookie },
            body: uploadForm,
        });
        const uploadJson = await uploadRes.json();
        if (!uploadJson.header.success) {
            return { ok: false, error: uploadJson.header.message ?? '업로드에 실패했습니다.' };
        }
        fileId = uploadJson.body.data.file_id;
    } catch {
        return { ok: false, error: '업로드 중 오류가 발생했습니다.' };
    }

    // 2단계: 번역 시작
    try {
        const result = await serverFetch<{ book_id: string; status: string }>(
            request,
            API_ENDPOINTS.TRANSLATE,
            { method: 'POST', body: JSON.stringify({ file_id: fileId }) },
        );
        return { ok: true, bookId: result.book_id };
    } catch (err) {
        if (err instanceof ApiError) return { ok: false, error: err.message };
        return { ok: false, error: '번역 시작에 실패했습니다.' };
    }
}
```

---

### 2-4. `apps/client/app/views/translate/TranslateView.tsx`

#### 상태 설계

```ts
type Phase =
    | 'idle'           // 초기 상태
    | 'uploading'      // 파일 업로드 + 번역 시작 중 (useFetcher submitting)
    | 'translating'    // 폴링 중
    | 'completed'      // 번역 완료
    | 'failed'         // 번역 실패
    | 'no_text';       // OCR 텍스트 없음
```

#### 폴링 로직

`setInterval` 대신 `setTimeout` 재귀로 요청 완료 후 다음 polling 예약 — 네트워크 지연 시 중첩 요청 방지.  
`NO_TEXT`는 Book 상태가 아닌 Page 상태 → `COMPLETED` 후 `pages` 확인으로 분기.

```ts
const POLL_INTERVAL = 3000;

useEffect(() => {
    if (!bookId) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | null = null;

    const poll = async () => {
        try {
            const data = await apiClient.get<BookResult>(API_ENDPOINTS.TRANSLATE_DETAIL(bookId));
            if (cancelled) return;

            if (data.status === 'COMPLETED') {
                setResult(data);
                const hasNoText = data.pages.some((p) => p.status === 'NO_TEXT');
                setPhase(hasNoText ? 'no_text' : 'completed');
                return;
            }

            if (data.status === 'FAILED') {
                setPhase('failed');
                return;
            }

            // 진행 중 — 다음 폴링 예약
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

#### UI 단계별 렌더링

| Phase | 표시 |
|-------|------|
| `idle` | 파일 업로드 영역 활성화 |
| `uploading` | 스피너 + "업로드 및 번역 준비 중..." (`fetcher.state !== 'idle'`) |
| `translating` | 스피너 + Book status에 따라 "이미지 인식 중..." / "번역 중..." (폴링 중) |
| `completed` | 직역 / 의역 결과 표시 + 다시 번역 버튼 |
| `failed` | "번역에 실패했습니다." + 다시 시도 버튼 |
| `no_text` | "이미지에서 텍스트를 인식하지 못했습니다." + 다시 시도 버튼 |

#### fetcher 상태 동기화

```ts
// fetcher.state로 uploading 감지
useEffect(() => {
    if (fetcher.state !== 'idle') {
        setPhase('uploading');
        return;
    }
    if (fetcher.data?.ok === true) {
        setBookId(fetcher.data.bookId);
        setPhase('translating');
    } else if (fetcher.data?.ok === false) {
        setPhase('failed');
        setError(fetcher.data.error);
    }
}, [fetcher.state, fetcher.data]);
```

#### 파일 선택 시 클라이언트 검증

```ts
const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        setError('이미지 파일만 업로드할 수 있습니다.'); return;
    }
    if (file.size > 10 * 1024 * 1024) {
        setError('파일 크기는 10MB를 초과할 수 없습니다.'); return;
    }

    // 이전 상태 초기화
    setBookId(null); setResult(null); setError(null); setPhase('idle');
    e.target.value = '';

    const fd = new FormData();
    fd.append('file', file);
    fetcher.submit(fd, { method: 'post', encType: 'multipart/form-data' });
};
```

#### 결과 표시

```tsx
{/* 직역 */}
<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
        <h2>직역</h2>
    </div>
    <div className="p-6">
        <p className="whitespace-pre-wrap">{result.pages[0]?.literal_text}</p>
    </div>
</div>

{/* 의역 */}
<div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
        <h2>의역</h2>
    </div>
    <div className="p-6">
        <p className="whitespace-pre-wrap">{result.pages[0]?.interpretive_text}</p>
    </div>
</div>
```

> 파일 선택 즉시 제출 — 별도 "번역 시작" 버튼 불필요. UX 단순화. 검증 포함 패턴은 위 `onChange` 예시 참조.

---

## 3. 데이터 흐름

```
[파일 선택]
    → onChange → fetcher.submit(FormData)
    → action: upload → translate start
    → fetcher.data = { ok: true, bookId }

[bookId 설정]
    → useEffect → poll() 즉시 실행
    → apiClient.get(TRANSLATE_DETAIL(bookId))
    → status === 'COMPLETED'
        → pages.some(p => p.status === 'NO_TEXT') ? phase = 'no_text' : phase = 'completed'
    → status === 'FAILED'    → phase = 'failed'
    → 진행 중                → setTimeout(poll, 3000)

[unmount / 새 파일 선택]
    → cancelled = true + clearTimeout(timeoutId)
```

---

## 4. 엣지 케이스

| 케이스 | 처리 |
|--------|------|
| 이미지 아닌 파일 선택 | `accept="image/*"` + `file.type.startsWith('image/')` 클라이언트 차단 |
| 업로드 API 실패 | `fetcher.data.error` → 에러 메시지 표시 |
| 번역 시작 API 실패 | `fetcher.data.error` → 에러 메시지 표시 |
| 10MB 초과 파일 선택 | `file.size > 10MB` 클라이언트 차단 + 안내 메시지 |
| 폴링 중 네트워크 오류 | `catch` → timeout 중단 → phase = 'failed' |
| 컴포넌트 언마운트 | `useEffect` cleanup → `cancelled = true` + `clearTimeout` |
| 번역 중 새 파일 선택 | `bookId` 초기화 → 기존 timeout 정리 후 재시작 |

---

## 5. 변경 파일 확정

| 파일 | 유형 |
|------|------|
| `apps/client/app/shared/api/endpoints.ts` | 수정 |
| `apps/client/app/shared/types/translate.ts` | 신규 |
| `apps/client/app/routes/_protected.translate.tsx` | 수정 (action 추가) |
| `apps/client/app/views/translate/TranslateView.tsx` | 수정 (전면 재작성) |

---

## 6. 테스트 시나리오

| # | 시나리오 | 기대 |
|---|----------|------|
| T-1 | 고서 이미지 선택 → 업로드 → 번역 완료 | 직역/의역 표시 |
| T-2 | 번역 완료 후 새 이미지 선택 | 이전 결과 초기화, 새 번역 시작 |
| T-3 | 텍스트 없는 이미지 업로드 | "텍스트를 인식하지 못했습니다" 안내 |
| T-4 | 번역 중 페이지 이탈 후 재진입 | 폴링 중단 확인 (메모리 누수 없음) |
| T-5 | 이미지 아닌 파일 선택 시도 | input에서 차단 |
