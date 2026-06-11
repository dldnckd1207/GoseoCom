import { useEffect, useRef, useState } from 'react';

import { Loader2, Send } from 'lucide-react';

import type { LearnChatMessage } from '../types/chat';

interface Props {
    messages: LearnChatMessage[];
    isSending: boolean;
    onSend: (question: string) => void;
}

export function LearnChat({ messages, isSending, onSend }: Props) {
    const [input, setInput] = useState('');
    const feedRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const feed = feedRef.current;
        if (feed) feed.scrollTop = feed.scrollHeight;
    }, [messages, isSending]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isSending) return;
        onSend(input);
        setInput('');
    };

    return (
        <div className="flex flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
                <span className="text-sm font-semibold text-gray-700">문서 Q&A 챗봇</span>
                <span className="ml-2 text-xs text-gray-500">문서 내용을 근거로 답변합니다</span>
            </div>

            <div ref={feedRef} className="flex h-72 flex-col gap-3 overflow-y-auto p-4">
                {messages.length === 0 && (
                    <p className="text-sm text-gray-400">문서에 대해 궁금한 점을 질문해보세요.</p>
                )}
                {messages.map((message) => (
                    <div
                        key={message.message_id}
                        className={
                            message.role === 'USER'
                                ? 'max-w-[85%] self-end rounded-2xl bg-indigo-600 px-4 py-2.5 text-sm leading-relaxed text-white'
                                : 'max-w-[85%] self-start rounded-2xl border border-gray-200 bg-gray-50 px-4 py-2.5'
                        }
                    >
                        {message.role === 'USER' ? (
                            message.content
                        ) : (
                            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed break-words text-gray-800">
                                {message.content}
                            </pre>
                        )}
                    </div>
                ))}
                {isSending && (
                    <div className="flex items-center gap-2 self-start rounded-2xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-500">
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                        답변 생성 중...
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-200 p-3">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    maxLength={1000}
                    placeholder="문서에 대해 질문해보세요..."
                    aria-label="문서 질문 입력"
                    className="flex-1 rounded-xl bg-gray-100 px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-300"
                />
                <button
                    type="submit"
                    disabled={!input.trim() || isSending}
                    className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    <Send className="h-3.5 w-3.5" aria-hidden />
                    전송
                </button>
            </form>
        </div>
    );
}
