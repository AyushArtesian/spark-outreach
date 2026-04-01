import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Filter, Download, Mail, Linkedin, ExternalLink, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const prospects = [
  { id: 1, name: "Sarah Chen", title: "CEO", company: "TechFlow", email: "sarah@techflow.io", score: "hot", status: "Replied", lastActivity: "2 hrs ago", campaign: "SaaS Founders Q4", avatar: "SC" },
  { id: 2, name: "Mike Johnson", title: "VP Sales", company: "CloudStack", email: "mike@cloudstack.com", score: "hot", status: "Meeting Booked", lastActivity: "4 hrs ago", campaign: "SaaS Founders Q4", avatar: "MJ" },
  { id: 3, name: "Lisa Park", title: "Founder", company: "DataLens", email: "lisa@datalens.ai", score: "warm", status: "Opened", lastActivity: "1 day ago", campaign: "E-commerce Directors", avatar: "LP" },
  { id: 4, name: "James Wright", title: "CTO", company: "FinAPI", email: "james@finapi.co", score: "warm", status: "Emailed", lastActivity: "2 days ago", campaign: "FinTech CEOs", avatar: "JW" },
  { id: 5, name: "Emma Davis", title: "Marketing Dir", company: "GrowthLab", email: "emma@growthlab.io", score: "cold", status: "Not Contacted", lastActivity: "—", campaign: "Agency Owners", avatar: "ED" },
  { id: 6, name: "Ryan Mitchell", title: "CEO", company: "BrightScale", email: "ryan@brightscale.com", score: "hot", status: "Replied", lastActivity: "5 hrs ago", campaign: "SaaS Founders Q4", avatar: "RM" },
  { id: 7, name: "Alex Turner", title: "Founder", company: "NovaPay", email: "alex@novapay.com", score: "warm", status: "Opened", lastActivity: "12 hrs ago", campaign: "FinTech CEOs", avatar: "AT" },
  { id: 8, name: "Nina Patel", title: "VP Marketing", company: "StyleHub", email: "nina@stylehub.co", score: "cold", status: "Emailed", lastActivity: "3 days ago", campaign: "E-commerce Directors", avatar: "NP" },
];

const scoreStyles: Record<string, string> = {
  hot: "bg-destructive/10 text-destructive",
  warm: "bg-warning/10 text-warning",
  cold: "bg-accent/10 text-accent",
};

const scoreLabels: Record<string, string> = { hot: "🔥 Hot", warm: "🟡 Warm", cold: "❄️ Cold" };

const statusStyles: Record<string, string> = {
  "Not Contacted": "bg-muted text-muted-foreground",
  Emailed: "bg-primary/10 text-primary",
  Opened: "bg-accent/10 text-accent",
  Replied: "bg-success/10 text-success",
  "Meeting Booked": "bg-success/20 text-success",
};

export default function ProspectsPage() {
  const [selected, setSelected] = useState<number | null>(null);
  const prospect = prospects.find((p) => p.id === selected);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Prospects</h1>
          <p className="text-muted-foreground text-sm">{prospects.length.toLocaleString()} total prospects across all campaigns</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm"><Filter className="w-4 h-4" /> Filters</Button>
          <Button variant="outline" size="sm"><Download className="w-4 h-4" /> Export</Button>
        </div>
      </div>

      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input placeholder="Search by name, company, email..." className="w-full h-10 pl-9 pr-4 rounded-lg bg-muted/50 border border-border text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary" />
      </div>

      <div className="glass-card rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-left p-4 text-muted-foreground font-medium">Prospect</th>
                <th className="text-left p-4 text-muted-foreground font-medium hidden md:table-cell">Company</th>
                <th className="text-left p-4 text-muted-foreground font-medium hidden lg:table-cell">Email</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Score</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Status</th>
                <th className="text-left p-4 text-muted-foreground font-medium hidden lg:table-cell">Campaign</th>
                <th className="text-left p-4 text-muted-foreground font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {prospects.map((p) => (
                <tr key={p.id} className="border-b border-border/30 hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => setSelected(p.id)}>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-xs font-bold text-primary-foreground shrink-0">{p.avatar}</div>
                      <div>
                        <div className="font-medium text-foreground">{p.name}</div>
                        <div className="text-xs text-muted-foreground">{p.title}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-foreground hidden md:table-cell">{p.company}</td>
                  <td className="p-4 text-muted-foreground hidden lg:table-cell">{p.email}</td>
                  <td className="p-4"><span className={`px-2 py-1 rounded-full text-xs font-medium ${scoreStyles[p.score]}`}>{scoreLabels[p.score]}</span></td>
                  <td className="p-4"><span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[p.status]}`}>{p.status}</span></td>
                  <td className="p-4 text-xs text-muted-foreground hidden lg:table-cell">{p.campaign}</td>
                  <td className="p-4">
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" className="w-7 h-7"><Mail className="w-3.5 h-3.5" /></Button>
                      <Button variant="ghost" size="icon" className="w-7 h-7"><Linkedin className="w-3.5 h-3.5" /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over */}
      {prospect && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={() => setSelected(null)} />
          <motion.div initial={{ x: "100%" }} animate={{ x: 0 }} className="relative w-full max-w-md bg-card border-l border-border overflow-y-auto">
            <div className="p-6 space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="font-display font-semibold text-foreground">Prospect Profile</h2>
                <Button variant="ghost" size="icon" onClick={() => setSelected(null)}><X className="w-4 h-4" /></Button>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full gradient-primary flex items-center justify-center text-lg font-bold text-primary-foreground">{prospect.avatar}</div>
                <div>
                  <div className="font-semibold text-lg text-foreground">{prospect.name}</div>
                  <div className="text-sm text-muted-foreground">{prospect.title} at {prospect.company}</div>
                </div>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground"><Mail className="w-4 h-4" /> {prospect.email}</div>
                <div className="flex items-center gap-2 text-muted-foreground"><Linkedin className="w-4 h-4" /> LinkedIn Profile</div>
              </div>
              <div>
                <h3 className="font-medium text-foreground mb-3 text-sm">Activity Timeline</h3>
                <div className="space-y-3 border-l-2 border-border pl-4">
                  {[
                    { text: "Email sent", date: "Oct 12, 9:04 AM", color: "bg-primary" },
                    { text: "Email opened (3x)", date: "Oct 12, 2:31 PM", color: "bg-accent" },
                    { text: "Follow-up sent", date: "Oct 15, 9:00 AM", color: "bg-primary" },
                    { text: "Replied", date: "Oct 16, 11:22 AM", color: "bg-success" },
                  ].map((a, i) => (
                    <div key={i} className="relative">
                      <div className={`absolute -left-[21px] w-2.5 h-2.5 rounded-full ${a.color}`} />
                      <p className="text-sm text-foreground">{a.text}</p>
                      <p className="text-xs text-muted-foreground">{a.date}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg bg-accent/5 border border-accent/20 p-4">
                <p className="text-sm font-medium text-foreground mb-1">AI Score Explanation</p>
                <p className="text-xs text-muted-foreground">Opened 3 times, replied within 24hrs — High intent</p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="gradient" size="sm"><Mail className="w-4 h-4" /> Send Email</Button>
                <Button variant="outline" size="sm"><Linkedin className="w-4 h-4" /> Send LinkedIn</Button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
