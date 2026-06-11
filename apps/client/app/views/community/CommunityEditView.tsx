import { Form, Link, useLoaderData, useActionData, useNavigation } from 'react-router';

import { ChevronLeft, Paperclip } from 'lucide-react';

import { PUBLIC_BASE_URL } from '~/shared/api/client';

import type { loader, action } from '~/routes/_layout.community.$id_.edit';

export function CommunityEditView() {
    const { post, postId, myBooks, categories } = useLoaderData<typeof loader>();
    const actionData = useActionData<typeof action>();
    const navigation = useNavigation();
    const isSubmitting = navigation.state === 'submitting';

    return (
        <div className="page-wrapper py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link
                    to={`/community/${postId}`}
                    className="inline-flex items-center gap-2 mb-6 text-gray-600 hover:text-gray-900 transition-colors"
                >
                    <ChevronLeft className="w-5 h-5" aria-hidden />
                    <span>게시글로</span>
                </Link>

                <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
                    <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                        <h1 className="text-[length:var(--text-section-title)] font-bold text-gray-900">글 수정하기</h1>
                    </div>

                    <Form method="post" className="p-6 space-y-5">
                        {/* 카테고리 */}
                        {categories.length > 0 && (
                            <div>
                                <label htmlFor="category_id" className="block mb-1 text-sm font-medium text-gray-700">
                                    카테고리
                                </label>
                                <select
                                    id="category_id"
                                    name="category_id"
                                    defaultValue={post.category_id ?? ''}
                                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent bg-white"
                                >
                                    <option value="">카테고리 없음</option>
                                    {categories.map(c => (
                                        <option key={c.id} value={c.id}>{c.category_name}</option>
                                    ))}
                                </select>
                            </div>
                        )}

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
                                defaultValue={post.title}
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label htmlFor="content" className="block mb-1 text-sm font-medium text-gray-700">
                                내용 <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                id="content"
                                name="content"
                                required
                                rows={12}
                                defaultValue={post.content}
                                className="w-full px-4 py-3 rounded-lg border border-gray-300 resize-y focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                            />
                        </div>

                        {/* 첨부파일 (읽기전용 표시) */}
                        {post.files.length > 0 && (
                            <div>
                                <p className="text-sm font-medium text-gray-700 mb-2">첨부파일</p>
                                <div className="space-y-2">
                                    {post.files.map(file => {
                                        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(file.file_ext.toLowerCase());
                                        const src = `${PUBLIC_BASE_URL}${file.url_path}`;
                                        return isImage ? (
                                            <img
                                                key={file.file_id}
                                                src={src}
                                                alt={file.original_name}
                                                className="max-w-xs rounded-lg border border-gray-200"
                                            />
                                        ) : (
                                            <a
                                                key={file.file_id}
                                                href={src}
                                                download={file.original_name}
                                                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50"
                                            >
                                                <Paperclip className="w-4 h-4" aria-hidden />
                                                {file.original_name}
                                            </a>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* 번역 이력 연동 */}
                        {myBooks.length > 0 && (
                            <div>
                                <label htmlFor="book_id" className="block mb-1 text-sm font-medium text-gray-700">
                                    번역 이력 연동 <span className="text-gray-400 font-normal">(선택)</span>
                                </label>
                                <select
                                    id="book_id"
                                    name="book_id"
                                    defaultValue={post.book?.book_id ?? ''}
                                    className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent bg-white"
                                >
                                    <option value="">선택 안 함</option>
                                    {myBooks.map(b => (
                                        <option key={b.book_id} value={b.book_id}>{b.title}</option>
                                    ))}
                                </select>
                                <p className="mt-1 text-xs text-gray-500">연동 시 AI 자동 답변 대신 번역 결과가 게시글에 표시됩니다.</p>
                            </div>
                        )}

                        {actionData?.error && (
                            <p className="text-sm text-red-500">{actionData.error}</p>
                        )}

                        <div className="flex justify-end gap-3 pt-2">
                            <Link
                                to={`/community/${postId}`}
                                className="px-6 py-2 font-medium text-gray-700 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                            >
                                취소
                            </Link>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="px-6 py-2 font-medium text-white rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isSubmitting ? '저장 중...' : '저장하기'}
                            </button>
                        </div>
                    </Form>
                </div>
            </div>
        </div>
    );
}
