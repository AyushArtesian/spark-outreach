import { useState } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Sparkles, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

const ranges = ["7d", "14d", "30d", "90d"];

const kpis = [
  { label: "Total Sent", value: "14,280" },
  { label: "Delivery Rate", value: "98.2%" },
  { label: "Open Rate", value: "47.3%" },
  { label: "Click Rate", value: "8.1%" },
  { label: "Reply Rate", value: "12.4%" },
  { label: "Bounce Rate", value: "1.8%" },
  { label: "Unsubscribe", value: "0.3%" },
];

const areaData = Array.from({ length: 30 }, (_, i) => ({
  day: `${i + 1}`,
  sends: Math.floor(100 + Math.random() * 80),
  opens: Math.floor(40 + Math.random() * 50),
  replies: Math.floor(5 + Math.random() * 20),
}));

const subjectData = [
  { subject: "Quick question about {{company}}", rate: 58 },
  { subject: "Congrats on the funding!", rate: 54 },
  { subject: "Idea for {{company}}", rate: 49 },
  { subject: "{{first_name}}, saw your post", rate: 45 },
  { subject: "Can we help {{company}} grow?", rate: 41 },
];

const dayData = [
  { day: "Mon", rate: 42 }, { day: "Tue", rate: 61 }, { day: "Wed", rate: 48 },
  { day: "Thu", rate: 45 }, { day: "Fri", rate: 39 }, { day: "Sat", rate: 22 }, { day: "Sun", rate: 18 },
];

const toneData = [
  { name: "Professional", value: 42, color: "hsl(263, 70%, 58%)" },
  { name: "Friendly", value: 35, color: "hsl(187, 92%, 43%)" },
  { name: "Bold", value: 23, color: "hsl(160, 84%, 39%)" },
];

const insights = [
  "Tuesday 10AM has your highest open rate (61%)",
  "Questions in subject lines outperform statements by 2.4x",
  "Follow-up 2 gets 40% of all your replies — don't skip it",
  "Your LinkedIn messages outperform emails by 23%",
];

export default function AnalyticsPage() {
  const [range, setRange] = useState("30d");

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-display font-bold text-foreground">Analytics</h1>
        <div className="flex gap-1 bg-muted/50 rounded-lg p-1">
          {ranges.map((r) => (
            <button key={r} onClick={() => setRange(r)} className={`px-3 py-1 rounded-md text-sm transition-all ${range === r ? "gradient-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>{r}</button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {kpis.map((k) => (
          <div key={k.label} className="glass-card rounded-xl p-4 text-center">
            <div className="text-xl font-display font-bold text-foreground">{k.value}</div>
            <div className="text-xs text-muted-foreground mt-1">{k.label}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Area Chart */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-xl p-6">
          <h3 className="font-display font-semibold text-foreground mb-4">Sends vs Opens vs Replies</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={areaData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }} />
              <Area type="monotone" dataKey="sends" stroke="hsl(var(--primary))" fill="hsl(var(--primary) / 0.15)" strokeWidth={2} />
              <Area type="monotone" dataKey="opens" stroke="hsl(var(--accent))" fill="hsl(var(--accent) / 0.15)" strokeWidth={2} />
              <Area type="monotone" dataKey="replies" stroke="hsl(var(--success))" fill="hsl(var(--success) / 0.15)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Subject Lines */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card rounded-xl p-6">
          <h3 className="font-display font-semibold text-foreground mb-4">Best Subject Lines</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={subjectData} layout="vertical" margin={{ left: 120 }}>
              <XAxis type="number" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="subject" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} width={120} />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }} />
              <Bar dataKey="rate" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Day of Week */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card rounded-xl p-6">
          <h3 className="font-display font-semibold text-foreground mb-4">Open Rate by Day</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={dayData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }} />
              <Bar dataKey="rate" fill="hsl(var(--accent))" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Tone Pie */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card rounded-xl p-6">
          <h3 className="font-display font-semibold text-foreground mb-4">Reply Rate by Tone</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={toneData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={4} dataKey="value">
                {toneData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 text-xs">
            {toneData.map((t) => (
              <span key={t.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ background: t.color }} />
                {t.name}
              </span>
            ))}
          </div>
        </motion.div>
      </div>

      {/* AI Insights */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="glass-card rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-primary" />
          <h3 className="font-display font-semibold text-foreground">AI Insights</h3>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {insights.map((insight, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-lg bg-muted/30 border border-border/50">
              <TrendingUp className="w-4 h-4 text-accent shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-foreground">{insight}</p>
                <Button variant="ghost" size="sm" className="mt-2 text-primary text-xs px-0">Apply to Campaigns →</Button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
