import { HomeView } from '~/views/home/HomeView';

import type { Route } from './+types/_layout._index';

export function meta(_: Route.MetaArgs) {
    return [
        { title: '해독 AI - 고서 번역 플랫폼' },
        {
            name: 'description',
            content: 'AI 기술을 활용한 고서 번역 플랫폼. 옛 문헌을 현대 언어로 쉽고 빠르게 해독하세요.',
        },
    ];
}

export default function HomeRoute() {
    return <HomeView />;
}
