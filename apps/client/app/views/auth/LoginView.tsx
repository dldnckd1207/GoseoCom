import { Link, useSearchParams } from 'react-router';

import { BookOpen } from 'lucide-react';

import { isSafeRedirect, REDIRECT_AFTER_LOGIN_KEY } from '~/shared/lib/redirect';
import { openModal } from '~/shared/ui/modal';

// SSR 서버→서버 통신은 VITE_API_BASE_URL, 브라우저 OAuth 리다이렉트는 VITE_PUBLIC_API_URL
const OAUTH_BASE_URL = import.meta.env.VITE_PUBLIC_API_URL ?? import.meta.env.VITE_API_BASE_URL ?? '';

export function LoginView() {
    const [searchParams] = useSearchParams();
    const redirectPath = searchParams.get('redirect') ?? '';

    // OAuth 버튼 클릭 시에만 저장 — 단순 방문으로는 저장 안 함 (redirect 루프 방지)
    const handleOAuthClick = () => {
        if (!redirectPath || !isSafeRedirect(redirectPath)) return;
        try {
            sessionStorage.setItem(REDIRECT_AFTER_LOGIN_KEY, redirectPath);
        } catch {
            // sessionStorage 미지원 환경 — 홈으로 fallback
        }
    };

    const handleGoogleClick = () => {
        openModal({
            type: 'alert',
            message: 'Google 로그인은 서비스 준비 중입니다.\n카카오로 로그인해주세요.',
            buttons: [{ label: '확인' }],
        });
    };

    return (
        <div className="w-full max-w-sm px-4">
            <div className="bg-white rounded-2xl shadow-md p-8 flex flex-col items-center gap-6">
                <div className="flex flex-col items-center gap-2">
                    <Link to="/" className="flex items-center gap-2 text-blue-600">
                        <BookOpen className="w-8 h-8" aria-hidden />
                        <span className="text-2xl font-bold text-gray-900">해독 AI</span>
                    </Link>
                    <p className="text-sm text-gray-500">고서를 쉽고 빠르게 읽다</p>
                </div>

                <div className="w-full flex flex-col gap-3">
                    <a
                        href={`${OAUTH_BASE_URL}/auth/kakao`}
                        onClick={handleOAuthClick}
                        className="flex items-center justify-center gap-3 w-full py-3 px-4 rounded-lg font-medium bg-[#FEE500] text-gray-900 hover:bg-[#F0D800] transition-colors"
                    >
                        카카오로 시작하기
                    </a>
                    <button
                        type="button"
                        onClick={handleGoogleClick}
                        className="flex items-center justify-center gap-3 w-full py-3 px-4 rounded-lg font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 transition-colors"
                    >
                        Google로 시작하기
                    </button>
                </div>
            </div>
        </div>
    );
}
