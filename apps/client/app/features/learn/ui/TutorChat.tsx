import { useEffect, useRef, useState } from 'react';

import { Loader2, Send } from 'lucide-react';

import type { LearnChatMessage } from '../types/chat';

interface Props {
    messages: LearnChatMessage[];
    isSending: boolean;
    onSend: (question: string) => void;
}

export function TutorChat({ messages, isSending, onSend }: Props) {
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
        <>
            <div ref={feedRef} className="flex max-h-56 flex-col gap-2.5 overflow-y-auto">
                {messages.length === 0 && (
                    <p className="text-sm text-gray-400">
                        문서 내용으로 카드, 퀴즈, 설명을 만들어 드릴게요.
                    </p>
                )}
                {messages.map((message) => (
                    <div
                        key={message.message_id}
                        className={
                            message.role === 'USER'
                                ? 'max-w-[85%] self-end rounded-xl bg-indigo-50 px-3 py-2 text-sm leading-relaxed text-gray-800'
                                : 'rounded-xl bg-gray-50 px-3 py-2'
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
                    <div className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-2 text-sm text-gray-500">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
                        답변 생성 중...
                    </div>
                )}
            </div>
            <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    maxLength={1000}
                    placeholder="AI 튜터에게 질문하기..."
                    aria-label="튜터 질문 입력"
                    className="min-w-0 flex-1 rounded-xl bg-gray-100 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-300"
                />
                <button
                    type="submit"
                    disabled={!input.trim() || isSending}
                    className="flex items-center rounded-xl bg-indigo-600 px-3 py-2 text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
                    aria-label="전송"
                >
                    <Send className="h-3.5 w-3.5" aria-hidden />
                </button>
            </form>
        </>
    );
}
