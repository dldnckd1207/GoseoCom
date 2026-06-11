import { useQuery } from "@tanstack/react-query";

import { translationApi } from "~/features/translations/api/translationApi";

export function useTranslationDetail(bookId: string | null) {
  return useQuery({
    queryKey: ["admin", "translations", "detail", bookId],
    queryFn: () => translationApi.get(bookId ?? ""),
    enabled: Boolean(bookId),
  });
}
