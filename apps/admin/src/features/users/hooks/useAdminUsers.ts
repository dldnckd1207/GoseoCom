import { useQuery } from "@tanstack/react-query";

import { userApi } from "~/features/users/api/userApi";

import type { AdminUserRoleFilter } from "~/entities/user/types";

interface UseAdminUsersParams {
  keyword: string;
  role: AdminUserRoleFilter;
  useYn: "all" | "active" | "inactive";
  blockYn: "all" | "normal" | "blocked";
  includeDeleted: boolean;
  page: number;
}

export function useAdminUsers({
  keyword,
  role,
  useYn,
  blockYn,
  includeDeleted,
  page,
}: UseAdminUsersParams) {
  return useQuery({
    queryKey: ["admin", "users", { keyword, role, useYn, blockYn, includeDeleted, page }],
    queryFn: () =>
      userApi.list({
        keyword: keyword.trim() || null,
        role,
        use_yn: useYn === "all" ? null : useYn === "active",
        block_yn: blockYn === "all" ? null : blockYn === "blocked",
        include_deleted: includeDeleted,
        page,
        size: 10,
      }),
  });
}
