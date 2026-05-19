/**
 * [Golden File] 타입 정의 예시
 * 실제 위치: features/{domain}/types/index.ts
 */

// --- 목록 응답 ---
export interface Sample {
    listNo: number;
    id: string;
    siteId: string;
    name: string;
    category: string;
    status: string;
    sortOrder: number;
    createdAt: string;
    createdBy: string;
}

// --- 상세 응답 ---
export interface SampleDetail {
    id: string;
    siteId: string;
    name: string;
    description: string;
    category: string;
    status: string;
    sortOrder: number;
    useYn: boolean;
    createdAt: string;
    createdBy: string;
    updatedAt: string;
    updatedBy: string;
}

// --- 검색 조건 ---
export interface SampleSearchParams {
    keyword?: string;
    category?: string;
    status?: string;
    page?: number;
    size?: number;
}

// --- CUD 요청 ---
export interface SampleCreateRequest {
    name: string;
    description?: string;
    category: string;
    status: string;
    sortOrder: number;
    useYn: boolean;
}

export interface SampleUpdateRequest extends SampleCreateRequest {
    id: string;
}

// --- 폼 데이터 (UI 친화적 값) ---
export interface SampleFormData {
    name: string;
    description: string;
    category: string;
    status: string;
    sortOrder: number;
    useYn: string; // '사용' | '미사용' (UI 표시용)
}

export const DEFAULT_SAMPLE_FORM_DATA: SampleFormData = {
    name: '',
    description: '',
    category: '',
    status: '',
    sortOrder: 0,
    useYn: '사용',
};
