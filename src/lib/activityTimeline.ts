export type ActivityEventType =
  | "search"
  | "enrichment"
  | "message"
  | "follow_up"
  | "reply"
  | "status"
  | "ai_recommendation"
  | "system";

export interface ActivityEvent {
  id: string;
  timestamp: string;
  type: ActivityEventType;
  title: string;
  description?: string;
  leadId?: string;
  leadName?: string;
  company?: string;
}

type NewActivityEvent = Omit<ActivityEvent, "id" | "timestamp"> & {
  timestamp?: string;
};

const STORAGE_KEY = "spark_activity_timeline_v1";
const MAX_EVENTS = 500;

const safeParse = (raw: string | null): ActivityEvent[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => item && typeof item === "object");
  } catch {
    return [];
  }
};

const readAll = (): ActivityEvent[] => {
  if (typeof window === "undefined") return [];
  return safeParse(window.localStorage.getItem(STORAGE_KEY));
};

const writeAll = (events: ActivityEvent[]) => {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(0, MAX_EVENTS)));
};

export const logActivityEvent = (event: NewActivityEvent) => {
  const now = new Date().toISOString();
  const normalized: ActivityEvent = {
    id: `evt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    timestamp: event.timestamp || now,
    type: event.type,
    title: event.title,
    description: event.description,
    leadId: event.leadId,
    leadName: event.leadName,
    company: event.company,
  };
  const current = readAll();
  writeAll([normalized, ...current]);
};

export const getAccountActivityEvents = (limit = 20): ActivityEvent[] => {
  return readAll()
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, limit);
};

export const getLeadActivityEvents = (leadId: string, limit = 30): ActivityEvent[] => {
  if (!leadId) return [];
  return readAll()
    .filter((item) => item.leadId === leadId)
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, limit);
};

export const formatActivityTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  const diffMs = Date.now() - date.getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleString();
};
