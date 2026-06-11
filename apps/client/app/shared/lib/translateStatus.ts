import type { BookStatus } from '~/shared/types/translate';

export const STATUS_BADGE: Record<BookStatus, { label: string; className: string }> = {
    PENDING:        { label: '대기중',   className: 'bg-amber-100 text-amber-700 border-amber-200' },
    OCR_PROCESSING: { label: '처리중',   className: 'bg-blue-100 text-blue-700 border-blue-200' },
    OCR_COMPLETED:  { label: 'OCR 완료', className: 'bg-amber-100 text-amber-700 border-amber-200' },
    TRANSLATING:    { label: '번역중',   className: 'bg-blue-100 text-blue-700 border-blue-200' },
    COMPLETED:      { label: '완료',     className: 'bg-green-100 text-green-700 border-green-200' },
    FAILED:         { label: '실패',     className: 'bg-red-100 text-red-700 border-red-200' },
};
