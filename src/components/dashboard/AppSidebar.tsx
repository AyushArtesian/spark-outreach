import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Rocket, Users, MessageSquare, BarChart3, Brain, Settings, Zap, ChevronLeft, Crown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: Rocket, label: "Campaigns", path: "/campaigns" },
  { icon: Users, label: "Prospects", path: "/prospects" },
  { icon: MessageSquare, label: "Review Queue", path: "/review", badge: 47 },
  { icon: BarChart3, label: "Analytics", path: "/analytics" },
  { icon: Brain, label: "AI Learning", path: "/ai-learning" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

export default function AppSidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      className="h-screen sticky top-0 flex flex-col border-r border-border/50 bg-card/50 backdrop-blur-xl"
    >
      <div className="flex items-center gap-2 p-4 border-b border-border/50">
        <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0">
          <Zap className="w-5 h-5 text-primary-foreground" />
        </div>
        {!collapsed && <span className="font-display font-bold text-foreground">OutreachAI</span>}
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
              {!collapsed && item.badge && (
                <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary font-semibold">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {!collapsed && (
        <div className="p-3 border-t border-border/50">
          <div className="glass-card rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Crown className="w-4 h-4 text-warning" />
              <span className="text-xs font-semibold text-foreground">Pro Plan</span>
            </div>
            <p className="text-xs text-muted-foreground mb-2">3,240 / 10,000 emails used</p>
            <div className="w-full h-1.5 rounded-full bg-muted">
              <div className="h-full rounded-full gradient-primary" style={{ width: "32%" }} />
            </div>
          </div>
        </div>
      )}

      <div className="p-3 border-t border-border/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-xs font-bold text-primary-foreground shrink-0">
            JD
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <div className="text-sm font-medium text-foreground truncate">John Doe</div>
              <div className="text-xs text-muted-foreground truncate">john@company.com</div>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
