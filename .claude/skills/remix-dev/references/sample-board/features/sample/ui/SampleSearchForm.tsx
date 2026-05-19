/**
 * [Golden File] 검색폼 UI 예시
 * 실제 위치: features/{domain}/ui/{Entity}SearchForm.tsx
 *
 * 패턴 포인트:
 * - Props로 상태/핸들러 수신 (View → UI 단방향)
 * - shared/ui 컴포넌트 활용
 * - form role="search" + aria-label 접근성
 * - 80-140줄 목표
 */

import { useState } from 'react';

import { Button } from '~/shared/ui/button';
import { Input } from '~/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/shared/ui/select';

interface Props {
    searchKeyword: string;
    category: string;
    onSearch: (keyword: string) => void;
    onCategoryChange: (category: string) => void;
}

export function SampleSearchForm({ searchKeyword, category, onSearch, onCategoryChange }: Props) {
    const [keyword, setKeyword] = useState(searchKeyword);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(keyword);
    };

    return (
        <form role="search" aria-label="게시글 검색" onSubmit={handleSubmit} className="filter-panel">
            <div className="filter-row">
                <Select value={category} onValueChange={onCategoryChange}>
                    <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="전체 카테고리" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="">전체</SelectItem>
                        <SelectItem value="notice">공지</SelectItem>
                        <SelectItem value="general">일반</SelectItem>
                    </SelectContent>
                </Select>

                <Input
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="검색어를 입력하세요"
                    className="flex-1"
                />

                <Button type="submit" className="btn-search">검색</Button>
            </div>
        </form>
    );
}
