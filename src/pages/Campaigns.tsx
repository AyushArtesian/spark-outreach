import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Play, Pause, Copy, Trash2, Eye, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const campaignsData = [
  { id: 1, name: "SaaS Founders Q4", audience: "SaaS", contacted: 1820, total: 2400, sent: 1820, opened: 946, replied: 255, hotLeads: 12, status: "Active" },
  { id: 2, name: "E-commerce Directors", audience: "E-commerce", contacted: 1200, total: 1800, sent: 1200, opened: 528, replied: 132, hotLeads: 8, status: "Active" },
  { id: 3, name: "FinTech CEOs", audience: "Finance", contacted: 3200, total: 3200, sent: 3200, opened: 1216, replied: 288, hotLeads: 14, status: "Completed" },
  { id: 4, name: "Agency Owners", audience: "Agency", contacted: 890, total: 1600, sent: 890, opened: 454, replied: 142, hotLeads: 4, status: "Active" },
  { id: 5, name: "Healthcare VP Sales", audience: "Healthcare", contacted: 0, total: 950, sent: 0, opened: 0, replied: 0, hotLeads: 0, status: "Draft" },
  { id: 6, name: "Real Estate Brokers", audience: "Real Estate", contacted: 640, total: 1100, sent: 640, opened: 320, replied: 0, hotLeads: 0, status: "Paused" },
];

const statusColors: Record<string, string> = {
  Active: "bg-success/10 text-success border-success/20",
  Paused: "bg-warning/10 text-warning border-warning/20",
  Completed: "bg-muted text-muted-foreground border-border",
  Draft: "bg-accent/10 text-accent border-accent/20",
};

const tabs = ["All", "Active", "Paused", "Completed", "Draft"];

export default function CampaignsPage() {
  const [activeTab, setActiveTab] = useState("All");
  const filtered = activeTab === "All" ? campaignsData : campaignsData.filter((c) => c.status === activeTab);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Campaigns</h1>
          <p className="text-muted-foreground text-sm">Manage and monitor your outreach campaigns.</p>
        </div>
        <Link to="/campaigns/new">
          <Button variant="gradient"><Plus className="w-4 h-4" /> New Campaign</Button>
        </Link>
      </div>

      <div className="flex gap-2 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              activeTab === tab ? "gradient-primary text-primary-foreground" : "bg-muted/50 text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filtered.map((c, i) => (
          <motion.div
            key={c.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass-card rounded-xl p-6 hover:border-primary/30 transition-all group"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-foreground">{c.name}</h3>
                <span className="text-xs text-accent font-medium">{c.audience}</span>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColors[c.status]}`}>
                {c.status}
              </span>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>{c.contacted.toLocaleString()} / {c.total.toLocaleString()} contacted</span>
                <span>{Math.round((c.contacted / c.total) * 100)}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-muted">
                <div className="h-full rounded-full gradient-primary transition-all" style={{ width: `${(c.contacted / c.total) * 100}%` }} />
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2 mb-4 text-center">
              {[
                { label: "Sent", value: c.sent },
                { label: "Opened", value: c.opened },
                { label: "Replied", value: c.replied },
                { label: "Hot", value: c.hotLeads },
              ].map((s) => (
                <div key={s.label}>
                  <div className="text-sm font-semibold text-foreground">{s.value.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground">{s.label}</div>
                </div>
              ))}
            </div>

            <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button variant="ghost" size="sm"><Eye className="w-3.5 h-3.5" /></Button>
              <Button variant="ghost" size="sm">
                {c.status === "Active" ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              </Button>
              <Button variant="ghost" size="sm"><Copy className="w-3.5 h-3.5" /></Button>
              <Button variant="ghost" size="sm" className="text-destructive"><Trash2 className="w-3.5 h-3.5" /></Button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
