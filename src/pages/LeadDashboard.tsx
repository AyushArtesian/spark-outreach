import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Users, Star, Search, TrendingUp, ArrowRight, Sparkles, Target, Zap, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from "recharts";
import { campaignsAPI, leadsAPI } from "@/services/api";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

type CampaignRecord = {
  id: string;
  title: string;
  status: string;
  services?: string[];
  target_locations?: string[];
  updated_at?: string;
};

type LeadRecord = {
  id: string;
  campaign_id: string;
  name: string;
  company?: string;
  industry?: string;
  status?: string;
  message_sent?: boolean;
  opened?: boolean;
  replied?: boolean;
  converted?: boolean;
  created_at?: string;
  updated_at?: string;
  signal_keywords?: string[];
  company_fit_score?: number;
  signal_score?: number;
  raw_data?: Record<string, any>;
  score?: {
    total_score?: number;
    grade?: "A" | "B" | "C" | "D";
    is_hot_lead?: boolean;
  };
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

const titleCase = (value?: string) => {
  const text = String(value || "").trim().toLowerCase();
  if (!text) return "Unknown";
  return text.charAt(0).toUpperCase() + text.slice(1);
};

const priorityColors: Record<string, string> = {
  High: "bg-warning/10 text-warning border-warning/20",
  Medium: "bg-accent/10 text-accent border-accent/20",
  Low: "bg-muted text-muted-foreground border-border",
};

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function LeadDashboard() {
  const { user } = useAuth();
  const [campaignsData, setCampaignsData] = useState<CampaignRecord[]>([]);
  const [leadsData, setLeadsData] = useState<LeadRecord[]>([]);
  const [hotLeads, setHotLeads] = useState<LeadRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAllLeads = async (): Promise<LeadRecord[]> => {
    const pageSize = 200;
    const maxPages = 10;
    const all: LeadRecord[] = [];

    for (let page = 0; page < maxPages; page += 1) {
      const batch: LeadRecord[] = await leadsAPI.all(page * pageSize, pageSize);
      if (!Array.isArray(batch) || batch.length === 0) break;
      all.push(...batch);
      if (batch.length < pageSize) break;
    }

    return all;
  };

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [campaignsRes, leadsRes, hotRes] = await Promise.all([
        campaignsAPI.list(0, 200),
        fetchAllLeads(),
        leadsAPI.hot(200),
      ]);

      setCampaignsData(Array.isArray(campaignsRes) ? campaignsRes : []);
      setLeadsData(Array.isArray(leadsRes) ? leadsRes : []);
      setHotLeads(Array.isArray(hotRes) ? hotRes : []);
    } catch (error) {
      console.error("Failed to load lead dashboard", error);
      toast({
        title: "Dashboard load failed",
        description: "Could not fetch live dashboard data.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const activeCampaignCount = useMemo(
    () => campaignsData.filter((campaign) => String(campaign.status || "").toLowerCase() === "active").length,
    [campaignsData]
  );

  const thisWeekCount = useMemo(() => {
    const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    return leadsData.filter((lead) => {
      const ts = new Date(lead.created_at || 0).getTime();
      return Number.isFinite(ts) && ts >= oneWeekAgo;
    }).length;
  }, [leadsData]);

  const sentCount = useMemo(
    () =>
      leadsData.filter((lead) => {
        const status = String(lead.status || "").toLowerCase();
        return Boolean(lead.message_sent) || ["contacted", "replied", "converted"].includes(status);
      }).length,
    [leadsData]
  );

  const convertedCount = useMemo(
    () =>
      leadsData.filter((lead) => {
        const status = String(lead.status || "").toLowerCase();
        return Boolean(lead.converted) || status === "converted";
      }).length,
    [leadsData]
  );

  const conversionRate = sentCount > 0 ? (convertedCount / sentCount) * 100 : 0;

  const stats = useMemo(
    () => [
      {
        label: "Total Leads Found",
        value: leadsData.length.toLocaleString(),
        change: `+${thisWeekCount.toLocaleString()} this week`,
        icon: Users,
        color: "text-primary",
      },
      {
        label: "High Priority",
        value: hotLeads.length.toLocaleString(),
        change: "Hot leads",
        icon: Star,
        color: "text-warning",
      },
      {
        label: "Conversion Rate",
        value: formatPercent(conversionRate),
        change: `${convertedCount.toLocaleString()} converted`,
        icon: TrendingUp,
        color: "text-success",
      },
      {
        label: "Active Searches",
        value: activeCampaignCount.toLocaleString(),
        change: "Live from campaigns",
        icon: Search,
        color: "text-accent",
      },
    ],
    [activeCampaignCount, convertedCount, conversionRate, hotLeads.length, leadsData.length, thisWeekCount]
  );

  const trendData = useMemo(() => {
    const days = 14;
    const now = new Date();
    const bucketMap: Record<string, { day: string; leads: number; highPriority: number }> = {};

    for (let i = days - 1; i >= 0; i -= 1) {
      const date = new Date(now);
      date.setDate(now.getDate() - i);
      const key = date.toISOString().slice(0, 10);
      bucketMap[key] = {
        day: date.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        leads: 0,
        highPriority: 0,
      };
    }

    for (const lead of leadsData) {
      const createdAt = lead.created_at ? new Date(lead.created_at) : null;
      if (!createdAt || Number.isNaN(createdAt.getTime())) continue;
      const key = createdAt.toISOString().slice(0, 10);
      if (!bucketMap[key]) continue;

      bucketMap[key].leads += 1;
      if (lead.score?.is_hot_lead || hotLeads.some((hotLead) => hotLead.id === lead.id)) {
        bucketMap[key].highPriority += 1;
      }
    }

    return Object.values(bucketMap);
  }, [hotLeads, leadsData]);

  const industryData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const lead of leadsData) {
      const key = titleCase(lead.industry || "Unknown");
      counts[key] = (counts[key] || 0) + 1;
    }

    const rows = Object.entries(counts)
      .map(([name, leads]) => ({ name, leads }))
      .sort((a, b) => b.leads - a.leads)
      .slice(0, 5);

    if (rows.length > 0) return rows;
    return [{ name: "No Data", leads: 0 }];
  }, [leadsData]);

  const recentSearches = useMemo(() => {
    const leadsByCampaign = leadsData.reduce<Record<string, LeadRecord[]>>((acc, lead) => {
      const key = String(lead.campaign_id || "");
      if (!acc[key]) acc[key] = [];
      acc[key].push(lead);
      return acc;
    }, {});

    const extractLocationFromLeads = (campaignLeads: LeadRecord[]): string => {
      if (campaignLeads.length === 0) return "Any location";
      
      // Try to extract locations from leads' raw_data or industry
      const locations: Record<string, number> = {};
      for (const lead of campaignLeads) {
        // Check raw_data for location
        const location = lead.raw_data?.location || lead.industry || "Unknown";
        locations[location] = (locations[location] || 0) + 1;
      }
      
      // Return most common location
      const topLocation = Object.entries(locations)
        .sort((a, b) => b[1] - a[1])[0]?.[0];
      
      return topLocation && topLocation !== "Unknown" ? topLocation : "Any location";
    };

    const items = campaignsData
      .slice()
      .sort((a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime())
      .slice(0, 4)
      .map((campaign) => {
        const campaignLeads = leadsByCampaign[String(campaign.id)] || [];
        
        // First try campaign target_locations, then extract from leads
        let location = campaign.target_locations?.[0] || "";
        if (!location) {
          location = extractLocationFromLeads(campaignLeads);
        }
        
        const service = campaign.services?.[0] || campaign.title;
        return {
          id: campaign.id,
          location,
          service,
          leads: campaignLeads.length,
          date: formatRelativeTime(campaign.updated_at),
        };
      });

    if (items.length > 0) return items;
    return [{ id: "no-data", location: "No searches yet", service: "Create a campaign", leads: 0, date: "just now" }];
  }, [campaignsData, leadsData]);

  const topLeads = useMemo(() => {
    const normalized = leadsData
      .slice()
      .sort((a, b) => {
        const scoreA = Number(a.score?.total_score || 0);
        const scoreB = Number(b.score?.total_score || 0);
        if (scoreA !== scoreB) return scoreB - scoreA;
        return Number(b.signal_score || 0) - Number(a.signal_score || 0);
      })
      .slice(0, 4)
      .map((lead) => {
        const totalScore = Number(lead.score?.total_score || 0);
        const priority = totalScore >= 80 || lead.score?.grade === "A" ? "High" : totalScore >= 60 || lead.score?.grade === "B" ? "Medium" : "Low";
        const reasonFromSignals = Array.isArray(lead.signal_keywords) && lead.signal_keywords.length > 0
          ? lead.signal_keywords.slice(0, 2).join(", ")
          : "Strong fit from current signals";

        return {
          id: lead.id,
          company: lead.company || lead.name,
          score: totalScore > 0 ? totalScore / 10 : Number((Number(lead.signal_score || 0) * 10).toFixed(1)),
          location: lead.industry || "Unknown industry",
          reason: reasonFromSignals,
          priority,
        };
      });

    if (normalized.length > 0) return normalized;
    return [{ id: "no-lead", company: "No leads yet", score: 0, location: "-", reason: "Run a lead search to see top matches", priority: "Low" }];
  }, [leadsData]);

  const aiRecommendation = useMemo(() => {
    if (leadsData.length === 0) {
      return "No lead data available yet. Run a search or intent scan to generate recommendations.";
    }

    const bestIndustry = industryData[0]?.name || "your target segment";
    return `Live signal: ${bestIndustry} currently leads with ${industryData[0]?.leads || 0} prospects. You have ${hotLeads.length} hot leads and ${convertedCount} conversions so far.`;
  }, [convertedCount, hotLeads.length, industryData, leadsData.length]);

  const firstName = (user?.full_name || user?.username || "there").split(" ")[0];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading live dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Welcome back, {firstName}</h1>
          <p className="text-muted-foreground text-sm mt-1">Here's your lead intelligence overview</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={loadDashboardData}>Refresh</Button>
          <Link to="/search">
            <Button variant="gradient" size="lg" className="gap-2">
              <Search className="w-4 h-4" /> Search Leads
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <motion.div variants={container} initial="hidden" animate="show" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <motion.div key={s.label} variants={item}>
            <Card className="border-border/50 shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-muted ${s.color}`}>
                    <s.icon className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-2xl font-display font-bold text-foreground">{s.value}</div>
                <div className="text-xs text-muted-foreground mt-1">{s.label}</div>
                <div className="text-xs text-success mt-1">{s.change}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Lead Trend Chart */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="lg:col-span-1 border-border/50 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-display">Lead Trend (14 days)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="leadGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} interval={2} />
                  <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                  <Area type="monotone" dataKey="leads" stroke="hsl(var(--primary))" fill="url(#leadGrad)" strokeWidth={2} />
                  <Area type="monotone" dataKey="highPriority" stroke="hsl(var(--warning))" fill="none" strokeWidth={2} strokeDasharray="4 4" />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-primary" /> Total</span>
                <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-warning" /> High Priority</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Industry Distribution */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
          <Card className="border-border/50 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-display">Leads by Industry</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={industryData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} width={80} />
                  <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="leads" fill="hsl(var(--primary))" radius={[0, 6, 6, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Searches */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card className="border-border/50 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-display">Recent Searches</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentSearches.map((s, i) => (
                  <div key={s.id || i} className="flex items-center justify-between p-2.5 rounded-xl bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer">
                    <div>
                      <div className="text-sm font-medium text-foreground">{s.location}</div>
                      <div className="text-xs text-muted-foreground">{s.service}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-foreground">{s.leads} leads</div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="w-3 h-3" /> {s.date}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* AI Insight */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
        <Card className="border-primary/20 bg-primary/5 shadow-sm">
          <CardContent className="p-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center shrink-0">
                <Sparkles className="w-5 h-5 text-primary-foreground" />
              </div>
              <div className="flex-1">
                <h3 className="font-display font-semibold text-foreground">AI Recommendation</h3>
                <p className="text-muted-foreground text-sm mt-1">
                  {aiRecommendation}
                </p>
              </div>
              <Link to="/ai-insights">
                <Button variant="default" className="shrink-0 gap-1">
                  View Insights <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Top Leads */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-display">Top Leads Today</CardTitle>
              <Link to="/leads">
                <Button variant="ghost" size="sm" className="text-xs gap-1">View All <ArrowRight className="w-3 h-3" /></Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {topLeads.map((lead) => (
                <Link key={lead.id} to={lead.id === "no-lead" ? "/search" : `/lead/${lead.id}`} className="block">
                  <div className="p-4 rounded-xl border border-border/50 hover:border-primary/30 hover:shadow-md transition-all group cursor-pointer">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${priorityColors[lead.priority]}`}>
                        {lead.priority}
                      </span>
                      <div className="text-lg font-display font-bold text-primary">{lead.score}</div>
                    </div>
                    <h4 className="font-semibold text-foreground text-sm group-hover:text-primary transition-colors">{lead.company}</h4>
                    <p className="text-xs text-muted-foreground mt-0.5">{lead.location}</p>
                    <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{lead.reason}</p>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Search Leads", path: "/search", icon: Search },
          { label: "Setup Profile", path: "/company-setup", icon: Target },
          { label: "View All Leads", path: "/leads", icon: Users },
          { label: "AI Insights", path: "/leads", icon: Zap },
        ].map((a) => (
          <Link key={a.label} to={a.path}>
            <Button variant="outline" className="w-full h-auto py-4 flex flex-col gap-2 hover:border-primary/50 transition-all">
              <a.icon className="w-5 h-5" />
              <span className="text-sm">{a.label}</span>
            </Button>
          </Link>
        ))}
      </div>
    </div>
  );
}
