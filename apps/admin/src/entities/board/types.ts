export type BoardType = "LIST" | "IMAGE" | "QNA";

export interface AdminBoard {
  id: string;
  board_code: string;
  board_name: string;
  board_desc: string | null;
  board_group: string | null;
  board_type: BoardType;
  read_yn: boolean;
  guest_read_yn: boolean;
  write_yn: boolean;
  guest_write_yn: boolean;
  notice_yn: boolean;
  reply_yn: boolean;
  comment_yn: boolean;
  secret_yn: boolean;
  like_yn: boolean;
  category_yn: boolean;
  attach_yn: boolean;
  attach_ext: string | null;
  attach_size: number;
  attach_count: number;
  list_count: number;
  auto_reply_enabled: boolean;
  auto_reply_delay_min: number;
  pipeline_enabled: boolean;
  sort_order: number;
  use_yn: boolean;
  del_yn: boolean;
}

export interface AdminBoardListRequest {
  keyword?: string | null;
  use_yn?: boolean | null;
  page: number;
  size: number;
}

export interface AdminBoardSaveRequest {
  board_code?: string;
  board_name: string;
  board_desc: string | null;
  board_group: string | null;
  board_type: BoardType;
  read_yn?: boolean;
  guest_read_yn: boolean;
  write_yn: boolean;
  guest_write_yn?: boolean;
  notice_yn?: boolean;
  reply_yn?: boolean;
  comment_yn: boolean;
  category_yn: boolean;
  attach_yn: boolean;
  attach_ext?: string | null;
  attach_size?: number;
  attach_count?: number;
  list_count?: number;
  auto_reply_enabled: boolean;
  auto_reply_delay_min?: number;
  sort_order: number;
  use_yn?: boolean;
}

export interface AdminBoardCategory {
  id: string;
  board_id: string;
  category_name: string;
  sort_order: number;
  use_yn: boolean;
  del_yn: boolean;
}

export interface AdminBoardCategorySaveRequest {
  category_name: string;
  sort_order: number;
  use_yn: boolean;
}
