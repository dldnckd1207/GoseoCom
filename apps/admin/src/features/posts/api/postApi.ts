import { apiClient } from "~/shared/api/client";

import type {
  AdminPostDetail,
  AdminPostListItem,
  AdminPostListRequest,
} from "~/entities/post/types";
import type { PageData } from "~/shared/api/page";

const ADMIN_POSTS_PATH = "/admin/api/v1/posts";

export const postApi = {
  list: (request: AdminPostListRequest) =>
    apiClient.post<PageData<AdminPostListItem>>(`${ADMIN_POSTS_PATH}/list`, request),
  get: (postId: string) => apiClient.get<AdminPostDetail>(`${ADMIN_POSTS_PATH}/${postId}`),
  remove: (postId: string) => apiClient.delete<null>(`${ADMIN_POSTS_PATH}/${postId}`),
  restore: (postId: string) =>
    apiClient.put<AdminPostDetail>(`${ADMIN_POSTS_PATH}/${postId}/restore`, {}),
};
