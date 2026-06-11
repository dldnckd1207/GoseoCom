import { useMutation, useQueryClient } from "@tanstack/react-query";

import { userApi } from "~/features/users/api/userApi";

import type {
  AdminUserForceWithdrawRequest,
  AdminUserUpdateRequest,
} from "~/entities/user/types";

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, request }: { userId: string; request: AdminUserUpdateRequest }) =>
      userApi.update(userId, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}

export function useForceWithdrawUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      request,
    }: {
      userId: string;
      request: AdminUserForceWithdrawRequest;
    }) => userApi.forceWithdraw(userId, request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
  });
}
