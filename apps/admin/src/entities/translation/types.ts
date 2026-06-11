import type { PageData } from "~/shared/api/page";

export type AdminTranslationStatus =
  | "all"
  | "PENDING"
  | "OCR_PROCESSING"
  | "OCR_COMPLETED"
  | "TRANSLATING"
  | "COMPLETED"
  | "FAILED";

export interface AdminTranslationListRequest {
  page: number;
  size: number;
  keyword?: string | null;
  status: AdminTranslationStatus;
}

export interface AdminTranslationListItem {
  book_id: string;
  title: string;
  owner_name: string;
  owner_is_self: boolean;
  status: string;
  total_pages: number;
  created_at: string;
  latest_run_status: string | null;
  latest_run_error_msg: string | null;
  can_retry: boolean;
}

export interface AdminTranslationPageItem {
  page_no: number;
  status: string;
  ocr_text: string | null;
  literal_text: string | null;
  interpretive_text: string | null;
  has_ocr_text: boolean;
  has_literal_text: boolean;
  has_interpretive_text: boolean;
  ocr_engine: string | null;
  translator_engine: string | null;
}

export interface AdminPipelineRunItem {
  id: number;
  trigger_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error_msg: string | null;
}

export interface AdminTranslationDetail {
  book_id: string;
  title: string;
  owner_name: string;
  owner_is_self: boolean;
  status: string;
  book_type: string;
  source_type: string;
  total_pages: number;
  source_file_url: string | null;
  created_at: string;
  updated_at: string;
  can_retry: boolean;
  retry_disabled_reason: string | null;
  pages: AdminTranslationPageItem[];
  pipeline_runs: AdminPipelineRunItem[];
}

export interface AdminTranslationRetryResponse {
  book_id: string;
  status: string;
}

export type AdminTranslationPage = PageData<AdminTranslationListItem>;
