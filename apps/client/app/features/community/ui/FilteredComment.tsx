import { useState } from 'react';

interface Props {
    content: string;
}

export function FilteredComment({ content }: Props) {
    const [showOriginal, setShowOriginal] = useState(false);

    return (
        <div>
            <p className="text-gray-400 text-sm italic">필터링된 댓글입니다.</p>
            <button
                type="button"
                onClick={() => setShowOriginal((v) => !v)}
                className="text-xs text-blue-500 underline mt-1"
            >
                {showOriginal ? '원문 숨기기' : '원문 보기'}
            </button>
            {showOriginal && (
                <p className="text-gray-500 text-sm mt-2 whitespace-pre-wrap break-words bg-yellow-50 px-3 py-2 rounded border border-yellow-200">
                    {content}
                </p>
            )}
        </div>
    );
}
