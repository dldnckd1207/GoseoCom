/**
 * [Golden File] API 함수 예시
 * 실제 위치: features/{domain}/api.ts
 *
 * 공통 서비스 함수 사용:
 * - fetchList:   POST, 페이징 목록 조회 → PageData<T>
 * - fetchDetail: POST, 단건 조회 (id 전달) → T
 * - fetchCreate: POST, 신규 생성 → T
 * - fetchUpdate: PUT, 기존 데이터 수정 → T
 * - fetchDelete: DELETE, 삭제 → void
 */

import { API_ENDPOINTS } from '~/shared/api/endpoints';
import { fetchList, fetchDetail, fetchCreate, fetchUpdate, fetchDelete } from '~/shared/api/service.api';

import type {
    SampleResponse,
    SampleDetailResponse,
    SampleSearchRequest,
    SampleCreateRequest,
    SampleUpdateRequest,
    SampleDeleteRequest,
} from './types';
import type { PageData } from '~/shared/types/api';

// 조회
export async function getSampleList(params?: SampleSearchRequest): Promise<PageData<SampleResponse>> {
    return fetchList<SampleResponse, SampleSearchRequest>(API_ENDPOINTS.SAMPLE_LIST, params);
}

export async function getSampleDetail(id: string): Promise<SampleDetailResponse> {
    return fetchDetail<SampleDetailResponse>(API_ENDPOINTS.SAMPLE_DETAIL, id);
}

// CUD
export async function createSample(data: SampleCreateRequest): Promise<SampleResponse> {
    return fetchCreate<SampleResponse, SampleCreateRequest>(API_ENDPOINTS.SAMPLE_CREATE, data);
}

export async function updateSample(data: SampleUpdateRequest): Promise<SampleResponse> {
    return fetchUpdate<SampleResponse, SampleUpdateRequest>(API_ENDPOINTS.SAMPLE_UPDATE, data);
}

export async function deleteSample(data: SampleDeleteRequest): Promise<void> {
    return fetchDelete<SampleDeleteRequest>(API_ENDPOINTS.SAMPLE_DELETE, data);
}
