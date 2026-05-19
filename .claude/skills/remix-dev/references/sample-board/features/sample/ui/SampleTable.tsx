/**
 * [Golden File] 테이블 UI 예시
 * 실제 위치: features/{domain}/ui/{Entity}Table.tsx
 *
 * 패턴 포인트:
 * - 데이터 + 핸들러를 Props로 수신
 * - shared/ui 또는 layout.css 시맨틱 클래스 활용
 * - 키보드 접근성 (tabIndex + onKeyDown)
 */

import { useNavigate } from 'react-router';
import { format } from 'date-fns';

import { Button } from '~/shared/ui/button';

import type { SampleResponse } from '../types';

interface Props {
    list: SampleResponse[];
    onDelete: (id: string) => void;
}

export function SampleTable({ list, onDelete }: Props) {
    const navigate = useNavigate();

    const handleRowClick = (id: string) => {
        navigate(`/board/sample/${id}`);
    };

    return (
        <div className="table-wrapper">
            <table className="table">
                <thead className="table-header">
                    <tr>
                        <th className="th">번호</th>
                        <th className="th">카테고리</th>
                        <th className="th">제목</th>
                        <th className="th">작성자</th>
                        <th className="th">작성일</th>
                        <th className="th">조회수</th>
                        <th className="th">관리</th>
                    </tr>
                </thead>
                <tbody>
                    {list.map((item, index) => (
                        <tr
                            key={item.id}
                            className="tr cursor-pointer hover:bg-gray-50"
                            tabIndex={0}
                            onClick={() => handleRowClick(item.id)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') handleRowClick(item.id);
                            }}
                        >
                            <td className="td">{index + 1}</td>
                            <td className="td">
                                <span className="badge">{item.category}</span>
                            </td>
                            <td className="td">{item.title}</td>
                            <td className="td">{item.createdBy}</td>
                            <td className="td">{format(new Date(item.createdAt), 'yyyy-MM-dd')}</td>
                            <td className="td">{item.viewCount}</td>
                            <td className="td">
                                <Button
                                    variant="destructive"
                                    size="sm"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDelete(item.id);
                                    }}
                                >
                                    삭제
                                </Button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
