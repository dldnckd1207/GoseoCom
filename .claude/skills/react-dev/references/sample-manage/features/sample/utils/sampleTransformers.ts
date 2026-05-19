/**
 * [Golden File] 데이터 변환 함수 예시
 * 실제 위치: features/{domain}/utils/{domain}Transformers.ts
 *
 * 패턴 포인트:
 * - API 응답 → 폼 데이터 (detailToFormData)
 * - 폼 데이터 → API 요청 (formDataToRequest)
 * - boolean ↔ UI 문자열 변환
 */
import type { SampleDetail, SampleFormData, SampleCreateRequest } from '../types';

// API 응답 → 폼 데이터
export function detailToFormData(detail: SampleDetail): SampleFormData {
    return {
        name: detail.name,
        description: detail.description ?? '',
        category: detail.category,
        status: detail.status,
        sortOrder: detail.sortOrder,
        useYn: detail.useYn ? '사용' : '미사용',
    };
}

// 폼 데이터 → API 요청
export function formDataToRequest(formData: SampleFormData): SampleCreateRequest {
    return {
        name: formData.name,
        description: formData.description || undefined,
        category: formData.category,
        status: formData.status,
        sortOrder: formData.sortOrder,
        useYn: formData.useYn === '사용',
    };
}
