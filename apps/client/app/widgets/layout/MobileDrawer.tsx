import { Form, NavLink } from 'react-router';

import { LogOut, User } from 'lucide-react';

import { cn } from '~/shared/lib/cn';
import {
    Sheet,
    SheetContent,
    SheetFooter,
    SheetHeader,
    SheetTitle,
} from '~/shared/ui/sheet';

import type { NavItem } from '~/shared/config/navigation';
import type { User as UserType } from '~/shared/types/auth';

interface Props {
    isOpen: boolean;
    onClose: () => void;
    user: UserType | null;
    visibleLinks: NavItem[];
}

export function MobileDrawer({ isOpen, onClose, user, visibleLinks }: Props) {
    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent side="right" className="w-72" id="mobile-menu">
                <SheetHeader>
                    <SheetTitle>메뉴</SheetTitle>
                </SheetHeader>

                <nav aria-label="모바일 네비게이션" className="flex flex-col gap-1 px-4">
                    {visibleLinks.map((link) => (
                        <NavLink
                            key={link.path}
                            to={link.path}
                            onClick={onClose}
                            className={({ isActive }) =>
                                cn(
                                    'px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                                    isActive
                                        ? 'bg-blue-600 text-white'
                                        : 'text-gray-700 hover:bg-gray-100',
                                )
                            }
                        >
                            {link.label}
                        </NavLink>
                    ))}
                </nav>

                <SheetFooter className="border-t border-gray-200">
                    {user ? (
                        <div className="flex flex-col gap-1 w-full">
                            <span className="flex items-center gap-2 px-4 py-2 text-gray-700">
                                <User className="w-4 h-4" aria-hidden />
                                {user.name}
                            </span>
                            <Form method="post" action="/auth/logout">
                                <button
                                    type="submit"
                                    className="w-full flex items-center gap-2 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                                    aria-label="로그아웃"
                                >
                                    <LogOut className="w-4 h-4" aria-hidden />
                                    로그아웃
                                </button>
                            </Form>
                        </div>
                    ) : (
                        <NavLink
                            to="/login"
                            onClick={onClose}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                        >
                            로그인
                        </NavLink>
                    )}
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
}
