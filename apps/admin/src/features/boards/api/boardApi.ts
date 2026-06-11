import { apiClient } from "~/shared/api/client";

import type {
  AdminBoard,
  AdminBoardCategory,
  AdminBoardCategorySaveRequest,
  AdminBoardListRequest,
  AdminBoardSaveRequest,
} from "~/entities/board/types";
import type { PageData } from "~/shared/api/page";

const ADMIN_BOARDS_PATH = "/admin/api/v1/boards";

export const boardApi = {
  list: (request: AdminBoardListRequest) =>
    apiClient.post<PageData<AdminBoard>>(`${ADMIN_BOARDS_PATH}/list`, request),
  get: (boardId: string) => apiClient.get<AdminBoard>(`${ADMIN_BOARDS_PATH}/${boardId}`),
  create: (request: AdminBoardSaveRequest) =>
    apiClient.post<AdminBoard>(ADMIN_BOARDS_PATH, request),
  update: (boardId: string, request: AdminBoardSaveRequest) =>
    apiClient.put<AdminBoard>(`${ADMIN_BOARDS_PATH}/${boardId}`, request),
  remove: (boardId: string) => apiClient.delete<null>(`${ADMIN_BOARDS_PATH}/${boardId}`),
  listCategories: (boardId: string) =>
    apiClient.get<AdminBoardCategory[]>(`${ADMIN_BOARDS_PATH}/${boardId}/categories`),
  createCategory: (boardId: string, request: AdminBoardCategorySaveRequest) =>
    apiClient.post<AdminBoardCategory>(`${ADMIN_BOARDS_PATH}/${boardId}/categories`, request),
  updateCategory: (
    boardId: string,
    categoryId: string,
    request: AdminBoardCategorySaveRequest,
  ) =>
    apiClient.put<AdminBoardCategory>(
      `${ADMIN_BOARDS_PATH}/${boardId}/categories/${categoryId}`,
      request,
    ),
  removeCategory: (boardId: string, categoryId: string) =>
    apiClient.delete<null>(`${ADMIN_BOARDS_PATH}/${boardId}/categories/${categoryId}`),
};
