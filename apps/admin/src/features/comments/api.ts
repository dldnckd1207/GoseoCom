import { apiClient } from "~/shared/api/client";

import type { AdminCommentItem, AdminCommentListRequest } from "./types";
import type { PageData } from "~/shared/api/page";

const PATH = "/admin/api/v1/comments";

export const commentApi = {
  list: (request: AdminCommentListRequest) =>
    apiClient.post<PageData<AdminCommentItem>>(`${PATH}/list`, request),
  approve: (commentId: string) =>
    apiClient.put<AdminCommentItem>(`${PATH}/${commentId}/approve`, {}),
  reject: (commentId: string) =>
    apiClient.delete<null>(`${PATH}/${commentId}`),
};
