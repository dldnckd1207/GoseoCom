export type BookStatus = 'PENDING' | 'OCR_PROCESSING' | 'TRANSLATING' | 'COMPLETED' | 'FAILED';
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

export type BookResult = {
    book_id: string;
    title: string;
    status: BookStatus;
    total_pages: number;
    source_file_url: string | null;
    pages: BookPageResult[];
};

export type BookListItem = {
    book_id: string;
    title: string;
    status: BookStatus;
    created_at: string;
};

export type FileUploadResult = {
    file_id: string;
    url_path: string;
};
