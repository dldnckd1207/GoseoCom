/**
 * [Golden File] 목록 View 예시
 * 실제 위치: views/{domain}/{Entity}View.tsx
 *
 * 패턴 포인트:
 * - useLoaderData로 loader 데이터 수신
 * - Hook은 URL 상태(필터/페이징)와 삭제만 담당
 * - Hook + Feature UI + Shared UI 조합만 (50-80줄 목표)
 * - 직접 API 호출 금지
 */

import { useLoaderData, useNavigate } from 'react-router';

import { SampleSearchForm, SampleTable } from '~/features/sample';
import { useSampleList } from '~/features/sample/hooks/useSampleList';
import { Button } from '~/shared/ui/button';
import { PaginationNav } from '~/shared/ui/pagination-nav';
import { PageLayout } from '~/widgets/layout';

import type { loader } from '~/routes/sample._index';

export function SampleView() {
    const { data } = useLoaderData<typeof loader>();
    const navigate = useNavigate();
    const {
        searchKeyword, category, currentPage,
        handleSearch, handleCategoryChange, handlePageChange, handleDelete,
    } = useSampleList();

    return (
        <PageLayout pageTitle="Sample 게시판">
            <SampleSearchForm
                searchKeyword={searchKeyword}
                category={category}
                onSearch={handleSearch}
                onCategoryChange={handleCategoryChange}
            />

            <div className="result-header">
                <span className="total-count">총 {data.total}건</span>
                <Button onClick={() => navigate('/board/sample/create')}>글쓰기</Button>
            </div>

            {data.items.length === 0 ? (
                <div className="state-empty">등록된 게시글이 없습니다.</div>
            ) : (
                <>
                    <SampleTable list={data.items} onDelete={handleDelete} />
                    <PaginationNav
                        currentPage={currentPage}
                        totalPages={Math.ceil(data.total / data.size)}
                        onPageChange={handlePageChange}
                    />
                </>
            )}
        </PageLayout>
    );
}
