/**
 * [Golden File] 엔드포인트 등록 예시
 * 실제 위치: shared/api/endpoints.ts
 */

export const API_ENDPOINTS = {
    // ... 기존 엔드포인트 ...

    // Sample 게시판
    SAMPLE_LIST:   '/api/board/sample/list',
    SAMPLE_DETAIL: '/api/board/sample/detail',
    SAMPLE_CREATE: '/api/board/sample/create',
    SAMPLE_UPDATE: '/api/board/sample/update',
    SAMPLE_DELETE: '/api/board/sample/delete',
} as const;
