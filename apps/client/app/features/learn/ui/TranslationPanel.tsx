import { useState } from 'react';

import type { LearnPage } from '../types/workspace';

interface Props {
    pages: LearnPage[];
}

type ActiveTab = 'literal' | 'interpretive';

export function TranslationPanel({ pages }: Props) {
    const [activeTab, setActiveTab] = useState<ActiveTab>('literal');

    return (
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="flex items-center gap-2 border-b border-gray-200 bg-gray-50 px-4 py-2.5">
                {(['literal', 'interpretive'] as const).map((tab) => (
                    <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveTab(tab)}
                        className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                            activeTab === tab
                                ? 'bg-indigo-600 text-white'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        {tab === 'literal' ? '📝 직역' : '✨ 의역'}
                    </button>
                ))}
            </div>
            <div className="max-h-72 overflow-y-auto p-4">
                {pages.map((page) => (
                    <div key={page.page_no}>
                        {pages.length > 1 && (
                            <p className="mb-1 text-xs font-semibold text-gray-400">
                                p.{page.page_no}
                            </p>
                        )}
                        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed break-words text-gray-800">
                            {(activeTab === 'literal' ? page.literal_text : page.interpretive_text) ||
                                '내용이 없습니다.'}
                        </pre>
                    </div>
                ))}
            </div>
        </div>
    );
}
