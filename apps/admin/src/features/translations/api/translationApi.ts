import { apiClient } from "~/shared/api/client";

import type {
  AdminTranslationDetail,
  AdminTranslationListItem,
  AdminTranslationListRequest,
  AdminTranslationRetryResponse,
} from "~/entities/translation/types";
import type { PageData } from "~/shared/api/page";

const ADMIN_TRANSLATIONS_PATH = "/admin/api/v1/translations";

export const translationApi = {
  list: (request: AdminTranslationListRequest) =>
    apiClient.post<PageData<AdminTranslationListItem>>(
      `${ADMIN_TRANSLATIONS_PATH}/list`,
      request,
    ),
  get: (bookId: string) =>
    apiClient.get<AdminTranslationDetail>(`${ADMIN_TRANSLATIONS_PATH}/${bookId}`),
  retry: (bookId: string) =>
    apiClient.put<AdminTranslationRetryResponse>(
      `${ADMIN_TRANSLATIONS_PATH}/${bookId}/retry`,
      {},
    ),
};
