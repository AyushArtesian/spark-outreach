import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Users, Send, Eye, MessageSquare, Flame, Rocket, TrendingUp, TrendingDown, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Link } from "react-router-dom";
import { campaignsAPI, leadsAPI } from "@/services/api";
import { toast } from "@/hooks/use-toast";

type CampaignRecord = {
  id: string;
  title: string;
  status: string;
};

type LeadRecord = {
  id: string;
  campaign_id: string;
  name: string;
  company?: string;
  status?: string;
  message_sent?: boolean;
  opened?: boolean;
  replied?: boolean;
  created_at?: string;
  updated_at?: string;
  signal_score?: number;
  score?: {
    is_hot_lead?: boolean;
  };
};

const titleCase = (value: string) => {
  const text = String(value || "").trim().toLowerCase();
  if (!text) return "Unknown";
  return text.charAt(0).toUpperCase() + text.slice(1);
};

const formatRelativeTime = (input?: string) => {
  if (!input) return "just now";
  const date = new Date(input);
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) return "just now";
  if (diffMinutes < 60) return `${diffMinutes} min ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours} hr ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
};

const formatPercent = (value: number) => `${value.toFixed(1)}%`;

const statusColors: Record<string, string> = {
  Active: "bg-success/10 text-success",
  Paused: "bg-warning/10 text-warning",
  Completed: "bg-muted text-muted-foreground",
};

const container = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function DashboardPage() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [scanMessage, setScanMessage] = useState<string>("");
  const [campaignsData, setCampaignsData] = useState<CampaignRecord[]>([]);
  const [leadsData, setLeadsData] = useState<LeadRecord[]>([]);
  const [hotLeads, setHotLeads] = useState<LeadRecord[]>([]);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);

  const fetchAllLeads = async (): Promise<LeadRecord[]> => {
    const pageSize = 200;
    const maxPages = 10;
    const all: LeadRecord[] = [];

    for (let page = 0; page < maxPages; page += 1) {
      const batch: LeadRecord[] = await leadsAPI.all(page * pageSize, pageSize);
      if (!Array.isArray(batch) || batch.length === 0) {
        break;
      }
      all.push(...batch);
      if (batch.length < pageSize) {
        break;
      }
    }

    return all;
  };

  const loadDashboardData = async () => {
    setIsLoadingDashboard(true);
    try {
      const [campaignsRes, leadsRes, hotRes] = await Promise.all([
        campaignsAPI.list(0, 200),
        fetchAllLeads(),
        leadsAPI.hot(500),
      ]);

      setCampaignsData(Array.isArray(campaignsRes) ? campaignsRes : []);
      setLeadsData(Array.isArray(leadsRes) ? leadsRes : []);
      setHotLeads(Array.isArray(hotRes) ? hotRes : []);
    } catch (error) {
      console.error("Failed to load dashboard data", error);
      toast({
        title: "Dashboard load failed",
        description: "Could not fetch live data. Please refresh.",
      });
    } finally {
      setIsLoadingDashboard(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const pollScanStatus = async () => {
    try {
      const statusPayload = await leadsAPI.getScanStatus();
      const status = String(statusPayload?.status || "idle");
      if (status === "complete") {
        setIsScanning(false);
        const summary = statusPayload?.summary || {};
        loadDashboardData();
        toast({
          title: "Intent scan complete",
          description: `Found ${summary.new_leads_found || 0} new leads (${summary.hot_leads || 0} hot).`,
        });
      }
    } catch (error) {
      console.error("Failed to poll scan status", error);
      setIsScanning(false);
      toast({
        title: "Scan status failed",
        description: "Could not fetch scan status. Try again.",
      });
    }
  };

  useEffect(() => {
    if (!isScanning) return;

    pollScanStatus();
    const intervalId = window.setInterval(() => {
      pollScanStatus();
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [isScanning]);

  const handleRunScan = async () => {
    if (isScanning) return;
    try {
      const payload = await leadsAPI.runIntentScan();
      setScanId(String(payload?.scan_id || ""));
      setScanMessage(String(payload?.message || "Intent scan started"));
      setIsScanning(true);
      toast({
        title: "Scanning job boards",
        description: "Looking for new intent-rich leads.",
      });
    } catch (error) {
      console.error("Failed to run intent scan", error);
      toast({
        title: "Scan failed to start",
        description: "Please retry in a moment.",
      });
    }
  };

  const hotLeadIdSet = useMemo(() => new Set(hotLeads.map((lead) => String(lead.id))), [hotLeads]);

  const sentCount = useMemo(
    () =>
      leadsData.filter((lead) => {
        const status = String(lead.status || "").toLowerCase();
        return Boolean(lead.message_sent) || ["contacted", "replied", "converted"].includes(status);
      }).length,
    [leadsData]
  );

  const openedCount = useMemo(() => leadsData.filter((lead) => Boolean(lead.opened)).length, [leadsData]);
  const repliedCount = useMemo(() => leadsData.filter((lead) => Boolean(lead.replied)).length, [leadsData]);
  const activeCampaignsCount = useMemo(
    () => campaignsData.filter((campaign) => String(campaign.status).toLowerCase() === "active").length,
    [campaignsData]
  );

  const stats = useMemo(
    () => [
      { label: "Total Prospects", value: leadsData.length.toLocaleString(), change: "Live", up: true, icon: Users },
      { label: "Emails Sent", value: sentCount.toLocaleString(), change: "Live", up: true, icon: Send },
      {
        label: "Open Rate",
        value: formatPercent(sentCount > 0 ? (openedCount / sentCount) * 100 : 0),
        change: "Live",
        up: true,
        icon: Eye,
      },
      { label: "Replies", value: repliedCount.toLocaleString(), change: "Live", up: true, icon: MessageSquare },
      { label: "Hot Leads", value: hotLeads.length.toLocaleString(), change: "Live", up: true, icon: Flame },
      { label: "Active Campaigns", value: activeCampaignsCount.toLocaleString(), change: "Running", up: true, icon: Rocket },
    ],
    [activeCampaignsCount, hotLeads.length, leadsData.length, openedCount, repliedCount, sentCount]
  );

  const chartData = useMemo(() => {
    const days = 30;
    const now = new Date();
    const bucketMap: Record<string, { day: string; sent: number; opened: number; replied: number }> = {};

    for (let i = days - 1; i >= 0; i -= 1) {
      const date = new Date(now);
      date.setDate(now.getDate() - i);
      const key = date.toISOString().slice(0, 10);
      bucketMap[key] = {
        day: date.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        sent: 0,
        opened: 0,
        replied: 0,
      };
    }

    for (const lead of leadsData) {
      const createdAt = lead.created_at ? new Date(lead.created_at) : null;
      if (!createdAt || Number.isNaN(createdAt.getTime())) continue;
      const key = createdAt.toISOString().slice(0, 10);
      if (!bucketMap[key]) continue;

      const status = String(lead.status || "").toLowerCase();
      const wasSent = Boolean(lead.message_sent) || ["contacted", "replied", "converted"].includes(status);
      if (wasSent) bucketMap[key].sent += 1;
      if (lead.opened) bucketMap[key].opened += 1;
      if (lead.replied) bucketMap[key].replied += 1;
    }

    return Object.values(bucketMap);
  }, [leadsData]);

  const activities = useMemo(() => {
    const sorted = [...leadsData].sort((a, b) => {
      const aTime = new Date(a.updated_at || a.created_at || 0).getTime();
      const bTime = new Date(b.updated_at || b.created_at || 0).getTime();
      return bTime - aTime;
    });

    const mapped = sorted.slice(0, 5).map((lead) => {
      const actor = lead.name || lead.company || "A lead";
      let text = `${actor} was added as a new prospect`;
      let color = "bg-primary";

      if (lead.replied) {
        text = `${actor} replied to your outreach`;
        color = "bg-success";
      } else if (lead.opened) {
        text = `${actor} opened your email`;
        color = "bg-accent";
      } else if (lead.message_sent || String(lead.status || "").toLowerCase() === "contacted") {
        text = `Outreach sent to ${actor}`;
        color = "bg-warning";
      }

      return {
        text,
        time: formatRelativeTime(lead.updated_at || lead.created_at),
        color,
      };
    });

    if (mapped.length > 0) return mapped;
    return [{ text: "No live activity yet", time: "just now", color: "bg-muted" }];
  }, [leadsData]);

  const campaigns = useMemo(() => {
    return campaignsData.map((campaign) => {
      const related = leadsData.filter((lead) => String(lead.campaign_id) === String(campaign.id));
      const prospects = related.length;
      const sent = related.filter((lead) => {
        const status = String(lead.status || "").toLowerCase();
        return Boolean(lead.message_sent) || ["contacted", "replied", "converted"].includes(status);
      }).length;
      const opened = related.filter((lead) => Boolean(lead.opened)).length;
      const replied = related.filter((lead) => Boolean(lead.replied)).length;
      const hotLeadsCount = related.filter((lead) => {
        return (
          hotLeadIdSet.has(String(lead.id)) ||
          Boolean(lead.score?.is_hot_lead) ||
          Number(lead.signal_score || 0) >= 0.75
        );
      }).length;

      return {
        name: campaign.title,
        prospects,
        sent,
        openRate: sent > 0 ? `${Math.round((opened / sent) * 100)}%` : "0%",
        replyRate: sent > 0 ? `${Math.round((replied / sent) * 100)}%` : "0%",
        hotLeads: hotLeadsCount,
        status: titleCase(campaign.status),
      };
    });
  }, [campaignsData, hotLeadIdSet, leadsData]);

  const aiInsightSummary = useMemo(() => {
    const openRate = sentCount > 0 ? (openedCount / sentCount) * 100 : 0;
    const replyRate = sentCount > 0 ? (repliedCount / sentCount) * 100 : 0;

    if (leadsData.length === 0) {
      return "No lead data yet. Run an intent scan to populate live insights.";
    }

    return `Live snapshot: ${leadsData.length.toLocaleString()} prospects, ${formatPercent(openRate)} open rate, ${formatPercent(replyRate)} reply rate, and ${hotLeads.length.toLocaleString()} hot leads across ${activeCampaignsCount} active campaigns.`;
  }, [activeCampaignsCount, hotLeads.length, leadsData.length, openedCount, repliedCount, sentCount]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Monitor outreach and discover new leads daily.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadDashboardData} disabled={isLoadingDashboard}>
            {isLoadingDashboard ? "Refreshing..." : "Refresh Data"}
          </Button>
          <Button onClick={handleRunScan} disabled={isScanning} className="gap-2">
          {isScanning ? (
            <>
              <div className="w-4 h-4 rounded-full border-2 border-primary-foreground border-t-transparent animate-spin" />
              Scanning job boards...
            </>
          ) : (
            <>Find New Leads</>
          )}
          </Button>
        </div>
      </div>

      {isScanning && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-foreground">
          Scanning job boards... {scanMessage || "In progress"}
          {scanId ? ` (Scan ID: ${scanId})` : ""}
        </div>
      )}

      {/* Stats */}
      <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stats.map((s) => (
          <motion.div key={s.label} variants={item} className="glass-card rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <s.icon className="w-4 h-4 text-muted-foreground" />
              {s.up ? <TrendingUp className="w-3 h-3 text-success" /> : <TrendingDown className="w-3 h-3 text-destructive" />}
            </div>
            <div className="text-2xl font-display font-bold text-foreground">{s.value}</div>
            <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
            <div className="text-xs text-success mt-0.5">{s.change}</div>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Chart */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="lg:col-span-2 glass-card rounded-xl p-6">
          <h3 className="font-display font-semibold text-foreground mb-4">Campaign Performance (30 days)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} interval={4} />
              <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="sent" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="opened" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="replied" stroke="hsl(var(--success))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="flex gap-6 mt-4 text-xs">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-primary" /> Sent</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-accent" /> Opened</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-success" /> Replied</span>
          </div>
        </motion.div>

        {/* Activity Feed */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card rounded-xl p-6">
          <h3 className="font-display font-semibold text-foreground mb-4">Recent Activity</h3>
          <div className="space-y-4">
            {activities.map((a, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${a.color}`} />
                <div>
                  <p className="text-sm text-foreground">{a.text}</p>
                  <p className="text-xs text-muted-foreground">{a.time}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* AI Insight */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }} className="rounded-xl p-6 gradient-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_50%,rgba(255,255,255,0.1),transparent)]" />
        <div className="relative flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <Sparkles className="w-8 h-8 text-primary-foreground shrink-0" />
          <div className="flex-1">
            <h3 className="font-display font-semibold text-primary-foreground">AI Insight</h3>
            <p className="text-primary-foreground/80 text-sm mt-1">
              {aiInsightSummary}
            </p>
          </div>
          <Button className="bg-background/20 text-primary-foreground border border-primary-foreground/20 hover:bg-background/30 shrink-0">
            Optimize Now
          </Button>
        </div>
      </motion.div>

      {/* Top Campaigns Table */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="glass-card rounded-xl overflow-hidden">
        <div className="p-6 pb-0">
          <h3 className="font-display font-semibold text-foreground">Top Performing Campaigns</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-left p-4 text-muted-foreground font-medium">Campaign</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Prospects</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Sent</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Open Rate</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Reply Rate</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Hot Leads</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.name} className="border-b border-border/30 hover:bg-muted/30 transition-colors">
                  <td className="p-4 font-medium text-foreground">{c.name}</td>
                  <td className="p-4 text-muted-foreground">{c.prospects.toLocaleString()}</td>
                  <td className="p-4 text-muted-foreground">{c.sent.toLocaleString()}</td>
                  <td className="p-4 text-foreground">{c.openRate}</td>
                  <td className="p-4 text-foreground">{c.replyRate}</td>
                  <td className="p-4 text-foreground">{c.hotLeads}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[c.status] || "bg-muted text-muted-foreground"}`}>
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "New Campaign", path: "/campaigns/new", icon: Rocket },
          { label: "Import Prospects", path: "/prospects", icon: Users },
          { label: "Review Queue", path: "/review", icon: MessageSquare },
          { label: "View Hot Leads", path: "/prospects", icon: Flame },
        ].map((a) => (
          <Link key={a.label} to={a.path}>
            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2 hover:border-primary/50">
              <a.icon className="w-5 h-5" />
              <span>{a.label}</span>
            </Button>
          </Link>
        ))}
      </div>
    </div>
  );
}
