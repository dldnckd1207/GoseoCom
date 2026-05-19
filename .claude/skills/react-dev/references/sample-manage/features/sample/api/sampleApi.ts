/**
 * [Golden File] API 함수 예시
 * 실제 위치: features/{domain}/api/{domain}Api.ts
 *
 * 패턴 포인트:
 * - apiClient (shared/api/) 사용 (fetch 직접 사용 금지)
 * - extractData()가 body.data 추출 + header.success 검증을 자동 처리
 * - 실패 시 ApiError throw → TanStack Query onError에서 처리
 */
import { apiClient } from '@/shared/api/client';

import type {
    Sample,
    SampleDetail,
    SampleSearchParams,
    SampleCreateRequest,
    SampleUpdateRequest,
} from '../types';
import type { PageData } from '@/shared/types';

const BASE = '/api/sample';

// 목록 조회
export async function getSampleList(params: SampleSearchParams): Promise<PageData<Sample>> {
    return apiClient.post<PageData<Sample>>(`${BASE}/list`, params);
}

// 상세 조회
export async function getSampleDetail(id: string): Promise<SampleDetail> {
    return apiClient.post<SampleDetail>(`${BASE}/detail`, { id });
}

// 생성
export async function createSample(request: SampleCreateRequest): Promise<SampleDetail> {
    return apiClient.post<SampleDetail>(`${BASE}/create`, request);
}

// 수정
export async function updateSample(request: SampleUpdateRequest): Promise<SampleDetail> {
    return apiClient.put<SampleDetail>(`${BASE}/update`, request);
}

// 삭제
export async function deleteSample(id: string): Promise<void> {
    return apiClient.delete<void>(`${BASE}/delete`, { id });
}
