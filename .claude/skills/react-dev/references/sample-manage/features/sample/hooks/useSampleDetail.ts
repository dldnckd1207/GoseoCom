/**
 * [Golden File] 상세 조회 Hook 예시
 * 실제 위치: features/{domain}/hooks/use{Domain}Detail.ts
 *
 * 패턴 포인트:
 * - enabled: !!id (id 없으면 비활성화)
 * - apiClient의 extractData()가 header.success 검증 + body.data 추출을 자동 처리
 */
import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/shared/lib/queryKeys';

import { getSampleDetail } from '../api/sampleApi';

export function useSampleDetail(id: string) {
    return useQuery({
        queryKey: queryKeys.sample.detail(id),
        queryFn: () => getSampleDetail(id),
        enabled: !!id,
    });
}
