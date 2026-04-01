import { motion } from "framer-motion";
import { Users, Send, Eye, MessageSquare, Flame, Rocket, TrendingUp, TrendingDown, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Link } from "react-router-dom";

const stats = [
  { label: "Total Prospects", value: "12,480", change: "+12.3%", up: true, icon: Users },
  { label: "Emails Sent", value: "3,240", change: "This week", up: true, icon: Send },
  { label: "Open Rate", value: "47.3%", change: "+5.2%", up: true, icon: Eye },
  { label: "Replies", value: "284", change: "+18", up: true, icon: MessageSquare },
  { label: "Hot Leads 🔥", value: "38", change: "+7", up: true, icon: Flame },
  { label: "Active Campaigns", value: "5", change: "Running", up: true, icon: Rocket },
];

const chartData = Array.from({ length: 30 }, (_, i) => ({
  day: `Day ${i + 1}`,
  sent: Math.floor(80 + Math.random() * 60),
  opened: Math.floor(30 + Math.random() * 40),
  replied: Math.floor(5 + Math.random() * 15),
}));

const activities = [
  { text: "John Smith opened your email", time: "2 min ago", color: "bg-accent" },
  { text: "Sarah Lee replied to Follow-up 2", time: "5 min ago", color: "bg-success" },
  { text: "New prospect batch ready: 340 leads", time: "12 min ago", color: "bg-primary" },
  { text: "Campaign 'SaaS Founders Q4' completed", time: "1 hr ago", color: "bg-warning" },
  { text: "AI optimized 23 subject lines", time: "2 hrs ago", color: "bg-primary" },
];

const campaigns = [
  { name: "SaaS Founders Q4", prospects: 2400, sent: 1820, openRate: "52%", replyRate: "14%", hotLeads: 12, status: "Active" },
  { name: "E-commerce Directors", prospects: 1800, sent: 1200, openRate: "44%", replyRate: "11%", hotLeads: 8, status: "Active" },
  { name: "FinTech CEOs", prospects: 3200, sent: 3200, openRate: "38%", replyRate: "9%", hotLeads: 14, status: "Completed" },
  { name: "Agency Owners", prospects: 1600, sent: 890, openRate: "51%", replyRate: "16%", hotLeads: 4, status: "Active" },
];

const statusColors: Record<string, string> = {
  Active: "bg-success/10 text-success",
  Paused: "bg-warning/10 text-warning",
  Completed: "bg-muted text-muted-foreground",
};

const container = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function DashboardPage() {
  return (
    <div className="space-y-6">
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
              Subject lines with questions get 2.3x more opens. Your Campaign #3 is underperforming — click to auto-optimize.
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
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[c.status]}`}>
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
