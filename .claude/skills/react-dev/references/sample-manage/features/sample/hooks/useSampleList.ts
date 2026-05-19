/**
 * [Golden File] 목록 조회 Hook 예시
 * 실제 위치: features/{domain}/hooks/use{Domain}List.ts
 *
 * 패턴 포인트:
 * - useQuery + queryKeys 사용
 * - apiClient의 extractData()가 header.success 검증 + body.data 추출을 자동 처리
 * - queryFn은 순수하게 API 함수 호출만 (수동 검증 불필요)
 */
import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/shared/lib/queryKeys';

import { getSampleList } from '../api/sampleApi';

import type { SampleSearchParams } from '../types';

export function useSampleList(params: SampleSearchParams) {
    return useQuery({
        queryKey: queryKeys.sample.list(params),
        queryFn: () => getSampleList(params),
    });
}
