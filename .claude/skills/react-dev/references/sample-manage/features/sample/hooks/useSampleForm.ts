/**
 * [Golden File] 폼 Hook 예시 — React Hook Form + Zod
 * 실제 위치: features/{domain}/hooks/use{Domain}Form.ts
 *
 * 패턴 포인트:
 * - RHF + Zod (수동 if문 유효성 검사 금지)
 * - isEditMode = !!id
 * - 상세 데이터 로드 → form.reset()
 * - 다중 Mutation (create/update/delete)
 * - 폼 훅 내부 useNavigate 허용 (방법 2)
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { z } from 'zod';

import { useSampleDetail } from './useSampleDetail';
import { useCreateSample, useUpdateSample, useDeleteSample } from './useSampleMutation';

import { detailToFormData, formDataToRequest } from '../utils/sampleTransformers';

// Zod 스키마 — Single Source of Truth
const sampleFormSchema = z.object({
    name: z.string().min(1, '이름을 입력해주세요'),
    description: z.string().optional(),
    category: z.string().min(1, '카테고리를 선택해주세요'),
    status: z.string().min(1, '상태를 선택해주세요'),
    sortOrder: z.number().min(0, '정렬 순서는 0 이상이어야 합니다'),
    useYn: z.string(),
});

type SampleFormSchema = z.infer<typeof sampleFormSchema>;

export function useSampleForm(id?: string) {
    const isEditMode = !!id;
    const navigate = useNavigate();
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);

    // React Hook Form
    const form = useForm<SampleFormSchema>({
        resolver: zodResolver(sampleFormSchema),
        defaultValues: {
            name: '',
            description: '',
            category: '',
            status: '',
            sortOrder: 0,
            useYn: '사용',
        },
    });

    // API Hooks
    const { data: detailData, isLoading } = useSampleDetail(id || '');
    const createMutation = useCreateSample();
    const updateMutation = useUpdateSample();
    const deleteMutation = useDeleteSample();

    // 상세 데이터 로드 시 폼에 반영
    useEffect(() => {
        if (isEditMode && detailData) {
            form.reset(detailToFormData(detailData));
        }
    }, [isEditMode, detailData, form]);

    // 저장 (Zod가 자동 검증)
    const handleSubmit = form.handleSubmit(async (data) => {
        try {
            if (isEditMode && id) {
                await updateMutation.mutateAsync({ id, ...formDataToRequest(data) });
            } else {
                await createMutation.mutateAsync(formDataToRequest(data));
            }
            navigate('/sample');
        } catch {
            // onError에서 toast 처리
        }
    });

    // 삭제
    async function handleDelete() {
        if (!id) return;
        try {
            await deleteMutation.mutateAsync(id);
            navigate('/sample');
        } catch {
            // onError에서 toast 처리
        }
    }

    return {
        form,
        isEditMode,
        isLoading,
        isSaving: createMutation.isPending || updateMutation.isPending,
        isDeleting: deleteMutation.isPending,
        handleSubmit,
        handleDelete,
        showDeleteDialog,
        setShowDeleteDialog,
    };
}
