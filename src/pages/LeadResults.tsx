import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Star, MapPin, ExternalLink, Mail, Check, Filter, ArrowUpDown, Copy, Eye, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { toast } from "@/hooks/use-toast";

const leads = [
  {
    id: 1, company: "TechVault Inc.", location: "San Francisco, CA", industry: "SaaS", size: "51-200",
    score: 9.4, priority: "High", status: "New",
    reasons: ["Hiring 5 backend engineers — matches your Node.js + Python expertise", "Recently raised Series B ($18M)", "Posted RFP for cloud migration project"],
    email: "john@techvault.io",
  },
  {
    id: 2, company: "NovaPay Systems", location: "New York, NY", industry: "FinTech", size: "200-1000",
    score: 8.9, priority: "High", status: "New",
    reasons: ["Expanding engineering team — 12 open roles", "Similar to your NovaPay past project", "Active LinkedIn posts about scaling challenges"],
    email: "hiring@novapay.com",
  },
  {
    id: 3, company: "GreenLeaf Health", location: "Austin, TX", industry: "Healthcare", size: "51-200",
    score: 8.2, priority: "High", status: "Contacted",
    reasons: ["Needs cloud migration — matches your GreenLeaf Health case study", "Budget approved for Q1 tech upgrade", "CTO active on LinkedIn"],
    email: "cto@greenleafhealth.com",
  },
  {
    id: 4, company: "DataStream AI", location: "London, UK", industry: "SaaS", size: "11-50",
    score: 7.8, priority: "Medium", status: "New",
    reasons: ["Posted RFP for ML pipeline development", "Using React + Python stack — direct match", "Growing 40% YoY"],
    email: "founders@datastream.ai",
  },
  {
    id: 5, company: "ShopFlow Commerce", location: "San Francisco, CA", industry: "E-commerce", size: "51-200",
    score: 7.5, priority: "Medium", status: "New",
    reasons: ["Hiring full-stack developers", "Mentioned need for mobile app in recent interview", "Previous client referral connection"],
    email: "dev@shopflow.com",
  },
  {
    id: 6, company: "EduBridge Platform", location: "Boston, MA", industry: "EdTech", size: "11-50",
    score: 7.1, priority: "Medium", status: "New",
    reasons: ["Looking for UI/UX redesign partner", "Seed stage — fast decision making", "Tech blog mentions scaling pain points"],
    email: "hello@edubridge.io",
  },
  {
    id: 7, company: "UrbanNest Realty", location: "Austin, TX", industry: "Real Estate", size: "11-50",
    score: 6.4, priority: "Low", status: "New",
    reasons: ["Wants to build property management platform", "Small budget but high growth potential"],
    email: "info@urbannest.com",
  },
  {
    id: 8, company: "CloudServe Solutions", location: "Seattle, WA", industry: "SaaS", size: "200-1000",
    score: 6.1, priority: "Low", status: "Contacted",
    reasons: ["DevOps consulting need identified", "Long sales cycle expected"],
    email: "partnerships@cloudserve.io",
  },
];

const priorityConfig: Record<string, { color: string; emoji: string }> = {
  High: { color: "bg-warning/10 text-warning border-warning/20", emoji: "🔥" },
  Medium: { color: "bg-accent/10 text-accent border-accent/20", emoji: "🟡" },
  Low: { color: "bg-muted text-muted-foreground border-border", emoji: "❄️" },
};

const statusConfig: Record<string, string> = {
  New: "bg-primary/10 text-primary",
  Contacted: "bg-success/10 text-success",
};

const container = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export default function LeadResults() {
  const [search, setSearch] = useState("");
  const [filterPriority, setFilterPriority] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");
  const [sortBy, setSortBy] = useState("score");

  let filtered = leads.filter((l) => {
    if (search && !l.company.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterPriority !== "All" && l.priority !== filterPriority) return false;
    if (filterStatus !== "All" && l.status !== filterStatus) return false;
    return true;
  });

  if (sortBy === "score") filtered.sort((a, b) => b.score - a.score);
  if (sortBy === "company") filtered.sort((a, b) => a.company.localeCompare(b.company));

  const highCount = leads.filter((l) => l.priority === "High").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Lead Results</h1>
          <p className="text-muted-foreground text-sm mt-1">{leads.length} leads found • {highCount} high priority</p>
        </div>
        <Link to="/search">
          <Button variant="outline" className="gap-2">
            <Search className="w-4 h-4" /> New Search
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card className="border-border/50 shadow-sm">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder="Search companies..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
            </div>
            <div className="flex gap-2 flex-wrap">
              {["All", "High", "Medium", "Low"].map((p) => (
                <button
                  key={p}
                  onClick={() => setFilterPriority(p)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                    filterPriority === p ? "bg-primary/10 text-primary border-primary/30" : "text-muted-foreground border-border/50 hover:border-primary/20"
                  }`}
                >
                  {p === "All" ? "All Priority" : `${priorityConfig[p]?.emoji} ${p}`}
                </button>
              ))}
              {["All", "New", "Contacted"].map((s) => (
                <button
                  key={s}
                  onClick={() => setFilterStatus(s)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                    filterStatus === s ? "bg-primary/10 text-primary border-primary/30" : "text-muted-foreground border-border/50 hover:border-primary/20"
                  }`}
                >
                  {s === "All" ? "All Status" : s}
                </button>
              ))}
              <button
                onClick={() => setSortBy(sortBy === "score" ? "company" : "score")}
                className="px-3 py-1.5 text-xs font-medium rounded-full border border-border/50 text-muted-foreground hover:border-primary/20 transition-all flex items-center gap-1"
              >
                <ArrowUpDown className="w-3 h-3" /> {sortBy === "score" ? "By Score" : "A-Z"}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leads Grid */}
      <motion.div variants={container} initial="hidden" animate="show" className="grid gap-4">
        {filtered.map((lead) => (
          <motion.div key={lead.id} variants={item}>
            <Card className={`border-border/50 shadow-sm hover:shadow-md transition-all hover:border-primary/20 ${lead.priority === "High" ? "ring-1 ring-warning/10" : ""}`}>
              <CardContent className="p-5">
                <div className="flex flex-col lg:flex-row gap-4">
                  {/* Left — Company Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-3">
                      <div className="w-11 h-11 rounded-xl bg-muted flex items-center justify-center text-sm font-bold text-foreground shrink-0">
                        {lead.company.charAt(0)}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Link to={`/lead/${lead.id}`} className="font-semibold text-foreground hover:text-primary transition-colors">
                            {lead.company}
                          </Link>
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${priorityConfig[lead.priority].color}`}>
                            {priorityConfig[lead.priority].emoji} {lead.priority}
                          </span>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusConfig[lead.status]}`}>
                            {lead.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {lead.location}</span>
                          <span>{lead.industry}</span>
                          <span>{lead.size} employees</span>
                        </div>
                      </div>
                    </div>

                    {/* Why this lead */}
                    <div className="mt-3 ml-14">
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">Why this lead?</p>
                      <ul className="space-y-1">
                        {lead.reasons.map((r, i) => (
                          <li key={i} className="text-sm text-foreground flex items-start gap-2">
                            <Check className="w-3.5 h-3.5 text-success mt-0.5 shrink-0" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Right — Score + Actions */}
                  <div className="flex lg:flex-col items-center lg:items-end gap-3 lg:gap-2 shrink-0 lg:min-w-[140px]">
                    <div className="text-center lg:text-right">
                      <div className="text-3xl font-display font-bold text-primary">{lead.score}</div>
                      <div className="text-xs text-muted-foreground">/ 10</div>
                    </div>
                    <div className="flex gap-2 flex-wrap justify-end">
                      <Link to={`/lead/${lead.id}`}>
                        <Button variant="outline" size="sm" className="gap-1 text-xs">
                          <Eye className="w-3 h-3" /> Details
                        </Button>
                      </Link>
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1 text-xs"
                        onClick={() => {
                          navigator.clipboard.writeText(lead.email);
                          toast({ title: "Email copied!", description: lead.email });
                        }}
                      >
                        <Copy className="w-3 h-3" /> Email
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1 text-xs text-success"
                        onClick={() => toast({ title: "Marked as contacted", description: lead.company })}
                      >
                        <Check className="w-3 h-3" /> Contacted
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
