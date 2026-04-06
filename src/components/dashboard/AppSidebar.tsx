import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Search, Users, Building2, Settings, Zap, ChevronLeft, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: Building2, label: "Setup Profile", path: "/company-setup" },
  { icon: Search, label: "Search Leads", path: "/search" },
  { icon: Users, label: "Leads", path: "/leads" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

export default function AppSidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      className="h-screen sticky top-0 flex flex-col border-r border-border/50 bg-card/80 backdrop-blur-xl"
    >
      <div className="flex items-center gap-2 p-4 border-b border-border/50">
        <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0">
          <Sparkles className="w-5 h-5 text-primary-foreground" />
        </div>
        {!collapsed && <span className="font-display font-bold text-foreground">LeadIntel AI</span>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft className={cn("w-4 h-4 transition-transform", collapsed && "rotate-180")} />
        </button>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              )}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-xs font-bold text-primary-foreground shrink-0">
            JD
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <div className="text-sm font-medium text-foreground truncate">John Doe</div>
              <div className="text-xs text-muted-foreground truncate">john@acmesoftware.com</div>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
