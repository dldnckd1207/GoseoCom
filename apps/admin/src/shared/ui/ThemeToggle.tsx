import { Moon, Sun } from "lucide-react";

import { useTheme } from "~/shared/stores/themeContext";
import { Button } from "~/shared/ui/button";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <Button
      type="button"
      variant="outline"
      size="icon"
      className="size-9"
      onClick={toggleTheme}
      aria-label={isDark ? "라이트 모드로 변경" : "다크 모드로 변경"}
      title={isDark ? "라이트 모드" : "다크 모드"}
    >
      {isDark ? <Sun /> : <Moon />}
    </Button>
  );
}
