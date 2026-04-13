import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
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
  ChevronDown,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { toast } from "@/hooks/use-toast";
import { leadsAPI } from "@/services/api";

interface GeneratedEmail {
  subject: string;
  body: string;
  personalization_score: number;
  generated_at: string;
  email_type: "cold" | "followup1" | "followup2" | "linkedin";
}

interface LeadScore {
  total_score: number;
  grade: "A" | "B" | "C" | "D";
  breakdown: {
    service_fit?: number;
    intent_score?: number;
    tech_stack?: number;
    contact_availability?: number;
    size_fit?: number;
  };
  is_hot_lead: boolean;
  recommended_action: string;
}

interface LeadEnrichment {
  tech_stack: string[];
  uses_microsoft_stack: boolean;
  ecommerce_platform?: string | null;
  decision_maker?: Record<string, any> | null;
  recent_signals: string[];
  signal_strength: number;
}

interface LeadDetail {
  id: string;
  name?: string;
  company?: string;
  email: string;
  phone?: string;
  job_title?: string;
  industry?: string;
  status?: string;
  created_at?: string;
  company_fit_score?: number;
  signal_score?: number;
  reason?: string[];
  signal_keywords?: string[];
  score?: LeadScore;
  enrichment?: LeadEnrichment;
  emails?: GeneratedEmail[];
  raw_data?: {
    company_summary?: string;
    snippet?: string;
    source_url?: string;
    location?: string;
    detected_location?: string;
    discovery_signals?: string[];
    final_reason?: string[];
  };
  ai_generated_message?: string;
  ai_notes?: string;
}

const BREAKDOWN_MAX: Record<string, number> = {
  service_fit: 30,
  intent_score: 25,
  tech_stack: 20,
  contact_availability: 15,
  size_fit: 10,
};

const BREAKDOWN_LABELS: Record<string, string> = {
  service_fit: "Service Fit",
  intent_score: "Intent",
  tech_stack: "Tech Stack",
  contact_availability: "Contact",
  size_fit: "Size Fit",
};

const GRADE_STYLES: Record<string, string> = {
  A: "bg-[#2d6a4f] text-white",
  B: "bg-[#0077b6] text-white",
  C: "bg-[#e76f51] text-white",
  D: "bg-[#6c757d] text-white",
};

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

  const [isGeneratingEmail, setIsGeneratingEmail] = useState(false);
  const [generatedEmail, setGeneratedEmail] = useState<GeneratedEmail | null>(null);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailHistoryOpen, setEmailHistoryOpen] = useState(false);

  const fetchLead = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await leadsAPI.get(id);
      setLead(data as LeadDetail);
      setError(null);
    } catch (err: any) {
      console.error("Failed to load lead details", err);
      setError(err.message || "Unable to load lead details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!id) {
      setError("Lead ID is missing from the URL.");
      setLoading(false);
      return;
    }

    fetchLead();
  }, [id]);

  const scoreCard = useMemo(() => {
    if (lead?.score) return lead.score;

    const fallbackScore = Number((lead as any)?.raw_data?.final_score_100 || 0);
    const grade = fallbackScore >= 70 ? "A" : fallbackScore >= 50 ? "B" : fallbackScore >= 30 ? "C" : "D";
    return {
      total_score: fallbackScore,
      grade,
      breakdown: {},
      is_hot_lead: fallbackScore >= 70,
      recommended_action: fallbackScore >= 70 ? "contact_immediately" : fallbackScore >= 50 ? "add_to_sequence" : fallbackScore >= 30 ? "nurture" : "skip",
    } as LeadScore;
  }, [lead]);

  const handleGenerateColdEmail = async () => {
    if (!id) return;
    setIsGeneratingEmail(true);
    try {
      const email = (await leadsAPI.generateEmail(id)) as GeneratedEmail;
      setGeneratedEmail(email);
      setEmailModalOpen(true);
      toast({ title: "Cold email generated" });
      await fetchLead();
    } catch (err: any) {
      console.error(err);
      toast({
        title: "Email generation failed",
        description: err.message || "Please try again.",
      });
    } finally {
      setIsGeneratingEmail(false);
    }
  };

  const copyEmailContent = () => {
    if (!generatedEmail) return;
    const text = `Subject: ${generatedEmail.subject}\n\n${generatedEmail.body}`;
    navigator.clipboard.writeText(text);
    toast({ title: "Email copied" });
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
  const location = lead.raw_data?.detected_location || lead.raw_data?.location || "Unknown location";
  const industry = lead.industry || "Unknown industry";
  const website = lead.raw_data?.source_url || "";
  const summary = lead.raw_data?.company_summary || lead.raw_data?.snippet || lead.job_title || "No summary available.";
  const signals = lead.signal_keywords?.length ? lead.signal_keywords : lead.raw_data?.discovery_signals || [];
  const reasonList = lead.reason?.length ? lead.reason : lead.raw_data?.final_reason || ["Qualified by scoring and signal analysis."];

  const outreachMessage = `Hi ${lead.name ? lead.name.split(" ")[0] : "there"},\n\nI noticed ${companyName} is showing active demand in ${industry}. We support teams like yours with targeted execution and faster delivery across product and engineering workflows.\n\nOpen to a short 15-minute conversation this week?\n\nBest,\nYour Team`;

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
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${GRADE_STYLES[scoreCard.grade] || GRADE_STYLES.D}`}>
                    {scoreCard.grade} - {scoreCard.total_score}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{summary}</p>
                <div className="flex flex-wrap gap-4 mt-3 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {location}</span>
                  <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5" /> {industry}</span>
                  {lead.job_title && <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {lead.job_title}</span>}
                  {website && <span className="flex items-center gap-1"><Globe className="w-3.5 h-3.5" /> {website}</span>}
                  {lead.created_at && <span>{new Date(lead.created_at).toLocaleDateString()}</span>}
                </div>
              </div>
              <div className="text-center shrink-0">
                <div className="text-4xl font-display font-bold text-primary">{scoreCard.total_score}</div>
                <div className="text-xs text-muted-foreground">Total Score</div>
                <div className="flex gap-2 mt-3">
                  <Button
                    size="sm"
                    className="gap-1"
                    onClick={() => {
                      if (lead.email) {
                        navigator.clipboard.writeText(lead.email);
                        toast({ title: "Email copied" });
                      }
                    }}
                  >
                    <Copy className="w-3 h-3" /> Email
                  </Button>
                  <Button variant="outline" size="sm" className="gap-1" onClick={() => website && window.open(website, "_blank")}>
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
                <CardTitle className="text-base font-display">Score Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.keys(BREAKDOWN_MAX).map((key) => {
                  const max = BREAKDOWN_MAX[key];
                  const value = Number((scoreCard.breakdown as any)?.[key] || 0);
                  const width = Math.max(0, Math.min(100, Math.round((value / max) * 100)));
                  return (
                    <div key={key}>
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-muted-foreground">{BREAKDOWN_LABELS[key]}</span>
                        <span className="font-medium text-foreground">{value}/{max}</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-primary rounded-full" style={{ width: `${width}%` }} />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </motion.div>

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
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <CardTitle className="text-base font-display flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-primary" /> Suggested Outreach
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(outreachMessage);
                        toast({ title: "Message copied" });
                      }}
                      className="gap-1"
                    >
                      <Copy className="w-3 h-3" /> Copy
                    </Button>
                    <Button size="sm" onClick={handleGenerateColdEmail} disabled={isGeneratingEmail} className="gap-1">
                      {isGeneratingEmail ? <Loader2 className="w-3 h-3 animate-spin" /> : <Mail className="w-3 h-3" />} Generate Cold Email
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-xl bg-muted/30 border border-border/50 text-sm text-foreground whitespace-pre-line leading-relaxed">
                  {outreachMessage}
                </div>

                <Collapsible open={emailHistoryOpen} onOpenChange={setEmailHistoryOpen}>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" className="mt-3 w-full justify-between">
                      Email History ({lead.emails?.length || 0})
                      <ChevronDown className={`w-4 h-4 transition-transform ${emailHistoryOpen ? "rotate-180" : ""}`} />
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <div className="mt-2 space-y-2">
                      {(lead.emails || []).length === 0 ? (
                        <p className="text-sm text-muted-foreground">No generated emails yet.</p>
                      ) : (
                        (lead.emails || []).map((email, index) => (
                          <div key={`${email.generated_at}-${index}`} className="rounded-lg border border-border/50 p-3">
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <div className="text-sm font-medium">{email.subject}</div>
                              <span className="text-xs rounded-full bg-muted px-2 py-0.5">{email.email_type}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mb-1">
                              {email.generated_at ? new Date(email.generated_at).toLocaleString() : ""}
                            </div>
                            <p className="text-sm text-foreground whitespace-pre-line">{email.body}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </CollapsibleContent>
                </Collapsible>
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
                <Button className="w-full gap-2 justify-start" variant="outline" onClick={() => website && window.open(website, "_blank")}>
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
                <Button size="sm" className="mt-2" onClick={() => toast({ title: "Notes saved" })}>Save Notes</Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      <Dialog open={emailModalOpen} onOpenChange={setEmailModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Generated Cold Email</DialogTitle>
          </DialogHeader>

          {generatedEmail ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Subject</p>
                <div className="rounded-md border border-border/60 px-3 py-2 text-sm font-medium">{generatedEmail.subject}</div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Body</p>
                <div className="rounded-md border border-border/60 px-3 py-2 text-sm whitespace-pre-line">{generatedEmail.body}</div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted-foreground">
                <span>Personalization score: {generatedEmail.personalization_score}/10</span>
                <Button size="sm" onClick={copyEmailContent} className="gap-1">
                  <Copy className="w-3 h-3" /> Copy to clipboard
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No generated email available.</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
