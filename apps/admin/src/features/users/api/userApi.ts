import { apiClient } from "~/shared/api/client";

import type {
  AdminUserDetail,
  AdminUserForceWithdrawRequest,
  AdminUserListItem,
  AdminUserListRequest,
  AdminUserUpdateRequest,
} from "~/entities/user/types";
import type { PageData } from "~/shared/api/page";

const ADMIN_USERS_PATH = "/admin/api/v1/users";

export const userApi = {
  list: (request: AdminUserListRequest) =>
    apiClient.post<PageData<AdminUserListItem>>(`${ADMIN_USERS_PATH}/list`, request),
  get: (userId: string) => apiClient.get<AdminUserDetail>(`${ADMIN_USERS_PATH}/${userId}`),
  update: (userId: string, request: AdminUserUpdateRequest) =>
    apiClient.put<AdminUserDetail>(`${ADMIN_USERS_PATH}/${userId}`, request),
  forceWithdraw: (userId: string, request: AdminUserForceWithdrawRequest) =>
    apiClient.delete<null>(`${ADMIN_USERS_PATH}/${userId}`, request),
};
