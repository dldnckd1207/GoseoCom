import { useState } from "react";

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Search } from "lucide-react";

import { useAdminSession } from "~/features/auth/hooks/useAdminSession";
import { userApi } from "~/features/users/api/userApi";
import { useAdminUsers } from "~/features/users/hooks/useAdminUsers";
import { useForceWithdrawUser, useUpdateUser } from "~/features/users/hooks/useUserMutations";
import { UserFormDialog } from "~/features/users/ui/UserFormDialog";
import { UserPermissionNotice } from "~/features/users/ui/UserPermissionNotice";
import { UserTable } from "~/features/users/ui/UserTable";

import { ApiError } from "~/shared/api/client";
import { openModal } from "~/shared/stores/modalStore";
import { Button } from "~/shared/ui/button";

import type {
  AdminUserDetail,
  AdminUserListItem,
  AdminUserRoleFilter,
  AdminUserUpdateRequest,
} from "~/entities/user/types";

type UseYnFilter = "all" | "active" | "inactive";
type BlockYnFilter = "all" | "normal" | "blocked";

function getPageNumbers(currentPage: number, totalPages: number) {
  const groupStart = Math.floor((currentPage - 1) / 10) * 10 + 1;
  const groupEnd = Math.min(totalPages, groupStart + 9);

  return Array.from({ length: groupEnd - groupStart + 1 }, (_, index) => groupStart + index);
}

export function UsersPage() {
  const session = useAdminSession();
  const [keyword, setKeyword] = useState("");
  const [role, setRole] = useState<AdminUserRoleFilter>("all");
  const [useYn, setUseYn] = useState<UseYnFilter>("all");
  const [blockYn, setBlockYn] = useState<BlockYnFilter>("all");
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [page, setPage] = useState(1);
  const [dialogUser, setDialogUser] = useState<AdminUserDetail | null>(null);
  const usersQuery = useAdminUsers({ keyword, role, useYn, blockYn, includeDeleted, page });
  const updateUser = useUpdateUser();
  const forceWithdrawUser = useForceWithdrawUser();

  const data = usersQuery.data;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.size)) : 1;
  const pageNumbers = getPageNumbers(page, totalPages);

  function resetPage() {
    setPage(1);
  }

  async function handleEdit(user: AdminUserListItem) {
    try {
      const detail = await userApi.get(user.id);
      setDialogUser(detail);
    } catch {
      openModal({ type: "error", message: "사용자 상세 정보를 불러오지 못했습니다." });
    }
  }

  function handleSubmit(request: AdminUserUpdateRequest) {
    if (!dialogUser) return;
    if (Object.keys(request).length === 0) {
      openModal({ type: "alert", message: "변경된 내용이 없습니다." });
      return;
    }
    updateUser.mutate(
      { userId: dialogUser.id, request },
      {
        onSuccess: (updated) => {
          setDialogUser(updated);
          openModal({ type: "alert", message: "사용자 정보가 수정되었습니다." });
        },
        onError: (error) => {
          openModal({
            type: "error",
            message:
              error instanceof ApiError
                ? error.message
                : "사용자 정보를 수정하지 못했습니다.",
          });
        },
      },
    );
  }

  function handleForceWithdraw(reason: string) {
    if (!dialogUser) return;
    openModal({
      type: "confirm",
      title: "강제 탈퇴",
      message:
        "사용자는 로그인할 수 없게 되며 기본 사용자 목록에서 제외됩니다.\n물리 삭제가 아니라 논리 삭제로 처리됩니다.\n계속 진행할까요?",
      buttons: [
        { label: "취소", variant: "outline" },
        {
          label: "강제 탈퇴",
          variant: "destructive",
          onClick: () => {
            forceWithdrawUser.mutate(
              { userId: dialogUser.id, request: { left_reason: reason } },
              {
                onSuccess: () => {
                  setDialogUser(null);
                  openModal({ type: "alert", message: "강제 탈퇴 처리되었습니다." });
                },
                onError: (error) => {
                  openModal({
                    type: "error",
                    message:
                      error instanceof ApiError
                        ? error.message
                        : "강제 탈퇴를 처리하지 못했습니다.",
                  });
                },
              },
            );
          },
        },
      ],
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium tracking-normal">사용자 관리</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          사용자 상태와 관리자 권한을 관리합니다.
        </p>
      </div>

      <UserPermissionNotice userLevel={session.data?.user_level} />

      <section className="grid gap-3 rounded-md border border-border bg-card p-4 md:grid-cols-[1fr_repeat(3,160px)]">
        <label className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={keyword}
            onChange={(event) => {
              setKeyword(event.target.value);
              resetPage();
            }}
            className="h-10 w-full rounded-md border border-border bg-secondary pl-9 pr-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
            placeholder="이름 또는 이메일 검색"
          />
        </label>
        <select
          value={role}
          onChange={(event) => {
            setRole(event.target.value as AdminUserRoleFilter);
            resetPage();
          }}
          className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
        >
          <option value="all">전체 권한</option>
          <option value="user">사용자</option>
          <option value="admin">관리자</option>
          <option value="system_admin">슈퍼관리자</option>
        </select>
        <select
          value={useYn}
          onChange={(event) => {
            setUseYn(event.target.value as UseYnFilter);
            resetPage();
          }}
          className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
        >
          <option value="all">전체 사용 여부</option>
          <option value="active">사용</option>
          <option value="inactive">미사용</option>
        </select>
        <select
          value={blockYn}
          onChange={(event) => {
            setBlockYn(event.target.value as BlockYnFilter);
            resetPage();
          }}
          className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
        >
          <option value="all">전체 차단 여부</option>
          <option value="normal">정상</option>
          <option value="blocked">차단</option>
        </select>
        <label className="flex h-10 items-center gap-2 rounded-md border border-border bg-secondary px-3 text-sm font-medium md:col-span-4">
          <input
            type="checkbox"
            checked={includeDeleted}
            className="size-4"
            onChange={(event) => {
              setIncludeDeleted(event.target.checked);
              resetPage();
            }}
          />
          <span>탈퇴 사용자 포함</span>
        </label>
      </section>

      <UserTable
        users={data?.items ?? []}
        isLoading={usersQuery.isLoading}
        isError={usersQuery.isError}
        onRetry={() => void usersQuery.refetch()}
        onEdit={handleEdit}
      />

      <div className="flex flex-col gap-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
        <span>총 {data?.total ?? 0}개</span>
        <div className="flex flex-wrap items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page <= 1}
            onClick={() => setPage(1)}
            aria-label="첫 페이지"
          >
            <ChevronsLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            aria-label="이전 페이지"
          >
            <ChevronLeft />
          </Button>
          {pageNumbers.map((pageNumber) => (
            <Button
              key={pageNumber}
              variant={pageNumber === page ? "default" : "outline"}
              size="sm"
              className="size-8 px-0 tabular-nums"
              onClick={() => setPage(pageNumber)}
              aria-current={pageNumber === page ? "page" : undefined}
            >
              {pageNumber}
            </Button>
          ))}
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            aria-label="다음 페이지"
          >
            <ChevronRight />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-8"
            disabled={page >= totalPages}
            onClick={() => setPage(totalPages)}
            aria-label="마지막 페이지"
          >
            <ChevronsRight />
          </Button>
        </div>
      </div>

      <UserFormDialog
        key={`${dialogUser?.id ?? "none"}-${String(Boolean(dialogUser))}`}
        user={dialogUser}
        sessionLevel={session.data?.user_level}
        open={dialogUser !== null}
        isSaving={updateUser.isPending}
        isWithdrawing={forceWithdrawUser.isPending}
        onClose={() => setDialogUser(null)}
        onSubmit={handleSubmit}
        onForceWithdraw={handleForceWithdraw}
      />
    </div>
  );
}
