import type { Route } from './+types/auth.logout';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function action({ request }: Route.ActionArgs) {
    const cookie = request.headers.get('cookie') ?? '';

    let setCookieHeaders: string[] = [];
    try {
        const res = await fetch(`${BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: { cookie },
        });
        // FastAPI가 반환한 Set-Cookie(쿠키 삭제) 헤더를 브라우저로 전달
        setCookieHeaders = res.headers.getSetCookie?.() ?? [];
    } catch {
        // 서버 미기동 등 실패해도 /login으로 이동
    }

    const headers = new Headers({ Location: '/?logout=true' });
    setCookieHeaders.forEach((v) => headers.append('Set-Cookie', v));
    return new Response(null, { status: 302, headers });
}
