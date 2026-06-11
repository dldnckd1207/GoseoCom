import { AlertTriangle, BookOpenText, Clock3, MessageSquareWarning, Users } from "lucide-react";

const metrics = [
  { label: "사용자", value: "준비", icon: Users },
  { label: "게시판", value: "연동", icon: BookOpenText },
  { label: "번역 실행", value: "준비", icon: Clock3 },
  { label: "필터링 대기", value: "준비", icon: MessageSquareWarning },
] as const;

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-normal">대시보드</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          관리자 기능의 현재 연동 상태와 주요 관리 진입점을 확인합니다.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-md border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <metric.icon className="size-4 text-muted-foreground" />
            </div>
            <p className="mt-4 text-2xl font-medium">{metric.value}</p>
          </div>
        ))}
      </div>

      <div className="rounded-md border border-border bg-card p-5">
        <div className="flex items-center gap-3">
          <AlertTriangle className="size-5 text-muted-foreground" />
          <h2 className="text-base font-medium">1차 구현 범위</h2>
        </div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          현재 백엔드에 구현된 관리자 API는 게시판 관리입니다. 사용자, 게시글, 번역 이력,
          댓글 필터링, 관리자 로그는 고정 메뉴와 화면 구조를 먼저 제공하고 API 준비 후
          순차 연동합니다.
        </p>
      </div>
    </div>
  );
}
