import { useState } from 'react';

import { Form, NavLink } from 'react-router';

import { BookOpen, LogIn, LogOut, Menu, User } from 'lucide-react';

import { NAV_LINKS } from '~/shared/config/navigation';
import { cn } from '~/shared/lib/cn';

import { MobileDrawer } from './MobileDrawer';

import type { User as UserType } from '~/shared/types/auth';

interface Props {
    user: UserType | null;
}

export function Header({ user }: Props) {
    const [isOpen, setIsOpen] = useState(false);
    const visibleLinks = NAV_LINKS.filter((link) => (user?.user_level ?? 0) >= link.minLevel);

    return (
        <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
            <div className="container-main">
                <div className="flex justify-between items-center h-16">
                    <NavLink
                        to="/"
                        className="flex items-center gap-2 text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                    >
                        <BookOpen className="w-6 h-6 text-blue-600" aria-hidden />
                        <span>해독 AI</span>
                    </NavLink>

                    {/* 데스크탑 네비게이션 (lg+) */}
                    <nav
                        className="hidden lg:flex items-center gap-1"
                        aria-label="주 네비게이션"
                    >
                        {visibleLinks.map((link) => (
                            <NavLink
                                key={link.path}
                                to={link.path}
                                className={({ isActive }) =>
                                    cn(
                                        'px-4 py-2 rounded-lg font-medium transition-colors',
                                        isActive
                                            ? 'bg-blue-600 text-white'
                                            : 'text-gray-700 hover:bg-gray-100',
                                    )
                                }
                            >
                                {link.label}
                            </NavLink>
                        ))}

                        {user ? (
                            <div className="flex items-center gap-2 ml-2">
                                <span className="flex items-center gap-1 text-gray-700">
                                    <User className="w-4 h-4" aria-hidden />
                                    {user.name}
                                </span>
                                <Form method="post" action="/auth/logout">
                                    <button
                                        type="submit"
                                        className="flex items-center gap-1 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                                        aria-label="로그아웃"
                                    >
                                        <LogOut className="w-4 h-4" aria-hidden />
                                        <span>로그아웃</span>
                                    </button>
                                </Form>
                            </div>
                        ) : (
                            <NavLink
                                to="/login"
                                className="flex items-center gap-1 ml-2 px-3 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                            >
                                <LogIn className="w-4 h-4" aria-hidden />
                                <span>로그인</span>
                            </NavLink>
                        )}
                    </nav>

                    {/* 모바일 햄버거 버튼 (lg 미만) */}
                    <button
                        type="button"
                        className="lg:hidden p-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                        aria-label="메뉴 열기"
                        aria-expanded={isOpen}
                        aria-controls="mobile-menu"
                        onClick={() => setIsOpen(true)}
                    >
                        <Menu className="w-6 h-6" aria-hidden />
                    </button>
                </div>
            </div>

            <MobileDrawer
                isOpen={isOpen}
                onClose={() => setIsOpen(false)}
                user={user}
                visibleLinks={visibleLinks}
            />
        </header>
    );
}
