import { useMutation, useQueryClient } from "@tanstack/react-query";

import { authApi } from "~/features/auth/api/authApi";

export function useLogout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      queryClient.clear();
      window.location.href = "/admin/login";
    },
  });
}
