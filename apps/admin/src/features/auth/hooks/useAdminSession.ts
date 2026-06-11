import { useQuery } from "@tanstack/react-query";

import { authApi } from "~/features/auth/api/authApi";

const ADMIN_LEVEL = 70;

export function useAdminSession() {
  const query = useQuery({
    queryKey: ["admin", "session"],
    queryFn: authApi.me,
    retry: false,
  });

  return {
    ...query,
    isAdmin: (query.data?.user_level ?? 0) >= ADMIN_LEVEL,
  };
}
