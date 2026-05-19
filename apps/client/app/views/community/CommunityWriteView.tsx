import { useState } from 'react';

import { Form, Link, useLoaderData, useActionData, useNavigation } from 'react-router';

import { ChevronLeft } from 'lucide-react';

import type { loader, action } from '~/routes/_layout.community.write';

export function CommunityWriteView() {
    const { boards, defaultBoard, categories } = useLoaderData<typeof loader>();
    const actionData = useActionData<typeof action>();
    const navigation = useNavigation();
    const isSubmitting = navigation.state === 'submitting';

    const [selectedBoard, setSelectedBoard] = useState(defaultBoard);
    const currentCategories = categories[selectedBoard] ?? [];

    return (
        <div className="page-wrapper py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link
                    to="/community"
                    className="inline-flex items-center gap-2 mb-6 text-gray-600 hover:text-gray-900 transition-colors"
                >
                    <ChevronLeft className="w-5 h-5" aria-hidden />
                    <span>목록으로</span>
                </Link>

                <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
                    <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                        <h1 className="text-[length:var(--text-section-title)] font-bold text-gray-900">글 작성하기</h1>
                    </div>

                    <Form method="post" className="p-6 space-y-5">
                        {/* 글 유형 */}
                        <div>
                            <p className="block mb-2 text-sm font-medium text-gray-700">
                                글 유형 <span className="text-red-500">*</span>
                            </p>
                            {boards.length === 0 ? (
                                <p className="text-sm text-gray-500">게시판 정보를 불러오지 못했습니다.</p>
                            ) : (
                                <div key={defaultBoard} role="group" aria-label="글 유형" className="flex flex-wrap gap-2">
                                    {boards.map((b) => (
                                        <label key={b.board_code} className="cursor-pointer">
                                            <input
                                                type="radio"
                                                name="board_code"
                                                value={b.board_code}
                                                defaultChecked={b.board_code === defaultBoard}
                                                required
                                                className="sr-only peer"
                                                onChange={() => setSelectedBoard(b.board_code)}
                                            />
                                            <span className="inline-flex items-center px-4 py-2 font-medium text-gray-700 rounded-lg bg-gray-100 transition-colors peer-checked:bg-blue-600 peer-checked:text-white peer-focus-visible:ring-2 peer-focus-visible:ring-blue-600 peer-focus-visible:ring-offset-2">
                                                {b.board_name}
                                            </span>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* 시대 — 카테고리가 있는 경우에만 표시 */}
                        {currentCategories.length > 0 && (
                            <div>
                                <label htmlFor="category_id" className="block mb-1 text-sm font-medium text-gray-700">
                                    시대
                                </label>
                                <select
                                    key={selectedBoard}
                                    id="category_id"
                                    name="category_id"
                                    className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                                >
                                    <option value="">선택 안 함</option>
                                    {currentCategories.map(c => (
                                        <option key={c.id} value={c.id}>{c.category_name}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* 제목 */}
                        <div>
                            <label htmlFor="title" className="block mb-1 text-sm font-medium text-gray-700">
                                제목 <span className="text-red-500">*</span>
                            </label>
                            <input
                                id="title"
                                name="title"
                                type="text"
                                required
                                maxLength={255}
                                placeholder="제목을 입력하세요"
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                            />
                        </div>

                        {/* 내용 */}
                        <div>
                            <label htmlFor="content" className="block mb-1 text-sm font-medium text-gray-700">
                                내용 <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                id="content"
                                name="content"
                                required
                                rows={12}
                                placeholder="내용을 입력하세요"
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 resize-y focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                            />
                        </div>

                        {actionData?.error && (
                            <p className="text-sm text-red-500">{actionData.error}</p>
                        )}

                        <div className="flex justify-end gap-3 pt-2">
                            <Link
                                to="/community"
                                className="px-6 py-2 font-medium text-gray-700 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                            >
                                취소
                            </Link>
                            <button
                                type="submit"
                                disabled={isSubmitting || boards.length === 0}
                                className="px-6 py-2 font-medium text-white rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isSubmitting ? '등록 중...' : '등록하기'}
                            </button>
                        </div>
                    </Form>
                </div>
            </div>
        </div>
    );
}
