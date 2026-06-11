import { apiClient, BASE_URL } from "~/shared/api/client";

import type { AdminUser } from "~/entities/user/types";

export const OAUTH_BASE_URL = BASE_URL;

export const authApi = {
  me: () => apiClient.get<AdminUser>("/api/v1/users/me"),
  logout: () => apiClient.post<null>("/auth/logout"),
  devToken: (userId: string) => apiClient.post("/auth/dev/token", { user_id: userId }),
};
