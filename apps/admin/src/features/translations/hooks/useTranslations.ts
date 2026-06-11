import { useQuery } from "@tanstack/react-query";

import { translationApi } from "~/features/translations/api/translationApi";

import type { AdminTranslationStatus } from "~/entities/translation/types";

interface UseTranslationsParams {
  keyword: string;
  status: AdminTranslationStatus;
  page: number;
}

export function useTranslations({ keyword, status, page }: UseTranslationsParams) {
  return useQuery({
    queryKey: ["admin", "translations", { keyword, status, page }],
    queryFn: () =>
      translationApi.list({
        keyword: keyword.trim() || null,
        status,
        page,
        size: 10,
      }),
  });
}
