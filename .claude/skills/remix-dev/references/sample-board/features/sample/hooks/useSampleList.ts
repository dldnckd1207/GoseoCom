/**
 * [Golden File] 목록 훅 예시 — URL searchParams 관리
 * 실제 위치: features/{domain}/hooks/use{Entity}List.ts
 *
 * 패턴 포인트:
 * - 데이터는 loader + useLoaderData()로 처리 (이 훅에서 fetch 금지)
 * - URL searchParams로 필터/페이징 상태 관리 → loader 재실행
 * - 삭제는 useFetcher.submit으로 action 호출
 */

import { useNavigate, useSearchParams, useFetcher } from 'react-router';
import { useEffect } from 'react';
import { toast } from 'sonner';

export function useSampleList() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const fetcher = useFetcher();

    // URL searchParams에서 필터/페이징 상태 추출
    const currentPage = Number(searchParams.get('page') ?? '1');
    const searchKeyword = searchParams.get('keyword') ?? '';
    const category = searchParams.get('category') ?? '';

    // 검색 — URL 변경으로 loader 재실행
    const handleSearch = (keyword: string) => {
        const params = new URLSearchParams(searchParams);
        params.set('keyword', keyword);
        params.set('page', '1');
        navigate(`?${params.toString()}`);
    };

    // 카테고리 변경
    const handleCategoryChange = (value: string) => {
        const params = new URLSearchParams(searchParams);
        params.set('category', value);
        params.set('page', '1');
        navigate(`?${params.toString()}`);
    };

    // 페이지 변경
    const handlePageChange = (page: number) => {
        const params = new URLSearchParams(searchParams);
        params.set('page', String(page));
        navigate(`?${params.toString()}`);
    };

    // 삭제 — useFetcher로 action 호출
    const handleDelete = (id: string) => {
        if (!confirm('삭제하시겠습니까?')) return;
        fetcher.submit(
            { intent: 'delete', id },
            { method: 'post' },
        );
    };

    // 삭제 완료 처리
    useEffect(() => {
        if (fetcher.state === 'idle' && fetcher.data?.success) {
            toast.success('삭제되었습니다.');
        }
        if (fetcher.state === 'idle' && fetcher.data?.error) {
            toast.error(fetcher.data.error);
        }
    }, [fetcher.state, fetcher.data]);

    return {
        searchKeyword,
        category,
        currentPage,
        isDeleting: fetcher.state !== 'idle',
        handleSearch,
        handleCategoryChange,
        handlePageChange,
        handleDelete,
    };
}
