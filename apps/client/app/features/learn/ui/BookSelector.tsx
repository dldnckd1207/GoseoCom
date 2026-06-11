import { Link } from 'react-router';

import { BookOpen } from 'lucide-react';

import { PUBLIC_BASE_URL } from '~/shared/api/client';

import type { BookDropdownItem } from '../types/workspace';

interface Props {
    books: BookDropdownItem[];
    error?: string | null;
}

export function BookSelector({ books, error }: Props) {
    return (
        <div>
            <div className="mb-6">
                <h1 className="mb-2 text-[length:var(--text-page-title-mobile)] font-bold text-gray-900 lg:text-[length:var(--text-page-title)]">
                    학습하기 (Beta)
                </h1>
                <p className="text-gray-600">학습할 번역 완료 문서를 선택하세요</p>
            </div>

            {error && (
                <p className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                    {error}
                </p>
            )}

            {books.length === 0 ? (
                <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center shadow-sm">
                    <BookOpen className="mx-auto mb-3 h-10 w-10 text-gray-300" aria-hidden />
                    <p className="mb-1 font-medium text-gray-700">완료된 번역이 없습니다</p>
                    <p className="text-sm text-gray-500">
                        먼저{' '}
                        <Link to="/translate" className="text-indigo-600 hover:underline">
                            번역하기
                        </Link>
                        에서 문서를 번역해 주세요.
                    </p>
                </div>
            ) : (
                <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {books.map((book) => (
                        <li key={book.book_id}>
                            <Link
                                to={`/translate-test?book_id=${book.book_id}`}
                                className="flex h-full flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md"
                            >
                                <div className="flex h-36 items-center justify-center bg-gray-50">
                                    {book.source_file_url ? (
                                        <img
                                            src={`${PUBLIC_BASE_URL}${book.source_file_url}`}
                                            alt=""
                                            className="h-full w-full object-cover"
                                        />
                                    ) : (
                                        <BookOpen className="h-8 w-8 text-gray-300" aria-hidden />
                                    )}
                                </div>
                                <div className="p-4">
                                    <p className="truncate font-medium text-gray-900">{book.title}</p>
                                    <p className="mt-1 text-xs text-gray-500">
                                        {new Date(book.created_at).toLocaleDateString('ko-KR')}
                                    </p>
                                </div>
                            </Link>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
