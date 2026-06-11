import { useState } from "react";

import { Navigate, useLocation, useNavigate } from "react-router";

import { KeyRound, ShieldCheck } from "lucide-react";

import { authApi, OAUTH_BASE_URL } from "~/features/auth/api/authApi";
import { useAdminSession } from "~/features/auth/hooks/useAdminSession";

import { Button } from "~/shared/ui/button";
import { ThemeToggle } from "~/shared/ui/ThemeToggle";

import type { FormEvent } from "react";

export function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = useAdminSession();
  const [devUserId, setDevUserId] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isDevSubmitting, setIsDevSubmitting] = useState(false);

  const redirectTo =
    typeof location.state === "object" &&
    location.state !== null &&
    "from" in location.state &&
    typeof location.state.from === "string"
      ? location.state.from
      : "/dashboard";
  const deniedReason =
    typeof location.state === "object" &&
    location.state !== null &&
    "reason" in location.state &&
    typeof location.state.reason === "string"
      ? location.state.reason
      : "";

  if (session.isAdmin) {
    return <Navigate to={redirectTo} replace />;
  }

  async function handleDevLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!devUserId.trim()) return;

    setIsDevSubmitting(true);
    setErrorMessage("");

    try {
      await authApi.devToken(devUserId.trim());
      const user = await authApi.me();
      if (user.user_level < 70) {
        setErrorMessage("관리자 권한이 없는 계정입니다.");
        return;
      }
      navigate(redirectTo, { replace: true });
    } catch {
      setErrorMessage("로그인에 실패했습니다. 사용자 ID와 서버 상태를 확인해주세요.");
    } finally {
      setIsDevSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <section className="w-full max-w-md rounded-md border border-border bg-card p-8">
        <div className="flex flex-col items-center text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <ShieldCheck className="size-6" />
          </div>
          <h1 className="mt-5 text-2xl font-medium tracking-normal">관리자 로그인</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            관리자 권한이 있는 계정으로 로그인해야 콘솔에 접근할 수 있습니다.
          </p>
        </div>

        <div className="mt-8 space-y-3">
          {deniedReason === "forbidden" ? (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              관리자 권한이 없는 계정입니다.
            </div>
          ) : null}
          <a
            href={`${OAUTH_BASE_URL}/auth/kakao?redirect=admin`}
            className="flex h-11 w-full items-center justify-center rounded-full bg-[#FEE500] px-4 text-sm font-medium text-gray-950 transition-colors hover:bg-[#F0D800]"
          >
            카카오로 로그인
          </a>
          <Button type="button" variant="outline" className="h-11 w-full" disabled>
            Google 로그인 준비 중
          </Button>
        </div>

        <div className="my-6 h-px bg-border" />

        <form className="space-y-3" onSubmit={handleDevLogin}>
          <label className="block text-sm font-medium" htmlFor="dev-user-id">
            개발용 사용자 ID
          </label>
          <div className="flex gap-2">
            <input
              id="dev-user-id"
              value={devUserId}
              onChange={(event) => setDevUserId(event.target.value)}
              className="h-10 min-w-0 flex-1 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
              placeholder="USR_00000001"
            />
            <Button type="submit" disabled={isDevSubmitting}>
              <KeyRound />
              발급
            </Button>
          </div>
          {errorMessage ? <p className="text-sm text-destructive">{errorMessage}</p> : null}
        </form>
      </section>
    </main>
  );
}
