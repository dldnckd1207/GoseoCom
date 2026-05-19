/**
 * [Golden File] 상세 View 예시
 * 실제 위치: views/{domain}/{Entity}DetailView.tsx
 *
 * 패턴 포인트:
 * - useLoaderData로 상세 데이터 수신 (Props로 id 불필요)
 * - 삭제는 useSampleDetail 훅의 useFetcher로 처리
 * - dangerouslySetInnerHTML 사용 시 sanitize 필수
 * - 40-60줄 목표
 */

import { useLoaderData, useNavigate } from 'react-router';
import { format } from 'date-fns';
import DOMPurify from 'dompurify';

import { useSampleDetail } from '~/features/sample/hooks/useSampleDetail';
import { Button } from '~/shared/ui/button';
import { PageLayout } from '~/widgets/layout';

import type { loader } from '~/routes/sample.$id';

export function SampleDetailView() {
    const { detail } = useLoaderData<typeof loader>();
    const navigate = useNavigate();
    const { handleDelete, isDeleting } = useSampleDetail();

    return (
        <PageLayout pageTitle="게시글 상세">
            <div className="card-padded">
                <h2 className="text-xl font-bold">{detail.title}</h2>
                <div className="flex gap-4 text-sm text-gray-500 mt-2">
                    <span>{detail.createdBy}</span>
                    <span>{format(new Date(detail.createdAt), 'yyyy-MM-dd')}</span>
                    <span>조회 {detail.viewCount}</span>
                </div>
                <div
                    className="mt-6"
                    dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(detail.content) }}
                />
            </div>

            <div className="flex gap-2 mt-4">
                <Button onClick={() => navigate(`/board/sample/${detail.id}/edit`)}>수정</Button>
                <Button
                    variant="destructive"
                    disabled={isDeleting}
                    onClick={() => handleDelete(detail.id)}
                >
                    삭제
                </Button>
                <Button variant="outline" onClick={() => navigate(-1)}>목록</Button>
            </div>
        </PageLayout>
    );
}
