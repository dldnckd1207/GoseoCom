/**
 * [Golden File] 목록 Page 예시
 * 실제 위치: pages/{domain}/{Domain}ListPage.tsx
 *
 * 패턴 포인트:
 * - 이벤트 핸들러 + UI 조합만 (200줄 이하 목표)
 * - 비즈니스 로직 금지 (Hook에 위임)
 * - usePagination + useDebounce 조합
 * - content-wrapper, list-header, list-count CSS 클래스
 * - 접근성: aria-label, aria-labelledby, 키보드 네비게이션
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { usePagination } from '@/shared/hooks/usePagination';
import { useDebounce } from '@/shared/hooks/useDebounce';
import { PageTitle } from '@/shared/components/PageTitle';
import { Pagination } from '@/shared/components/Pagination';
import { Button } from '@/shared/ui/button';
import { Card, CardContent } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { Skeleton } from '@/shared/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table';

import { useSampleList } from '@/features/sample/hooks/useSampleList';

import type { SampleSearchParams } from '@/features/sample/types';

export function SampleListPage() {
    // 1. Hooks
    const navigate = useNavigate();
    const { page, size, setPage } = usePagination({ initialSize: 10 });

    // 2. State
    const [searchParams, setSearchParams] = useState<SampleSearchParams>({});
    const [keyword, setKeyword] = useState('');
    const debouncedParams = useDebounce(searchParams);

    // 3. Query
    const { data, isLoading, isError, refetch } = useSampleList({
        ...debouncedParams,
        page,
        size,
    });

    // 6. Handlers
    function handleSearch() {
        setSearchParams((prev) => ({ ...prev, keyword }));
        setPage(1);
    }

    function handleKeyDown(e: React.KeyboardEvent) {
        if (e.key === 'Enter') handleSearch();
    }

    function handleRowClick(id: string) {
        navigate(`/sample/${id}`);
    }

    // 7. Early returns
    if (isError) {
        return (
            <div className="content-wrapper">
                <PageTitle title="Sample 관리" />
                <div className="error-state">
                    <p>데이터를 불러오는데 실패했습니다.</p>
                    <Button variant="outline" onClick={() => refetch()}>다시 시도</Button>
                </div>
            </div>
        );
    }

    // 8. JSX
    return (
        <div className="content-wrapper">
            <PageTitle title="Sample 관리" />

            {/* 검색 필터 */}
            <Card>
                <CardContent className="pt-6">
                    <div className="filter-row">
                        <Select defaultValue="name" aria-label="검색 조건">
                            <SelectTrigger className="w-[150px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="name">이름</SelectItem>
                                <SelectItem value="category">카테고리</SelectItem>
                            </SelectContent>
                        </Select>
                        <Input
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="검색어를 입력하세요"
                            className="max-w-xs"
                        />
                        <Button onClick={handleSearch}>검색</Button>
                    </div>
                </CardContent>
            </Card>

            {/* 목록 헤더 */}
            <div className="list-header">
                <p className="list-count">
                    총 <span className="text-primary font-medium">{data?.total ?? 0}</span>건
                </p>
                <Button onClick={() => navigate('/sample/create')}>등록</Button>
            </div>

            {/* 테이블 */}
            <Card>
                <Table>
                    <TableHeader>
                        <TableRow className="table-header-row">
                            <TableHead className="th-no">No</TableHead>
                            <TableHead>이름</TableHead>
                            <TableHead className="th-center">카테고리</TableHead>
                            <TableHead className="th-center">상태</TableHead>
                            <TableHead className="th-center">사용여부</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            Array.from({ length: 5 }).map((_, i) => (
                                <TableRow key={i}>
                                    <TableCell colSpan={5}><Skeleton className="h-8 w-full" /></TableCell>
                                </TableRow>
                            ))
                        ) : !data?.items.length ? (
                            <TableRow>
                                <TableCell colSpan={5} className="empty-state">
                                    데이터가 없습니다.
                                </TableCell>
                            </TableRow>
                        ) : (
                            data.items.map((item) => (
                                <TableRow
                                    key={item.id}
                                    className="table-row-clickable"
                                    tabIndex={0}
                                    onClick={() => handleRowClick(item.id)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                            e.preventDefault();
                                            handleRowClick(item.id);
                                        }
                                    }}
                                >
                                    <TableCell className="td-center">{item.listNo}</TableCell>
                                    <TableCell>{item.name}</TableCell>
                                    <TableCell className="td-center">{item.category}</TableCell>
                                    <TableCell className="td-center">{item.status}</TableCell>
                                    <TableCell className="td-center">{item.status}</TableCell>
                                </TableRow>
                            ))
                        )}
                    </TableBody>
                </Table>
            </Card>

            {/* 페이징 */}
            {data && Math.ceil(data.total / data.size) > 1 && (
                <Pagination
                    currentPage={page}
                    totalPages={Math.ceil(data.total / data.size)}
                    onPageChange={setPage}
                />
            )}
        </div>
    );
}
