import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";

import { Modal } from '~/shared/ui/modal';

import type { Route } from "./+types/root";
import "./app.css";

// OG 이미지는 절대 URL이어야 SNS 스크래퍼가 인식 — 배포 환경에선 VITE_SITE_URL 설정 필요
const SITE_URL = import.meta.env.VITE_SITE_URL ?? "";
const OG_IMAGE_URL = `${SITE_URL}/og-image.jpg`;

export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        {/* OG/Twitter 태그 — 라우트 meta()가 root meta를 대체하므로 항상 렌더되도록 정적 배치 */}
        <meta name="description" content="AI 기반 고서 번역 · 해석 · 학습 플랫폼" />
        <meta property="og:type" content="website" />
        <meta property="og:title" content="해독 AI" />
        <meta property="og:description" content="AI 기반 고서 번역 · 해석 · 학습 플랫폼" />
        <meta property="og:image" content={OG_IMAGE_URL} />
        <meta property="og:image:width" content="1871" />
        <meta property="og:image:height" content="1871" />
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content="해독 AI" />
        <meta name="twitter:description" content="AI 기반 고서 번역 · 해석 · 학습 플랫폼" />
        <meta name="twitter:image" content={OG_IMAGE_URL} />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return (
    <>
      <Outlet />
      <Modal />
    </>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let status = 500;
  let message = "오류가 발생했습니다.";
  let details = "예기치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    status = error.status;
    if (error.status === 404) {
      message = "페이지를 찾을 수 없습니다.";
      details = "요청하신 페이지가 존재하지 않거나 삭제되었습니다.";
    } else {
      message = "오류가 발생했습니다.";
      details = error.statusText || details;
    }
  } else if (import.meta.env.DEV && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center px-4">
        <p className="text-6xl font-bold text-blue-600 mb-4">{status}</p>
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">{message}</h1>
        <p className="text-gray-500 mb-8">{details}</p>
        <a
          href="/"
          className="inline-flex items-center px-5 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
        >
          홈으로 돌아가기
        </a>
        {stack && (
          <pre className="mt-8 w-full p-4 overflow-x-auto text-left text-sm bg-gray-100 rounded-lg">
            <code>{stack}</code>
          </pre>
        )}
      </div>
    </main>
  );
}
