import { Clock3, MessageSquare, RefreshCw, Search, Sparkles, Tag } from "lucide-react";
import { ActivityEvent, ActivityEventType, formatActivityTime } from "@/lib/activityTimeline";
import { ComponentType } from "react";

interface ActivityTimelineProps {
  events: ActivityEvent[];
  emptyMessage?: string;
}

const typeStyles: Record<ActivityEventType, { dot: string; icon: ComponentType<{ className?: string }> }> = {
  search: { dot: "bg-primary", icon: Search },
  enrichment: { dot: "bg-accent", icon: Sparkles },
  message: { dot: "bg-warning", icon: MessageSquare },
  follow_up: { dot: "bg-warning", icon: RefreshCw },
  reply: { dot: "bg-success", icon: MessageSquare },
  status: { dot: "bg-muted-foreground", icon: Tag },
  ai_recommendation: { dot: "bg-success", icon: Sparkles },
  system: { dot: "bg-muted-foreground", icon: Clock3 },
};

export default function ActivityTimeline({
  events,
  emptyMessage = "No activity recorded yet.",
}: ActivityTimelineProps) {
  if (!events.length) {
    return <p className="text-sm text-muted-foreground">{emptyMessage}</p>;
  }

  return (
    <div className="space-y-4">
      {events.map((event, index) => {
        const style = typeStyles[event.type] || typeStyles.system;
        const Icon = style.icon;
        return (
          <div key={event.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`w-6 h-6 rounded-full ${style.dot} text-white flex items-center justify-center`}>
                <Icon className="w-3.5 h-3.5" />
              </div>
              {index < events.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
            </div>
            <div className="min-w-0">
              <p className="text-sm text-foreground">{event.title}</p>
              {event.description && <p className="text-xs text-muted-foreground mt-0.5">{event.description}</p>}
              <p className="text-[11px] text-muted-foreground mt-1">{formatActivityTime(event.timestamp)}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
