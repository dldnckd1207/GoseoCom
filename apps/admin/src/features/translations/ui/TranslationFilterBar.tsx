import { Search } from "lucide-react";

import type { AdminTranslationStatus } from "~/entities/translation/types";

interface TranslationFilterBarProps {
  keyword: string;
  status: AdminTranslationStatus;
  onKeywordChange: (value: string) => void;
  onStatusChange: (value: AdminTranslationStatus) => void;
}

const statusOptions: Array<{ value: AdminTranslationStatus; label: string }> = [
  { value: "all", label: "전체 상태" },
  { value: "PENDING", label: "대기" },
  { value: "OCR_PROCESSING", label: "OCR 처리중" },
  { value: "OCR_COMPLETED", label: "OCR 완료" },
  { value: "TRANSLATING", label: "번역중" },
  { value: "COMPLETED", label: "완료" },
  { value: "FAILED", label: "실패" },
];

export function TranslationFilterBar({
  keyword,
  status,
  onKeywordChange,
  onStatusChange,
}: TranslationFilterBarProps) {
  return (
    <section className="grid gap-3 rounded-md border border-border bg-card p-4 md:grid-cols-[1fr_180px]">
      <label className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={keyword}
          onChange={(event) => onKeywordChange(event.target.value)}
          className="h-10 w-full rounded-md border border-border bg-secondary pl-9 pr-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
          placeholder="제목, 소유자 검색"
        />
      </label>
      <select
        value={status}
        onChange={(event) => onStatusChange(event.target.value as AdminTranslationStatus)}
        className="h-10 rounded-md border border-border bg-secondary px-3 text-sm outline-none focus:ring-3 focus:ring-ring/30"
      >
        {statusOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </section>
  );
}
