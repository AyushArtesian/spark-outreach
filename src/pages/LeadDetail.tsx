import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  MapPin,
  Users,
  Globe,
  Mail,
  Linkedin,
  Check,
  Copy,
  Calendar,
  TrendingUp,
  Sparkles,
  MessageSquare,
  Building2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/hooks/use-toast";
import { leadsAPI } from "@/services/api";

interface LeadDetail {
  id: string;
  company?: string;
  email: string;
  phone?: string;
  job_title?: string;
  industry?: string;
  status?: string;
  created_at?: string;
  company_fit_score?: number;
  signal_score?: number;
  score?: number;
  reason?: string[];
  signal_keywords?: string[];
  raw_data?: {
    company_summary?: string;
    snippet?: string;
    source_url?: string;
    location?: string;
    discovery_signals?: string[];
    final_score?: number;
    final_reason?: string[];
  };
  ai_generated_message?: string;
  ai_notes?: string;
}

const placeholderTimeline = [
  { date: "Discovered", event: "Lead discovered and added to the pipeline", type: "system" },
  { date: "Score calculated", event: "Lead scored using company fit and growth signals", type: "system" },
];

export default function LeadDetail() {
  const { id } = useParams<{ id: string }>();
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("Add notes about this lead and save them when ready.");

  useEffect(() => {
    if (!id) {
      setError("Lead ID is missing from the URL.");
      setLoading(false);
      return;
    }

    const fetchLead = async () => {
      setLoading(true);
      try {
        const data = await leadsAPI.get(id);
        setLead(data as LeadDetail);
      } catch (err: any) {
        console.error("Failed to load lead details", err);
        setError(err.message || "Unable to load lead details.");
      } finally {
        setLoading(false);
      }
    };

    fetchLead();
  }, [id]);

  const getPriority = (fitScore?: number, signalScore?: number) => {
    const combined = (fitScore || 0) * 0.5 + (signalScore || 0) * 0.3;
    if (combined >= 0.75) return "High";
    if (combined >= 0.5) return "Medium";
    return "Low";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading lead details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <p className="text-red-500 font-semibold mb-4">{error}</p>
        <Link to="/leads">
          <Button variant="outline">Back to leads</Button>
        </Link>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <p className="text-muted-foreground">No lead details available.</p>
        <Link to="/leads">
          <Button variant="outline">Back to leads</Button>
        </Link>
      </div>
    );
  }

  const companyName = lead.company || "Unknown Company";
  const location = lead.raw_data?.location || "Unknown location";
  const industry = lead.industry || "Unknown industry";
  const website = lead.raw_data?.source_url || "";
  const summary = lead.raw_data?.company_summary || lead.raw_data?.snippet || lead.job_title || "No summary available.";
  const score = lead.score ?? Math.round(((lead.company_fit_score || 0) * 0.5 + (lead.signal_score || 0) * 0.3) * 10 * 10) / 10;
  const priority = getPriority(lead.company_fit_score, lead.signal_score);
  const signals = lead.signal_keywords?.length ? lead.signal_keywords : lead.raw_data?.discovery_signals || [];
  const reasonList = lead.reason?.length ? lead.reason : lead.raw_data?.final_reason || ["Qualified by company profile fit and signals."];
  const outreachMessage = `Hi ${lead.name ? lead.name.split(" ")[0] : "there"},\n\nI noticed ${companyName} is actively moving in ${industry} and has a strong growth signal profile. We specialize in supporting companies like yours with dedicated engineering teams and product engineering for ${industry}.\n\nWould you be open to a short call this week to explore how we can help accelerate your next phase?\n\nBest,\nYour Team`;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <Link to="/leads" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to leads
      </Link>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="border-border/50 shadow-sm">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center text-2xl font-bold text-foreground shrink-0">
                {companyName.charAt(0) || "?"}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-2xl font-display font-bold text-foreground">{companyName}</h1>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full border bg-warning/10 text-warning border-warning/20">
                    🔥 {priority} Priority
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{summary}</p>
                <div className="flex flex-wrap gap-4 mt-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {location}</span>
                  <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" /> {industry}</span>
                  {lead.job_title && <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {lead.job_title}</span>}
                  {website && (
                    <span className="flex items-center gap-1"><Globe className="w-3.5 h-3.5" /> {website}</span>
                  )}
                  {lead.created_at && <span>{new Date(lead.created_at).toLocaleDateString()}</span>}
                </div>
              </div>
              <div className="text-center shrink-0">
                <div className="text-4xl font-display font-bold text-primary">{score?.toFixed ? score.toFixed(1) : score}</div>
                <div className="text-xs text-muted-foreground">Lead Score</div>
                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    className="gap-1"
                    onClick={() => {
                      if (lead.email) {
                        navigator.clipboard.writeText(lead.email);
                        toast({ title: "Email copied!" });
                      }
                    }}
                  >
                    <Copy className="w-3 h-3" /> Email
                  </Button>
                  <Button variant="outline" size="sm" className="gap-1" onClick={() => website && window.open(website, "_blank") }>
                    <Linkedin className="w-3 h-3" /> Website
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Detected Signals</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {signals.length > 0 ? (
                  signals.map((signal, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-muted/20 hover:bg-muted/40 transition-colors">
                      <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                        <TrendingUp className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-foreground">{signal}</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No strong signals detected yet.</p>
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <Card className="border-primary/20 bg-primary/5 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary" /> Why This Lead Matches You
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {reasonList.map((reason, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-foreground">
                      <Check className="w-4 h-4 text-success mt-0.5 shrink-0" />
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-display flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-primary" /> Suggested Outreach
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      navigator.clipboard.writeText(outreachMessage);
                      toast({ title: "Message copied!" });
                    }}
                    className="gap-1"
                  >
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

        <div className="space-y-6">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full gap-2 justify-start" variant="default" onClick={() => navigator.clipboard.writeText(lead.email)}>
                  <Mail className="w-4 h-4" /> Send Email
                </Button>
                <Button className="w-full gap-2 justify-start" variant="outline" onClick={() => website && window.open(website, "_blank") }>
                  <Linkedin className="w-4 h-4" /> Visit Website
                </Button>
                <Button className="w-full gap-2 justify-start" variant="outline">
                  <Calendar className="w-4 h-4" /> Book Meeting
                </Button>
                <Button className="w-full gap-2 justify-start text-success" variant="ghost" onClick={() => toast({ title: "Marked as contacted" })}>
                  <Check className="w-4 h-4" /> Mark as Contacted
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
            <Card className="border-border/50 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base font-display">Activity Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {placeholderTimeline.map((t, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-2 h-2 rounded-full mt-1.5 ${t.type === "signal" ? "bg-warning" : "bg-primary"}`} />
                        {i < placeholderTimeline.length - 1 && <div className="w-px flex-1 bg-border mt-1" />}
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
