import { motion } from "framer-motion";
import { Users, Star, Search, TrendingUp, ArrowRight, Sparkles, Target, Zap, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from "recharts";

const stats = [
  { label: "Total Leads Found", value: "1,247", change: "+89 this week", icon: Users, color: "text-primary" },
  { label: "High Priority", value: "38", change: "Score 8+", icon: Star, color: "text-warning" },
  { label: "Conversion Rate", value: "23.4%", change: "+4.2% vs last month", icon: TrendingUp, color: "text-success" },
  { label: "Active Searches", value: "3", change: "Running now", icon: Search, color: "text-accent" },
];

const trendData = Array.from({ length: 14 }, (_, i) => ({
  day: `Day ${i + 1}`,
  leads: Math.floor(60 + Math.random() * 80),
  highPriority: Math.floor(5 + Math.random() * 15),
}));

const industryData = [
  { name: "SaaS", leads: 340 },
  { name: "FinTech", leads: 280 },
  { name: "Healthcare", leads: 210 },
  { name: "E-commerce", leads: 190 },
  { name: "EdTech", leads: 120 },
];

const recentSearches = [
  { location: "San Francisco, CA", service: "Cloud Migration", leads: 142, date: "2 hours ago" },
  { location: "New York, NY", service: "AI/ML Development", leads: 89, date: "Yesterday" },
  { location: "Austin, TX", service: "Mobile App Dev", leads: 67, date: "2 days ago" },
  { location: "London, UK", service: "DevOps Consulting", leads: 234, date: "3 days ago" },
];

const topLeads = [
  { company: "TechVault Inc.", score: 9.4, location: "San Francisco", reason: "Hiring 5 engineers, matches past project", priority: "High" },
  { company: "NovaPay Systems", score: 8.9, location: "New York", reason: "Series B, expanding tech team", priority: "High" },
  { company: "GreenLeaf Health", score: 8.2, location: "Austin", reason: "Needs cloud migration, similar to ProjectX", priority: "High" },
  { company: "DataStream AI", score: 7.8, location: "London", reason: "Posted RFP for ML pipeline", priority: "Medium" },
];

const priorityColors: Record<string, string> = {
  High: "bg-warning/10 text-warning border-warning/20",
  Medium: "bg-accent/10 text-accent border-accent/20",
  Low: "bg-muted text-muted-foreground border-border",
};

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function LeadDashboard() {
  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Welcome back, John</h1>
          <p className="text-muted-foreground text-sm mt-1">Here's your lead intelligence overview</p>
        </div>
        <Link to="/search">
          <Button variant="gradient" size="lg" className="gap-2">
            <Search className="w-4 h-4" /> Search Leads
          </Button>
        </Link>
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
                  <div key={i} className="flex items-center justify-between p-2.5 rounded-xl bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer">
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
                  Based on your past wins, <strong className="text-foreground">FinTech companies in New York</strong> hiring backend engineers have a 3.2x higher conversion rate. We found 12 new matches today.
                </p>
              </div>
              <Link to="/search">
                <Button variant="default" className="shrink-0 gap-1">
                  View Matches <ArrowRight className="w-4 h-4" />
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
                <Link key={lead.company} to="/lead/1" className="block">
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
