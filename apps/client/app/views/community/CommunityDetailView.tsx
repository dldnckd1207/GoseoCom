import { useEffect, useState } from 'react';

import { Link, useLoaderData, useFetcher } from 'react-router';

import { ChevronLeft, MessageSquare, User as UserIcon } from 'lucide-react';

import { formatDate } from '~/shared/lib/date';

import type { loader, action } from '~/routes/_layout.community.$id';

export function CommunityDetailView() {
    const { post, postId, accessDenied, comments, user } = useLoaderData<typeof loader>();
    const fetcher = useFetcher<typeof action>();
    const [comment, setComment] = useState('');

    useEffect(() => {
        // fetcher 완료 후 입력 초기화 — setState in effect 규칙의 정당한 예외
        // eslint-disable-next-line react-hooks/set-state-in-effect
        if (fetcher.state === 'idle' && fetcher.data?.ok) setComment('');
    }, [fetcher.state, fetcher.data]);

    return (
        <div className="page-wrapper py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <Link
                    to="/community"
                    className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6 transition-colors"
                >
                    <ChevronLeft className="w-5 h-5" aria-hidden />
                    <span>목록으로</span>
                </Link>

                {accessDenied ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-16 text-center">
                        <h2 className="text-lg font-semibold text-gray-900 mb-2">
                            접근 권한이 없습니다.
                        </h2>
                        <p className="text-gray-500 mb-8">
                            로그인을 통해 조회해주세요.
                        </p>
                        <div className="flex items-center justify-center gap-3">
                            <Link
                                to="/community"
                                className="px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                            >
                                목록으로
                            </Link>
                            <Link
                                to={`/login?redirect=/community/${postId}`}
                                className="px-5 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
                            >
                                로그인하기
                            </Link>
                        </div>
                    </div>
                ) : !post ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-16 text-center">
                        <h2 className="text-lg font-semibold text-gray-900 mb-2">
                            게시글을 찾을 수 없습니다.
                        </h2>
                        <Link
                            to="/community"
                            className="mt-4 inline-block px-5 py-2 rounded-lg border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                        >
                            목록으로
                        </Link>
                    </div>
                ) : (
                    <>
                        <article className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-6">
                            <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                                <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-4">
                                    {post.title}
                                </h1>
                                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                                    <div className="flex items-center gap-1">
                                        <UserIcon className="w-4 h-4" aria-hidden />
                                        <span>{post.author_name}</span>
                                    </div>
                                    <span aria-hidden>•</span>
                                    <span>{formatDate(post.created_at)}</span>
                                    <span aria-hidden>•</span>
                                    <span>조회 {post.view_count}</span>
                                </div>
                            </div>
                            <div className="px-6 py-8">
                                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                    {post.content}
                                </p>
                            </div>
                        </article>

                        <section
                            aria-label="댓글"
                            className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden"
                        >
                            <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                                <div className="flex items-center gap-2">
                                    <MessageSquare className="w-5 h-5 text-gray-700" aria-hidden />
                                    <h2 className="text-lg font-semibold text-gray-900">
                                        댓글 {post.comment_count}
                                    </h2>
                                </div>
                            </div>

                            <fetcher.Form
                                method="post"
                                className="px-6 py-4 border-b border-gray-200 bg-gray-50"
                            >
                                <label htmlFor="comment-input" className="sr-only">댓글 입력</label>
                                <textarea
                                    id="comment-input"
                                    name="content"
                                    value={user ? comment : ''}
                                    onChange={e => setComment(e.target.value)}
                                    disabled={!user || fetcher.state !== 'idle'}
                                    placeholder={user ? '댓글을 입력하세요...' : '로그인 후 댓글을 작성할 수 있습니다.'}
                                    rows={3}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                                />
                                {fetcher.data?.error && (
                                    <p className="mt-2 text-sm text-red-500">{fetcher.data.error}</p>
                                )}
                                <div className="mt-3 flex justify-end">
                                    <button
                                        type="submit"
                                        disabled={!user || fetcher.state !== 'idle'}
                                        className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {fetcher.state !== 'idle' ? '작성 중...' : '댓글 작성'}
                                    </button>
                                </div>
                            </fetcher.Form>

                            {comments.length === 0 ? (
                                <p className="text-gray-500 text-sm text-center py-6">
                                    작성된 댓글이 없습니다.
                                </p>
                            ) : (
                                <ul className="divide-y divide-gray-200">
                                    {comments.map(c => (
                                        <li key={c.id} className="px-6 py-4">
                                            {c.is_deleted ? (
                                                <p className="text-gray-400 text-sm italic">삭제된 댓글입니다.</p>
                                            ) : (
                                                <>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                                                            <UserIcon className="w-4 h-4 text-gray-500" aria-hidden />
                                                            {c.author_name ?? '익명'}
                                                        </div>
                                                        <span className="text-sm text-gray-500" aria-hidden>•</span>
                                                        <span className="text-sm text-gray-500">{formatDate(c.created_at)}</span>
                                                    </div>
                                                    <p className="text-gray-800 leading-relaxed">{c.content}</p>
                                                    {c.replies.length > 0 && (
                                                        <ul className="mt-3 pl-6 border-l-2 border-gray-100 space-y-3">
                                                            {c.replies.map(r => (
                                                                <li key={r.id}>
                                                                    {r.is_deleted ? (
                                                                        <p className="text-gray-400 text-sm italic">삭제된 댓글입니다.</p>
                                                                    ) : (
                                                                        <>
                                                                            <div className="flex items-center gap-2 mb-1">
                                                                                <div className="flex items-center gap-2 text-sm font-medium text-gray-900">
                                                                                    <UserIcon className="w-3 h-3 text-gray-500" aria-hidden />
                                                                                    {r.author_name ?? '익명'}
                                                                                </div>
                                                                                <span className="text-sm text-gray-500" aria-hidden>•</span>
                                                                                <span className="text-sm text-gray-500">{formatDate(r.created_at)}</span>
                                                                            </div>
                                                                            <p className="text-gray-800 text-sm leading-relaxed">{r.content}</p>
                                                                        </>
                                                                    )}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    )}
                                                </>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    </>
                )}
            </div>
        </div>
    );
}
