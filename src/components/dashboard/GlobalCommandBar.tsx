import { useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  FolderKanban,
  Lightbulb,
  ListChecks,
  Search,
  Settings,
  Sparkles,
  UserRound,
} from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command";

interface GlobalCommandBarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type CommandAction = {
  id: string;
  label: string;
  hint: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  group: "Navigation";
};

const COMMANDS: CommandAction[] = [
  { id: "dashboard", label: "Dashboard", hint: "Overview", to: "/dashboard", icon: BarChart3, group: "Navigation" },
  { id: "setup", label: "Setup Profile", hint: "Company setup", to: "/company-setup", icon: UserRound, group: "Navigation" },
  { id: "search", label: "Search Leads", hint: "New discovery", to: "/search", icon: Search, group: "Navigation" },
  { id: "all-leads", label: "All Leads", hint: "Lead database", to: "/all-leads", icon: ListChecks, group: "Navigation" },
  { id: "lead-results", label: "Lead Results", hint: "Latest search output", to: "/leads", icon: Sparkles, group: "Navigation" },
  { id: "campaigns", label: "Campaigns", hint: "Manage campaigns", to: "/campaigns", icon: FolderKanban, group: "Navigation" },
  { id: "new-campaign", label: "New Campaign", hint: "Create campaign", to: "/campaigns/new", icon: Lightbulb, group: "Navigation" },
  { id: "insights", label: "AI Insights", hint: "Intelligence report", to: "/ai-insights", icon: Sparkles, group: "Navigation" },
  { id: "settings", label: "Settings", hint: "Account preferences", to: "/settings", icon: Settings, group: "Navigation" },
];

export default function GlobalCommandBar({ open, onOpenChange }: GlobalCommandBarProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const groups = useMemo(() => {
    return {
      Navigation: COMMANDS.filter((command) => command.group === "Navigation"),
    };
  }, []);

  const handleSelect = (to: string) => {
    onOpenChange(false);
    if (location.pathname !== to) {
      navigate(to);
    }
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a page or action..." />
      <CommandList>
        <CommandEmpty>No matching command.</CommandEmpty>
        <CommandGroup heading="Navigation">
          {groups.Navigation.map((command) => (
            <CommandItem key={command.id} value={`${command.label} ${command.hint} ${command.to}`} onSelect={() => handleSelect(command.to)}>
              <command.icon className="mr-2 h-4 w-4" />
              <span>{command.label}</span>
              <CommandShortcut>{command.hint}</CommandShortcut>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
