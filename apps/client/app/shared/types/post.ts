import type { KeywordItem } from './translate';

// ── 공통 페이지네이션 응답 ────────────────────────────────────────────────────

export type PageResult<T> = {
    items: T[];
    total: number;
    page: number;
    size: number;
};

// ── BE API 응답 타입 ──────────────────────────────────────────────────────────

export type FileItem = {
    file_id: string;
    original_name: string;
    url_path: string;
    file_size: number;
    file_ext: string;
};

export type BoardCategoryItem = {
    id: string;
    category_name: string;
    sort_order: number;
};

export type BoardSummary = {
    id: string;
    board_code: string;
    board_name: string;
    board_type: string;
    guest_read_yn: boolean;
    write_yn: boolean;
    board_group: string | null;
    sort_order: number;
    use_yn: boolean;
    attach_yn: boolean;
    attach_ext: string | null;
    attach_size: number;
};

export type PostSummary = {
    id: string;
    board_id: string;
    board_code: string;
    author_name: string;
    is_ai_gen: boolean;
    title: string;
    notice_yn: boolean;
    view_count: number;
    comment_count: number;
    created_at: string;
    category_id: string | null;
    category_name: string | null;
};

export type PostBookPage = {
    page_no: number;
    ocr_text: string | null;
    literal_text: string | null;
    interpretive_text: string | null;
};

export type PostBookData = {
    book_id: string;
    title: string;
    source_file_url: string | null;
    summary_text: string | null;
    keywords: KeywordItem[] | null;
    pages: PostBookPage[];
};

export type PostDetail = {
    id: string;
    board_id: string;
    board_code: string;
    user_id: string;
    author_name: string;
    is_ai_gen: boolean;
    parent_id: string | null;
    depth: number;
    title: string;
    content: string;
    notice_yn: boolean;
    view_count: number;
    comment_count: number;
    auto_reply_status: string;
    files: FileItem[];
    created_at: string;
    updated_at: string;
    category_id: string | null;
    category_name: string | null;
    book: PostBookData | null;
};

export type CommentItem = {
    id: string;
    post_id: string;
    user_id: string | null;
    author_name: string | null;
    is_ai_gen: boolean;
    is_deleted: boolean;
    is_filtered: boolean;
    filter_reason: string | null;
    parent_id: string | null;
    depth: number;
    content: string;
    created_at: string;
    updated_at: string;
    replies: CommentItem[];
};
