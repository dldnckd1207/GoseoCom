import { Link } from 'react-router';

import { BookOpen, Library, Users } from 'lucide-react';

const FEATURES = [
    {
        to: '/translate',
        icon: BookOpen,
        title: '고서 번역',
        description: 'AI 기반 자동 번역으로 고서를 쉽고 빠르게 해독할 수 있습니다',
    },
    {
        to: '/library',
        icon: Library,
        title: '라이브러리',
        description: '다양한 고서 자료와 번역 결과를 탐색하고 참고할 수 있습니다',
    },
    {
        to: '/community',
        icon: Users,
        title: '커뮤니티',
        description: '고서 해독에 대한 의견을 나누고 질문할 수 있습니다',
    },
] as const;

export function HomeView() {
    return (
        <>
            <section className="bg-gradient-to-br from-blue-600 to-blue-700 text-white py-20 sm:py-32">
                <div className="container-main text-center">
                    <h1 className="text-2xl sm:text-5xl lg:text-6xl font-bold mb-6">
                        고서를 쉽고 빠르게 해독하세요
                    </h1>
                    <p className="text-sm sm:text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
                        AI 기술을 활용한 고서 번역 플랫폼으로 옛 문헌을 현대 언어로 손쉽게 변환하고,
                        커뮤니티를 통해 지식을 공유하세요
                    </p>
                    <Link
                        to="/translate"
                        className="inline-block bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors shadow-lg"
                    >
                        지금 시작하기
                    </Link>
                </div>
            </section>

            <section className="py-16 sm:py-24">
                <div className="container-main">
                    <h2 className="text-xl sm:text-4xl font-bold text-center mb-12 text-gray-900">
                        주요 기능
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
                        {FEATURES.map(({ to, icon: Icon, title, description }) => (
                            <Link
                                key={to}
                                to={to}
                                className="bg-white rounded-xl p-8 shadow-md hover:shadow-xl transition-all duration-300 border border-gray-200 hover:border-blue-600 group"
                            >
                                <div className="flex flex-col items-center text-center">
                                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-6 group-hover:bg-blue-600 transition-colors">
                                        <Icon
                                            className="w-8 h-8 text-blue-600 group-hover:text-white transition-colors"
                                            aria-hidden
                                        />
                                    </div>
                                    <h3 className="text-xl font-semibold mb-3 text-gray-900">
                                        {title}
                                    </h3>
                                    <p className="text-gray-600 leading-relaxed">{description}</p>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            </section>
        </>
    );
}
