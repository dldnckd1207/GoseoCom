/**
 * [Golden File] 상세 훅 예시 — 삭제 전담
 * 실제 위치: features/{domain}/hooks/use{Entity}Detail.ts
 *
 * 패턴 포인트:
 * - 데이터는 loader + useLoaderData()로 처리 (이 훅에서 fetch 금지)
 * - 삭제만 useFetcher로 처리
 */

import { useNavigate, useFetcher } from 'react-router';
import { useEffect } from 'react';
import { toast } from 'sonner';

export function useSampleDetail() {
    const navigate = useNavigate();
    const fetcher = useFetcher();

    const handleDelete = (id: string) => {
        if (!confirm('삭제하시겠습니까?')) return;
        fetcher.submit(
            { intent: 'delete', id },
            { method: 'post' },
        );
    };

    useEffect(() => {
        if (fetcher.state === 'idle' && fetcher.data?.success) {
            toast.success('삭제되었습니다.');
            navigate(-1);
        }
        if (fetcher.state === 'idle' && fetcher.data?.error) {
            toast.error(fetcher.data.error);
        }
    }, [fetcher.state, fetcher.data, navigate]);

    return {
        handleDelete,
        isDeleting: fetcher.state !== 'idle',
    };
}
