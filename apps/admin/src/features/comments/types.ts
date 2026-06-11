export type AdminCommentItem = {
  id: string;
  post_id: string;
  post_title: string;
  board_name: string;
  user_id: string;
  author_name: string;
  content: string;
  filter_reason: string | null;
  filtered_at: string | null;
  filter_reviewed_by: string | null;
  created_at: string;
};

export type AdminCommentListRequest = {
  keyword: string | null;
  page: number;
  size: number;
};
