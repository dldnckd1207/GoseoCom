/**
 * [Golden File] CUD Mutation Hook 예시
 * 실제 위치: features/{domain}/hooks/use{Domain}Mutation.ts
 *
 * 패턴 포인트:
 * - useMutation + invalidateQueries
 * - onSuccess: 캐시 무효화 + toast.success
 * - onError: toast.error
 * - 수정 시 detail 캐시도 무효화
 */
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { queryKeys } from '@/shared/lib/queryKeys';

import { createSample, updateSample, deleteSample } from '../api/sampleApi';

import type { SampleCreateRequest, SampleUpdateRequest } from '../types';

export function useCreateSample() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: SampleCreateRequest) => createSample(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.sample.all });
            toast.success('등록되었습니다.');
        },
        onError: () => {
            toast.error('등록 중 오류가 발생했습니다.');
        },
    });
}

export function useUpdateSample() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (data: SampleUpdateRequest) => updateSample(data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.sample.all });
            queryClient.invalidateQueries({ queryKey: queryKeys.sample.detail(variables.id) });
            toast.success('수정되었습니다.');
        },
        onError: () => {
            toast.error('수정 중 오류가 발생했습니다.');
        },
    });
}

export function useDeleteSample() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => deleteSample(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.sample.all });
            toast.success('삭제되었습니다.');
        },
        onError: () => {
            toast.error('삭제 중 오류가 발생했습니다.');
        },
    });
}
