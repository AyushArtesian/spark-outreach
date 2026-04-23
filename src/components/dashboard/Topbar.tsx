import { Search, Bell, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/ThemeProvider";

interface TopbarProps {
  onOpenCommandBar: () => void;
}

export default function Topbar({ onOpenCommandBar }: TopbarProps) {
  const { theme, toggle } = useTheme();

  return (
    <header className="h-14 border-b border-border/50 flex items-center justify-between px-6 bg-card/30 backdrop-blur-xl sticky top-0 z-40">
      <button
        type="button"
        onClick={onOpenCommandBar}
        className="w-64 h-9 rounded-lg bg-muted/50 border border-border/50 px-3 text-sm text-muted-foreground flex items-center justify-between hover:border-primary/30 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Search className="w-4 h-4" />
          <span>Go to page or action...</span>
        </span>
        <span className="text-[11px] text-muted-foreground border border-border rounded px-1.5 py-0.5">Ctrl/Cmd + K</span>
      </button>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={toggle}>
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </Button>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-destructive" />
        </Button>
      </div>
    </header>
  );
}
