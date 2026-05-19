import type { ReactNode } from 'react';

interface Props {
    pageTitle?: string;
    pageDescription?: string;
    children: ReactNode;
}

export function PageLayout({ pageTitle, pageDescription, children }: Props) {
    return (
        <div className="page-wrapper py-8">
            <div className="container-main">
                {pageTitle && (
                    <header className="mb-8">
                        <h1 className="text-[length:var(--text-page-title-mobile)] lg:text-[length:var(--text-page-title)] font-bold text-gray-900 mb-2">
                            {pageTitle}
                        </h1>
                        {pageDescription && <p className="text-gray-600">{pageDescription}</p>}
                    </header>
                )}
                {children}
            </div>
        </div>
    );
}
