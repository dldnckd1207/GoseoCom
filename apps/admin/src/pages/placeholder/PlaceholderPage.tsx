import { Construction } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
  description: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-normal">{title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="rounded-md border border-border bg-card p-8">
        <Construction className="size-8 text-muted-foreground" />
        <h2 className="mt-4 text-base font-medium">API 연동 준비 중</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          메뉴와 라우트는 고정 구조로 먼저 배치했습니다. 백엔드 관리자 API가 준비되면 이 화면에
          목록, 필터, 상세 처리 흐름을 연결합니다.
        </p>
      </div>
    </div>
  );
}
