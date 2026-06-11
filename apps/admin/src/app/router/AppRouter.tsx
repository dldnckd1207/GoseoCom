import {
  NavLink,
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
  useLocation,
} from "react-router";

import {
  BookOpenText,
  BotMessageSquare,
  ClipboardList,
  LayoutDashboard,
  MessageSquareWarning,
  Newspaper,
  ShieldCheck,
  Users,
} from "lucide-react";

import { useAdminSession } from "~/features/auth/hooks/useAdminSession";
import { useLogout } from "~/features/auth/hooks/useLogout";
import { BoardsPage } from "~/pages/boards/BoardsPage";
import { FilteredCommentsPage } from "~/pages/comments/FilteredCommentsPage";
import { DashboardPage } from "~/pages/dashboard/DashboardPage";
import { LoginPage } from "~/pages/login/LoginPage";
import { PlaceholderPage } from "~/pages/placeholder/PlaceholderPage";
import { PostsPage } from "~/pages/posts/PostsPage";
import { UsersPage } from "~/pages/users/UsersPage";

import { cn } from "~/shared/lib/cn";
import { Button } from "~/shared/ui/button";
import { ThemeToggle } from "~/shared/ui/ThemeToggle";

const navItems = [
  { to: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { to: "/users", label: "사용자 관리", icon: Users },
  { to: "/boards", label: "게시판 관리", icon: BookOpenText },
  { to: "/posts", label: "게시글 관리", icon: Newspaper },
  { to: "/translations", label: "번역 이력", icon: BotMessageSquare },
  { to: "/comments", label: "댓글 필터링", icon: MessageSquareWarning },
  { to: "/logs", label: "관리자 로그", icon: ClipboardList },
] as const;

function getAdminRoleLabel(userLevel: number | undefined) {
  if ((userLevel ?? 0) >= 100) return "슈퍼관리자";
  return "관리자";
}

export function AppRouter() {
  return (
    <Router basename="/admin">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={<ProtectedAdminShell />} />
      </Routes>
    </Router>
  );
}

function ProtectedAdminShell() {
  const location = useLocation();
  const session = useAdminSession();
  const logout = useLogout();

  if (session.isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        관리자 세션을 확인하는 중입니다.
      </main>
    );
  }

  if (!session.isAdmin) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname, reason: session.data ? "forbidden" : "unauthorized" }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-background lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <div className="flex size-9 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <ShieldCheck className="size-5" />
          </div>
          <div>
            <p className="text-sm font-medium leading-none">해독 AI</p>
            <p className="mt-1 text-xs text-muted-foreground">Admin Console</p>
          </div>
        </div>
        <nav className="space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex h-10 items-center gap-3 rounded-md border border-transparent px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  isActive && "border-border bg-accent text-accent-foreground",
                )
              }
            >
              <item.icon className="size-4" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-background/90 px-4 backdrop-blur lg:px-8">
          <div aria-hidden="true" />
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <div className="hidden text-right text-sm md:block">
              <p className="font-medium text-foreground">{session.data?.name}</p>
              <p className="text-xs text-muted-foreground">
                {getAdminRoleLabel(session.data?.user_level)}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              로그아웃
            </Button>
          </div>
        </header>

        <main className="px-4 py-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/boards" element={<BoardsPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/posts" element={<PostsPage />} />
            <Route
              path="/translations"
              element={
                <PlaceholderPage
                  title="번역 이력"
                  description="OCR/번역 파이프라인 실행 이력과 실패 사유를 조회합니다."
                />
              }
            />
            <Route path="/comments" element={<FilteredCommentsPage />} />
            <Route
              path="/logs"
              element={
                <PlaceholderPage
                  title="관리자 로그"
                  description="권한 변경, 게시판 수정 등 관리자 작업 이력을 조회합니다."
                />
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}
