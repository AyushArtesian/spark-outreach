import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Mail, RefreshCw, Sparkles, XCircle } from "lucide-react";

export type SmartLeadAction = "send_message" | "follow_up" | "enrich_profile" | "not_fit";

interface LeadActionPanelProps {
  recommendedAction: SmartLeadAction;
  onAction: (action: SmartLeadAction) => void;
  isLoading: (action: SmartLeadAction) => boolean;
}

const actionLabels: Record<SmartLeadAction, string> = {
  send_message: "Send message",
  follow_up: "Follow up",
  enrich_profile: "Enrich profile",
  not_fit: "Not a fit",
};

const actionIcons = {
  send_message: Mail,
  follow_up: RefreshCw,
  enrich_profile: Sparkles,
  not_fit: XCircle,
};

export default function LeadActionPanel({
  recommendedAction,
  onAction,
  isLoading,
}: LeadActionPanelProps) {
  const actions: SmartLeadAction[] = ["send_message", "follow_up", "enrich_profile", "not_fit"];

  return (
    <div className="mt-3 ml-14 rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="flex items-center justify-between gap-2 mb-2">
        <p className="text-xs font-semibold text-primary uppercase tracking-wide">Smart Action Panel</p>
        <p className="text-[11px] text-muted-foreground">
          Next best action: <span className="font-medium text-foreground">{actionLabels[recommendedAction]}</span>
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {actions.map((action) => {
          const Icon = actionIcons[action];
          const loading = isLoading(action);
          const highlighted = recommendedAction === action;
          return (
            <Button
              key={action}
              size="sm"
              variant={highlighted ? "default" : "outline"}
              className={cn("h-8 text-xs gap-1.5", highlighted && "ring-1 ring-primary/30")}
              onClick={() => onAction(action)}
              disabled={loading}
            >
              <Icon className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
              {loading ? "Running..." : actionLabels[action]}
            </Button>
          );
        })}
      </div>
    </div>
  );
}
