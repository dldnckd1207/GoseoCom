export type BookStatus = 'PENDING' | 'OCR_PROCESSING' | 'OCR_COMPLETED' | 'TRANSLATING' | 'COMPLETED' | 'FAILED';
export type BookPageStatus = 'PENDING' | 'COMPLETED' | 'NO_TEXT' | 'FAILED';

export type BookPageResult = {
    page_no: number;
    ocr_text: string | null;
    literal_text: string | null;
    interpretive_text: string | null;
    ocr_engine: string | null;
    translator_engine: string | null;
    status: BookPageStatus;
};

export type KeywordItem = {
    word: string;
    reading: string;
    meaning: string;
    count: number;
};

export type BookResult = {
    book_id: string;
    title: string;
    status: BookStatus;
    total_pages: number;
    source_file_url: string | null;
    summary_text: string | null;
    keywords: KeywordItem[] | null;
    pages: BookPageResult[];
};

export type BookListItem = {
    book_id: string;
    title: string;
    status: BookStatus;
    is_favorite: boolean;
    created_at: string;
};

export type BookPublicListItem = {
    book_id: string;
    title: string;
    created_at: string;
    source_file_url: string | null;
    owner_user_id: string;
    owner_name: string;
    is_bookmarked: boolean;
};

export type FileUploadResult = {
    file_id: string;
    url_path: string;
};

export type BookDropdownItem = {
    book_id: string;
    title: string;
    source_file_url: string | null;
    created_at: string;
};
