/** sessionStorage에 저장되는 로그인 후 복귀 경로 키 */
export const REDIRECT_AFTER_LOGIN_KEY = 'redirectAfterLogin';

/** Open Redirect 방지 + /login 루프 방지 검증 */
export const isSafeRedirect = (path: string): boolean =>
    path.startsWith('/') && !path.startsWith('//') && path !== '/login';
