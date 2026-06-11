import { Pencil, RefreshCcw } from "lucide-react";

import { Button } from "~/shared/ui/button";

import type { AdminUserListItem } from "~/entities/user/types";

interface UserTableProps {
  users: AdminUserListItem[];
  isLoading: boolean;
  isError: boolean;
  rowNumberStart: number;
  onRetry: () => void;
  onEdit: (user: AdminUserListItem) => void;
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function StatusBadge({ children }: { children: string }) {
  return <span className="rounded-full border border-border px-2 py-1 text-xs">{children}</span>;
}

export function UserTable({
  users,
  isLoading,
  isError,
  rowNumberStart,
  onRetry,
  onEdit,
}: UserTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        사용자 목록을 불러오는 중입니다.
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-between rounded-md border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">사용자 목록을 불러오지 못했습니다.</p>
        <Button variant="outline" onClick={onRetry}>
          <RefreshCcw />
          다시 시도
        </Button>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div className="rounded-md border border-border bg-card p-8 text-sm text-muted-foreground">
        조건에 맞는 사용자가 없습니다.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[860px] text-left text-sm">
        <thead className="border-b border-border bg-muted/60 text-xs uppercase tracking-[0.08em] text-muted-foreground">
          <tr>
            <th className="w-16 px-4 py-3 font-medium">순번</th>
            <th className="px-4 py-3 font-medium">사용자</th>
            <th className="px-4 py-3 font-medium">권한</th>
            <th className="px-4 py-3 font-medium">사용 여부</th>
            <th className="px-4 py-3 font-medium">차단 여부</th>
            <th className="px-4 py-3 font-medium">가입일</th>
            <th className="px-4 py-3 font-medium">마지막 로그인</th>
            <th className="w-24 px-4 py-3 font-medium">관리</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user, index) => (
            <tr key={user.id} className="border-b border-border last:border-b-0">
              <td className="px-4 py-3 text-muted-foreground tabular-nums">
                {rowNumberStart - index}
              </td>
              <td className="px-4 py-3">
                <div className="font-medium">
                  {user.name}
                  {user.is_self ? <span className="ml-2 text-xs text-muted-foreground">본인</span> : null}
                </div>
              </td>
              <td className="px-4 py-3">{user.role_label}</td>
              <td className="px-4 py-3">
                <StatusBadge>{user.use_yn ? "사용" : "미사용"}</StatusBadge>
              </td>
              <td className="px-4 py-3">
                <StatusBadge>{user.block_yn ? "차단" : "정상"}</StatusBadge>
              </td>
              <td className="px-4 py-3 text-muted-foreground">{formatDate(user.joined_at)}</td>
              <td className="px-4 py-3 text-muted-foreground">
                {formatDate(user.last_login_at)}
              </td>
              <td className="px-4 py-3">
                {user.del_yn ? (
                  <StatusBadge>탈퇴</StatusBadge>
                ) : (
                  <Button
                    aria-label="사용자 수정"
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(user)}
                  >
                    <Pencil />
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
