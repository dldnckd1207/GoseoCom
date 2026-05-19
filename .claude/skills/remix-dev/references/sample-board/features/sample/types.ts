/**
 * [Golden File] 타입 정의 예시
 * 실제 위치: features/{domain}/types.ts
 *
 * 접미사 규칙:
 * - 목록 응답: ~Response
 * - 상세 응답: ~DetailResponse
 * - 검색 요청: ~SearchRequest (PageRequest 확장)
 * - 생성 요청: ~CreateRequest
 * - 수정 요청: ~UpdateRequest
 * - 삭제 요청: ~DeleteRequest
 * - 하위 타입: ~Item
 */

import type { PageRequest } from '~/shared/types/api';

// 목록 응답
type SampleResponse = {
    id: string;
    title: string;
    content: string;
    category: string;
    viewCount: number;
    createdAt: string;
    createdBy: string;
};

// 상세 응답 (목록보다 필드가 많을 때 분리)
type SampleDetailResponse = {
    id: string;
    title: string;
    content: string;
    category: string;
    viewCount: number;
    fileList: SampleFileItem[];
    createdAt: string;
    createdBy: string;
    updatedAt: string;
    updatedBy: string;
};

// 하위 타입
type SampleFileItem = {
    id: string;
    fileName: string;
    fileSize: number;
};

// 검색 요청 (PageRequest 확장)
type SampleSearchRequest = PageRequest & {
    keyword?: string;
    category?: string;
};

// 생성 요청
type SampleCreateRequest = {
    title: string;
    content: string;
    category: string;
};

// 수정 요청
type SampleUpdateRequest = {
    id: string;
    title: string;
    content: string;
    category: string;
};

// 삭제 요청
type SampleDeleteRequest = {
    id: string;
};

export type {
    SampleResponse,
    SampleDetailResponse,
    SampleFileItem,
    SampleSearchRequest,
    SampleCreateRequest,
    SampleUpdateRequest,
    SampleDeleteRequest,
};
