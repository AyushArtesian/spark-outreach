import { motion } from "framer-motion";
import { ArrowLeft, MapPin, Users, Globe, Mail, Linkedin, Check, Copy, Calendar, TrendingUp, Sparkles, MessageSquare, Star, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Link } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { useState } from "react";

const lead = {
  company: "TechVault Inc.",
  location: "San Francisco, CA",
  industry: "SaaS",
  size: "51-200 employees",
  website: "techvault.io",
  score: 9.4,
  priority: "High",
  founded: "2019",
  revenue: "$12M ARR",
  email: "john@techvault.io",
  linkedin: "linkedin.com/company/techvault",
  description: "TechVault is a rapidly growing SaaS platform providing secure data storage and analytics for mid-market enterprises. They've recently expanded into the healthcare vertical and are actively building out their engineering team.",
};

const signals = [
  { icon: TrendingUp, label: "Series B Funding", detail: "Raised $18M in October 2024 — actively investing in product development", type: "funding" },
  { icon: Users, label: "Hiring Engineers", detail: "5 open positions: Backend (Node.js), ML Engineer, DevOps — direct match with your stack", type: "hiring" },
  { icon: Globe, label: "Market Expansion", detail: "Expanding from US to UK market — posted about scaling challenges on LinkedIn", type: "growth" },
  { icon: Building2, label: "Cloud Migration Need", detail: "CTO mentioned AWS migration plans in recent podcast interview", type: "need" },
  { icon: Star, label: "Past Project Match", detail: "Similar to your NovaPay fraud detection project — 92% relevance score", type: "match" },
];

const matchExplanation = [
  "Your React + Node.js + Python stack is a direct match for their 5 open engineering roles",
  "Your GreenLeaf Health cloud migration case study demonstrates exactly the expertise they need",
  "Your experience in FinTech (NovaPay) translates well to their data security focus",
  "Company size (51-200) is in your sweet spot for dedicated team engagements",
  "Recent funding means budget is available — high likelihood of near-term decision",
];

const timeline = [
  { date: "Oct 28, 2024", event: "Lead discovered via market scan", type: "system" },
  { date: "Oct 29, 2024", event: "AI scored lead at 9.4/10", type: "system" },
  { date: "Nov 1, 2024", event: "Funding signal detected — Series B raised", type: "signal" },
  { date: "Nov 3, 2024", event: "5 new engineering job postings detected", type: "signal" },
];

const outreachMessage = `Hi John,

I noticed TechVault recently raised your Series B — congratulations! As you scale your engineering team (saw the Node.js and ML roles), I wanted to share how we helped NovaPay build their real-time fraud detection system with a similar stack.

We specialize in dedicated engineering teams for fast-growing SaaS companies, and our cloud migration work with GreenLeaf Health might be relevant as you explore AWS.

Would you be open to a quick 15-minute call this week to explore if there's a fit?

Best,
John Doe
Acme Software Solutions`;

export default function LeadDetail() {
  const [notes, setNotes] = useState("Looks like a strong fit. Reach out to CTO first via LinkedIn, then follow up with email.");

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back */}
      <Link to="/leads" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to leads
      </Link>

      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="border-border/50 shadow-sm">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center text-2xl font-bold text-foreground shrink-0">
                T
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-2xl font-display font-bold text-foreground">{lead.company}</h1>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full border bg-warning/10 text-warning border-warning/20">
                    🔥 {lead.priority} Priority
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{lead.description}</p>
                <div className="flex flex-wrap gap-4 mt-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {lead.location}</span>
                  <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" /> {lead.industry}</span>
                  <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {lead.size}</span>
                  <span className="flex items-center gap-1"><Globe className="w-3.5 h-3.5" /> {lead.website}</span>
                  <span>Founded {lead.founded}</span>
                  <span className="font-medium text-foreground">{lead.revenue}</span>
                </div>
              </div>
              <div className="text-center shrink-0">
                <div className="text-4xl font-display font-bold text-primary">{lead.score}</div>
                <div className="text-xs text-muted-foreground">Lead Score</div>
                <div className="flex gap-2 mt-3">
                  <Button size="sm" className="gap-1" onClick={() => { navigator.clipboard.writeText(lead.email); toast({ title: "Email copied!" }); }}>
                    <Copy className="w-3 h-3" /> Email
                  </Button>
                  <Button variant="outline" size="sm" className="gap-1">
                    <Linkedin className="w-3 h-3" /> LinkedIn
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Signals */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Detected Signals</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {signals.map((s, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-muted/20 hover:bg-muted/40 transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                      <s.icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-foreground">{s.label}</div>
                      <div className="text-xs text-muted-foreground mt-0.5">{s.detail}</div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Match Explanation */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <Card className="border-primary/20 bg-primary/5 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" /> Why This Lead Matches You
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {matchExplanation.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                      <Check className="w-4 h-4 text-success mt-0.5 shrink-0" />
                      <span>{m}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>

          {/* Outreach Message */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-display flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-primary" /> Suggested Outreach
                  </CardTitle>
                  <Button variant="outline" size="sm" onClick={() => { navigator.clipboard.writeText(outreachMessage); toast({ title: "Message copied!" }); }} className="gap-1">
                    <Copy className="w-3 h-3" /> Copy
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-xl bg-muted/30 border border-border/50 text-sm text-foreground whitespace-pre-line leading-relaxed">
                  {outreachMessage}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Actions */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full gap-2 justify-start" variant="default">
                  <Mail className="w-4 h-4" /> Send Email
                </Button>
                <Button className="w-full gap-2 justify-start" variant="outline">
                  <Linkedin className="w-4 h-4" /> Connect on LinkedIn
                </Button>
                <Button className="w-full gap-2 justify-start" variant="outline">
                  <Calendar className="w-4 h-4" /> Book Meeting
                </Button>
                <Button className="w-full gap-2 justify-start text-success" variant="ghost" onClick={() => toast({ title: "Marked as won!" })}>
                  <Check className="w-4 h-4" /> Mark as Won
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Timeline */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Activity Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {timeline.map((t, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-2 h-2 rounded-full mt-1.5 ${t.type === "signal" ? "bg-warning" : "bg-primary"}`} />
                        {i < timeline.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
                      </div>
                      <div>
                        <p className="text-sm text-foreground">{t.event}</p>
                        <p className="text-xs text-muted-foreground">{t.date}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Notes */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Notes</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Add notes about this lead..." />
                <Button size="sm" className="mt-2" onClick={() => toast({ title: "Notes saved!" })}>Save Notes</Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
