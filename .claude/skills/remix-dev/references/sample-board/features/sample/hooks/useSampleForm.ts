/**
 * [Golden File] CUD 폼 훅 예시 — React Hook Form + Zod + useFetcher
 * 실제 위치: features/{domain}/hooks/use{Entity}Form.ts
 *
 * 패턴 포인트:
 * - 데이터는 loader에서 defaultValues로 주입 (훅에서 직접 fetch 금지)
 * - Zod 스키마로 유효성 검증
 * - 제출은 useFetcher.submit으로 action 호출
 * - 성공/실패 처리는 useEffect에서 fetcher.data 확인
 */

import { useEffect } from 'react';

import { useNavigate, useFetcher } from 'react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { z } from 'zod';

// Zod 스키마 정의
const sampleFormSchema = z.object({
    title:    z.string().min(1, '제목을 입력해주세요'),
    content:  z.string().min(1, '내용을 입력해주세요'),
    category: z.string().min(1, '카테고리를 선택해주세요'),
});

type SampleFormData = z.infer<typeof sampleFormSchema>;

interface Options {
    defaultValues?: Partial<SampleFormData>;
    isEdit?: boolean;
}

export function useSampleForm({ defaultValues, isEdit = false }: Options = {}) {
    const navigate = useNavigate();
    const fetcher = useFetcher();

    const form = useForm<SampleFormData>({
        resolver: zodResolver(sampleFormSchema),
        defaultValues: { title: '', content: '', category: '', ...defaultValues },
    });

    // 제출 — useFetcher로 action 호출
    const handleSubmit = form.handleSubmit((data) => {
        fetcher.submit(
            { intent: isEdit ? 'update' : 'create', ...data },
            { method: 'post' },
        );
    });

    // 완료 처리
    useEffect(() => {
        if (fetcher.state === 'idle' && fetcher.data?.success) {
            toast.success(isEdit ? '수정되었습니다.' : '등록되었습니다.');
            navigate(-1);
        }
        if (fetcher.state === 'idle' && fetcher.data?.error) {
            toast.error(fetcher.data.error);
        }
    }, [fetcher.state, fetcher.data, isEdit, navigate]);

    return {
        form,
        handleSubmit,
        isSubmitting: fetcher.state !== 'idle',
    };
}
