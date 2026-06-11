import type { PageData } from "~/shared/api/page";

export type AdminPostDeletedStatus = "active" | "deleted" | "all";

export interface PostBookPageData {
  page_no: number;
  ocr_text: string | null;
  literal_text: string | null;
  interpretive_text: string | null;
}

export interface PostBookData {
  book_id: string;
  title: string;
  source_file_url: string | null;
  summary_text: string | null;
  keywords: Record<string, unknown>[] | null;
  pages: PostBookPageData[];
}

export interface PostFileData {
  file_id: string;
  original_name: string;
  url_path: string;
  file_size: number;
  file_ext: string;
}

export interface AdminPostListRequest {
  keyword?: string | null;
  board_id?: string | null;
  author_keyword?: string | null;
  notice_yn?: boolean | null;
  deleted_status: AdminPostDeletedStatus;
  page: number;
  size: number;
}

export interface AdminPostListItem {
  id: string;
  board_id: string;
  board_code: string;
  board_name: string;
  category_id: string | null;
  category_name: string | null;
  user_id: string;
  author_name: string;
  is_ai_gen: boolean;
  title: string;
  notice_yn: boolean;
  view_count: number;
  comment_count: number;
  auto_reply_status: string;
  del_yn: boolean;
  deleted_at: string | null;
  deleted_by: string | null;
  deleted_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminPostDetail extends AdminPostListItem {
  content: string;
  parent_id: string | null;
  depth: number;
  files: PostFileData[];
  book: PostBookData | null;
}

export type AdminPostPage = PageData<AdminPostListItem>;
