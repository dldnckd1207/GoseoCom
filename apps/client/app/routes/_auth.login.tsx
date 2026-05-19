import { LoginView } from '~/views/auth/LoginView';

import type { Route } from './+types/_auth.login';

export function meta(_: Route.MetaArgs) {
    return [{ title: '로그인 | 해독 AI' }];
}

export default function LoginRoute() {
    return <LoginView />;
}
