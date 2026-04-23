import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, ArrowUpDown, Copy, Eye, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Link } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { leadsAPI } from "@/services/api";
import LeadActionPanel, { SmartLeadAction } from "@/components/dashboard/LeadActionPanel";
import { logActivityEvent } from "@/lib/activityTimeline";

interface LeadScore {
  total_score: number;
  grade: "A" | "B" | "C" | "D";
  breakdown: {
    service_fit?: number;
    intent_score?: number;
    tech_stack?: number;
    contact_availability?: number;
    size_fit?: number;
    company_fit?: number;
    buyer_signal_strength?: number;
    accessibility?: number;
  };
  is_hot_lead: boolean;
  recommended_action: string;
}

interface Lead {
  id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  job_title?: string;
  industry?: string;
  source_url?: string;
  raw_data?: Record<string, any>;
  score?: LeadScore;
  company_fit_score: number;
  signal_score: number;
  signal_keywords: string[];
  status: string;
  created_at: string;
}

interface SavedLeadView {
  id: string;
  name: string;
  isDefault?: boolean;
  filters: {
    activeTab: string;
    search: string;
    filterPriority: string;
    filterStatus: string;
    sortBy: string;
  };
}

const SAVED_VIEWS_KEY = "all_leads_saved_views_v1";
const DEFAULT_VIEW_KEY = "all_leads_default_view_id_v1";

const GRADE_STYLES: Record<string, string> = {
  A: "bg-[#2d6a4f] text-white",
  B: "bg-[#0077b6] text-white",
  C: "bg-[#e76f51] text-white",
  D: "bg-[#6c757d] text-white",
};

const LEGACY_BREAKDOWN_ROWS = [
  { key: "service_fit", label: "Service Fit", max: 30 },
  { key: "intent_score", label: "Intent", max: 25 },
  { key: "tech_stack", label: "Tech Stack", max: 20 },
  { key: "contact_availability", label: "Contact", max: 15 },
  { key: "size_fit", label: "Size Fit", max: 10 },
];

const MODERN_BREAKDOWN_ROWS = [
  { key: "company_fit", label: "Company Fit", max: 40 },
  { key: "buyer_signal_strength", label: "Buyer Signals", max: 40 },
  { key: "accessibility", label: "Accessibility", max: 20 },
];

const getBreakdownRows = (breakdown?: LeadScore["breakdown"]) => {
  const card = breakdown || {};
  const hasModern = MODERN_BREAKDOWN_ROWS.some((row) => Object.prototype.hasOwnProperty.call(card, row.key));
  if (hasModern) return MODERN_BREAKDOWN_ROWS;
  return LEGACY_BREAKDOWN_ROWS;
};

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

export default function AllLeads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [hotLeads, setHotLeads] = useState<Lead[]>([]);
  const [activeTab, setActiveTab] = useState("all");
  const [expandedScore, setExpandedScore] = useState<Record<string, boolean>>({});
  const [search, setSearch] = useState("");
  const [filterPriority, setFilterPriority] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");
  const [sortBy, setSortBy] = useState("score");
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [savedViews, setSavedViews] = useState<SavedLeadView[]>([]);
  const [viewName, setViewName] = useState("");
  const [activeViewId, setActiveViewId] = useState<string | null>(null);
  const [defaultViewId, setDefaultViewId] = useState<string | null>(null);
  const [defaultApplied, setDefaultApplied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [skip, setSkip] = useState(0);
  const pageSize = 50;
  const hasMore = leads.length % pageSize === 0 && leads.length > 0;

  const normalizeLead = (lead: any): Lead => {
    const scoreCard = lead?.score || lead?.raw_data?.score_card || null;
    const hasStructuredScore = scoreCard && typeof scoreCard === "object";

    const legacyNormalized = Number(lead?.raw_data?.final_score ?? 0);
    const legacyScore100 = Number(lead?.raw_data?.final_score_100 ?? Math.round(legacyNormalized * 100));

    const score: LeadScore = hasStructuredScore
      ? {
          total_score: Number(scoreCard.total_score ?? 0),
          grade: (scoreCard.grade || "D") as "A" | "B" | "C" | "D",
          breakdown: scoreCard.breakdown || {},
          is_hot_lead: Boolean(scoreCard.is_hot_lead),
          recommended_action: String(scoreCard.recommended_action || "skip"),
        }
      : {
          total_score: legacyScore100,
          grade: legacyScore100 >= 80 ? "A" : legacyScore100 >= 60 ? "B" : legacyScore100 >= 40 ? "C" : "D",
          breakdown: {},
          is_hot_lead: legacyScore100 >= 80,
          recommended_action: legacyScore100 >= 80 ? "contact_immediately" : legacyScore100 >= 60 ? "add_to_sequence" : legacyScore100 >= 40 ? "nurture" : "skip",
        };

    return {
      ...lead,
      score,
      company_fit_score: lead.company_fit_score ?? 0,
      signal_score: lead.signal_score ?? 0,
      signal_keywords: lead.signal_keywords ?? [],
    };
  };

  const fetchLeads = async (skipVal: number = 0) => {
    try {
      const isLoadMore = skipVal > 0;
      if (isLoadMore) setLoadingMore(true);
      
      const data = await leadsAPI.all(skipVal, pageSize);
      const formatted = data.map((lead: any) => normalizeLead(lead));
      
      if (isLoadMore) {
        setLeads([...leads, ...formatted]);
      } else {
        setLeads(formatted);
      }
    } catch (error) {
      console.error(error);
      toast({
        title: "Unable to load leads",
        description: "Please refresh the page or try again later.",
      });
    } finally {
      if (skipVal > 0) setLoadingMore(false);
      else setLoading(false);
    }
  };

  const fetchHotLeads = async () => {
    try {
      const data = await leadsAPI.hot(200);
      const formatted = data.map((lead: any) => normalizeLead(lead));
      setHotLeads(formatted);
    } catch (error) {
      console.error(error);
      toast({
        title: "Unable to load hot leads",
        description: "Please try again shortly.",
      });
    }
  };

  useEffect(() => {
    fetchLeads(0);
    fetchHotLeads();

    try {
      const raw = localStorage.getItem(SAVED_VIEWS_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      if (Array.isArray(parsed)) {
        setSavedViews(parsed);
      }
      const savedDefaultId = localStorage.getItem(DEFAULT_VIEW_KEY);
      if (savedDefaultId) {
        setDefaultViewId(savedDefaultId);
      }
    } catch {
      setSavedViews([]);
      setDefaultViewId(null);
    }
  }, []);

  useEffect(() => {
    const matched = savedViews.find((view) => {
      const f = view.filters;
      return (
        f.activeTab === activeTab &&
        f.search === search &&
        f.filterPriority === filterPriority &&
        f.filterStatus === filterStatus &&
        f.sortBy === sortBy
      );
    });
    setActiveViewId(matched?.id || null);
  }, [activeTab, filterPriority, filterStatus, savedViews, search, sortBy]);

  const handleLoadMore = () => {
    const nextSkip = skip + pageSize;
    setSkip(nextSkip);
    fetchLeads(nextSkip);
  };

  const calculatePriority = (fitScore: number, signalScore: number): string => {
    const combinedScore = fitScore * 0.5 + signalScore * 0.3;
    if (combinedScore >= 0.75) return "High";
    if (combinedScore >= 0.5) return "Medium";
    return "Low";
  };

  const baseLeads = activeTab === "hot" ? hotLeads : leads;

  const filtered = baseLeads.filter((lead) => {
    if (search && !lead.company?.toLowerCase().includes(search.toLowerCase())) return false;
    const priority = lead.score?.grade === "A" ? "High" : lead.score?.grade === "B" ? "Medium" : lead.score?.grade === "C" ? "Low" : "Low";
    if (filterPriority !== "All" && priority !== filterPriority) return false;
    if (filterStatus !== "All" && lead.status !== filterStatus) return false;
    return true;
  });

  if (sortBy === "score") {
    filtered.sort((a, b) => {
      const scoreA = Number(a.score?.total_score || 0);
      const scoreB = Number(b.score?.total_score || 0);
      return scoreB - scoreA;
    });
  }

  if (sortBy === "company") {
    filtered.sort((a, b) => (a.company || "").localeCompare(b.company || ""));
  }

  const highCount = hotLeads.length;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "Email copied to clipboard",
    });
  };

  const normalizeRecommendedAction = (lead: Lead): SmartLeadAction => {
    const action = String(lead.score?.recommended_action || "").toLowerCase();
    if (action === "contact_immediately" || action === "add_to_sequence") return "send_message";
    if (action === "nurture") return "follow_up";
    if (action === "skip") return "not_fit";
    if ((lead.signal_keywords || []).length === 0 || !lead.industry) return "enrich_profile";
    if (lead.status === "contacted" || lead.status === "replied") return "follow_up";
    return "send_message";
  };

  const patchLeadInState = (leadId: string, patch: Partial<Lead>) => {
    setLeads((prev) => prev.map((item) => (item.id === leadId ? { ...item, ...patch } : item)));
    setHotLeads((prev) => prev.map((item) => (item.id === leadId ? { ...item, ...patch } : item)));
  };

  const runLeadAction = async (lead: Lead, action: SmartLeadAction) => {
    const actionKey = `${lead.id}:${action}`;
    setActionLoading((prev) => ({ ...prev, [actionKey]: true }));
    try {
      if (action === "send_message") {
        const updated = await leadsAPI.contact(lead.id);
        patchLeadInState(lead.id, {
          status: String(updated?.status || "contacted"),
          message_sent: true,
        });
        toast({
          title: "Message generated",
          description: `${lead.company || lead.name} marked as contacted.`,
        });
        logActivityEvent({
          type: "message",
          title: `Message sent to ${lead.company || lead.name}`,
          description: "Smart Action Panel: Send message",
          leadId: lead.id,
          leadName: lead.name,
          company: lead.company,
        });
        logActivityEvent({
          type: "status",
          title: `${lead.company || lead.name} status changed`,
          description: "Status updated to contacted",
          leadId: lead.id,
          leadName: lead.name,
          company: lead.company,
        });
      }

      if (action === "follow_up") {
        await leadsAPI.generateEmail(lead.id);
        if (String(lead.status || "").toLowerCase() === "new") {
          await leadsAPI.update(lead.id, { status: "contacted" });
          patchLeadInState(lead.id, { status: "contacted", message_sent: true });
          logActivityEvent({
            type: "status",
            title: `${lead.company || lead.name} status changed`,
            description: "Status updated to contacted",
            leadId: lead.id,
            leadName: lead.name,
            company: lead.company,
          });
        }
        toast({
          title: "Follow-up ready",
          description: `A fresh follow-up email was generated for ${lead.company || lead.name}.`,
        });
        logActivityEvent({
          type: "follow_up",
          title: `Follow-up generated for ${lead.company || lead.name}`,
          description: "Smart Action Panel: Follow up",
          leadId: lead.id,
          leadName: lead.name,
          company: lead.company,
        });
      }

      if (action === "enrich_profile") {
        const enriched = await leadsAPI.enrich(lead.id);
        patchLeadInState(lead.id, {
          industry: enriched?.industry ?? lead.industry,
          signal_keywords: enriched?.signal_keywords ?? lead.signal_keywords,
          signal_score: enriched?.signal_score ?? lead.signal_score,
          company_fit_score: enriched?.company_fit_score ?? lead.company_fit_score,
          score: enriched?.score ?? lead.score,
        });
        toast({
          title: "Profile enriched",
          description: `${lead.company || lead.name} was re-scored with latest enrichment.`,
        });
        logActivityEvent({
          type: "enrichment",
          title: `Lead enriched: ${lead.company || lead.name}`,
          description: "Profile data and score refreshed",
          leadId: lead.id,
          leadName: lead.name,
          company: lead.company,
        });
      }

      if (action === "not_fit") {
        await leadsAPI.update(lead.id, {
          status: "rejected",
          ai_notes: "Marked not a fit via Smart Action Panel",
        });
        patchLeadInState(lead.id, { status: "rejected" });
        toast({
          title: "Marked as not a fit",
          description: `${lead.company || lead.name} moved to rejected.`,
        });
        logActivityEvent({
          type: "status",
          title: `${lead.company || lead.name} marked not a fit`,
          description: "Status changed to rejected",
          leadId: lead.id,
          leadName: lead.name,
          company: lead.company,
        });
      }

      logActivityEvent({
        type: "ai_recommendation",
        title: `AI recommendation applied on ${lead.company || lead.name}`,
        description: `Action chosen: ${action.replace("_", " ")}`,
        leadId: lead.id,
        leadName: lead.name,
        company: lead.company,
      });

      fetchHotLeads();
    } catch (error: any) {
      toast({
        title: "Action failed",
        description: error?.message || "Could not complete lead action. Please retry.",
      });
    } finally {
      setActionLoading((prev) => ({ ...prev, [actionKey]: false }));
    }
  };

  const persistSavedViews = (next: SavedLeadView[]) => {
    setSavedViews(next);
    localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(next));
  };

  const saveCurrentView = () => {
    const name = viewName.trim();
    if (!name) {
      toast({
        title: "Name required",
        description: "Enter a view name before saving.",
      });
      return;
    }

    const snapshot: SavedLeadView = {
      id: activeViewId || `view_${Date.now()}`,
      name,
      filters: {
        activeTab,
        search,
        filterPriority,
        filterStatus,
        sortBy,
      },
    };

    const existingByName = savedViews.find((view) => view.name.toLowerCase() === name.toLowerCase());
    let next: SavedLeadView[];

    if (activeViewId) {
      next = savedViews.map((view) => (view.id === activeViewId ? snapshot : view));
    } else if (existingByName) {
      snapshot.id = existingByName.id;
      next = savedViews.map((view) => (view.id === existingByName.id ? snapshot : view));
    } else {
      next = [snapshot, ...savedViews].slice(0, 12);
    }

    persistSavedViews(next);
    setActiveViewId(snapshot.id);
    setViewName(snapshot.name);
    toast({
      title: "View saved",
      description: `"${snapshot.name}" is ready to reuse.`,
    });
  };

  const applyView = (view: SavedLeadView) => {
    setActiveTab(view.filters.activeTab);
    setSearch(view.filters.search);
    setFilterPriority(view.filters.filterPriority);
    setFilterStatus(view.filters.filterStatus);
    setSortBy(view.filters.sortBy);
    setActiveViewId(view.id);
    setViewName(view.name);
  };

  useEffect(() => {
    if (defaultApplied) return;
    if (!defaultViewId) {
      setDefaultApplied(true);
      return;
    }
    const defaultView = savedViews.find((view) => view.id === defaultViewId);
    if (!defaultView) {
      localStorage.removeItem(DEFAULT_VIEW_KEY);
      setDefaultViewId(null);
      setDefaultApplied(true);
      return;
    }
    applyView(defaultView);
    setDefaultApplied(true);
  }, [defaultApplied, defaultViewId, savedViews]);

  const toggleDefaultView = (id: string) => {
    if (defaultViewId === id) {
      localStorage.removeItem(DEFAULT_VIEW_KEY);
      setDefaultViewId(null);
      toast({
        title: "Default cleared",
        description: "This view will no longer auto-load.",
      });
      return;
    }

    localStorage.setItem(DEFAULT_VIEW_KEY, id);
    setDefaultViewId(id);
    const selected = savedViews.find((view) => view.id === id);
    toast({
      title: "Default view set",
      description: selected ? `"${selected.name}" will auto-load on page open.` : "Default view will auto-load.",
    });
  };

  const deleteView = (id: string) => {
    const next = savedViews.filter((view) => view.id !== id);
    persistSavedViews(next);
    if (activeViewId === id) {
      setActiveViewId(null);
      setViewName("");
    }
    if (defaultViewId === id) {
      localStorage.removeItem(DEFAULT_VIEW_KEY);
      setDefaultViewId(null);
    }
  };

  const resetFilters = () => {
    setActiveTab("all");
    setSearch("");
    setFilterPriority("All");
    setFilterStatus("All");
    setSortBy("score");
    setActiveViewId(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading leads from the database...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">All Leads</h1>
          <p className="text-muted-foreground text-sm mt-1">{filtered.length} leads • {highCount} hot leads (A)</p>
        </div>
        <Link to="/leads">
          <Button variant="outline" className="gap-2">
            <Users className="w-4 h-4" /> View Search Results
          </Button>
        </Link>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="all">All Leads</TabsTrigger>
          <TabsTrigger value="hot">Hot Leads (A) - {hotLeads.length}</TabsTrigger>
        </TabsList>
        <TabsContent value={activeTab} className="mt-4" />
      </Tabs>

      <Card className="border-border/50 shadow-sm">
        <CardContent className="p-4">
          <div className="mb-3 flex flex-col gap-2">
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                placeholder="Save current view as..."
                value={viewName}
                onChange={(e) => setViewName(e.target.value)}
                className="sm:max-w-xs"
              />
              <Button variant="outline" onClick={saveCurrentView}>
                {activeViewId ? "Update View" : "Save View"}
              </Button>
              <Button variant="ghost" onClick={resetFilters}>
                Reset Filters
              </Button>
            </div>
            {savedViews.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {savedViews.map((view) => (
                  <div key={view.id} className="flex items-center gap-1 rounded-full border border-border/60 px-2 py-1">
                    <button
                      type="button"
                      onClick={() => applyView(view)}
                      className={`text-xs font-medium ${
                        activeViewId === view.id ? "text-primary" : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {view.name}
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleDefaultView(view.id)}
                      className={`text-xs ${defaultViewId === view.id ? "text-warning" : "text-muted-foreground hover:text-warning"}`}
                      aria-label={defaultViewId === view.id ? `Unset default view ${view.name}` : `Set default view ${view.name}`}
                    >
                      {defaultViewId === view.id ? "★" : "☆"}
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteView(view.id)}
                      className="text-xs text-muted-foreground hover:text-destructive"
                      aria-label={`Delete view ${view.name}`}
                    >
                      x
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input placeholder="Search companies..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
            </div>
            <div className="flex gap-2 flex-wrap">
              {['All', 'High', 'Medium', 'Low'].map((p) => (
                <button
                  key={p}
                  onClick={() => setFilterPriority(p)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                    filterPriority === p ? 'bg-primary/10 text-primary border-primary/30' : 'text-muted-foreground border-border/50 hover:border-primary/20'
                  }`}
                >
                  {p === 'All' ? 'All Priority' : `${priorityConfig[p]?.emoji} ${p}`}
                </button>
              ))}
              {['All', 'New', 'Contacted'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                    filterStatus === status ? 'bg-primary/10 text-primary border-primary/30' : 'text-muted-foreground border-border/50 hover:border-primary/20'
                  }`}
                >
                  {status === 'All' ? 'All Status' : status}
                </button>
              ))}
              <button
                onClick={() => setSortBy(sortBy === 'score' ? 'company' : 'score')}
                className="px-3 py-1.5 text-xs font-medium rounded-full border border-border/50 text-muted-foreground hover:border-primary/20 transition-all flex items-center gap-1"
              >
                <ArrowUpDown className="w-3 h-3" /> {sortBy === 'score' ? 'By Score' : 'A-Z'}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      <motion.div variants={container} initial="hidden" animate="show" className="grid gap-4">
        {filtered.length === 0 ? (
          <Card className="border-border/50 shadow-sm">
            <CardContent className="p-8 text-center">
              <p className="text-muted-foreground">No leads found in the database matching your filters.</p>
            </CardContent>
          </Card>
        ) : (
          <>
            {filtered.map((lead) => {
              const totalScore = Number(lead.score?.total_score || 0);
              const grade = lead.score?.grade || "D";
              const priority = grade === "A" ? "High" : grade === "B" ? "Medium" : grade === "C" ? "Low" : "Low";
              const isExpanded = Boolean(expandedScore[lead.id]);
              const breakdown = lead.score?.breakdown || {};
              const breakdownRows = getBreakdownRows(breakdown);

              return (
                <motion.div key={lead.id} variants={item}>
                  <Card className={`border-border/50 shadow-sm hover:shadow-md transition-all hover:border-primary/20 ${priority === 'High' ? 'ring-1 ring-warning/10' : ''}`}>
                    <CardContent className="p-5">
                      <div className="flex flex-col lg:flex-row gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start gap-3">
                            <div className="w-11 h-11 rounded-xl bg-muted flex items-center justify-center text-sm font-bold text-foreground shrink-0">
                              {lead.company?.charAt(0) || "?"}
                            </div>
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <Link to={`/lead/${lead.id}`} className="font-semibold text-foreground hover:text-primary transition-colors">
                                  {lead.company || "Unknown Company"}
                                </Link>
                                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${priorityConfig[priority].color}`}>
                                  {priorityConfig[priority].emoji} {priority}
                                </span>
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusConfig[lead.status] || 'bg-muted/10 text-muted-foreground'}`}>
                                  {lead.status}
                                </span>
                              </div>
                              <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground flex-wrap">
                                {lead.job_title && <span>{lead.job_title}</span>}
                                {lead.industry && <span>{lead.industry}</span>}
                                {lead.created_at && <span>{new Date(lead.created_at).toLocaleDateString()}</span>}
                              </div>
                              <div className="mt-2 text-xs text-muted-foreground space-y-1">
                                {lead.email && <div><span className="font-semibold text-foreground">Email:</span> {lead.email}</div>}
                                {lead.phone && <div><span className="font-semibold text-foreground">Phone:</span> {lead.phone}</div>}
                                {lead.source_url && <div><span className="font-semibold text-foreground">Website:</span> <a href={lead.source_url} target="_blank" rel="noreferrer" className="text-primary underline">Visit</a></div>}
                              </div>
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="mt-3 ml-14 rounded-lg border border-border/50 bg-muted/20 p-3 space-y-2">
                              {breakdownRows.map(({ key, label, max }) => {
                                const value = Number((breakdown as any)[key] || 0);
                                const width = Math.max(0, Math.min(100, Math.round((value / max) * 100)));
                                return (
                                  <div key={key}>
                                    <div className="flex items-center justify-between text-xs mb-1">
                                      <span className="text-muted-foreground">{label}</span>
                                      <span className="font-medium text-foreground">{value}/{max}</span>
                                    </div>
                                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                                      <div className="h-full bg-primary rounded-full" style={{ width: `${width}%` }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}

                          <div className="mt-3 ml-14">
                            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1.5">Signals</p>
                            {lead.signal_keywords && lead.signal_keywords.length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {lead.signal_keywords.map((keyword, i) => (
                                  <Badge key={i} variant="secondary" className="text-xs">
                                    {keyword}
                                  </Badge>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground">No signals detected</p>
                            )}
                          </div>

                          <LeadActionPanel
                            recommendedAction={normalizeRecommendedAction(lead)}
                            onAction={(action) => runLeadAction(lead, action)}
                            isLoading={(action) => Boolean(actionLoading[`${lead.id}:${action}`])}
                          />
                        </div>

                        <div className="flex lg:flex-col items-center lg:items-end gap-3 lg:gap-2 shrink-0 lg:min-w-[160px]">
                          <div className="text-center lg:text-right">
                            <button
                              type="button"
                              onClick={() => setExpandedScore((prev) => ({ ...prev, [lead.id]: !prev[lead.id] }))}
                              className={`rounded-md px-3 py-1 text-sm font-semibold ${GRADE_STYLES[grade] || GRADE_STYLES.D}`}
                            >
                              {grade} - {totalScore}
                            </button>
                            <div className="text-xs text-muted-foreground mt-1">Score</div>
                            <div className="mt-2 space-y-0.5 text-xs">
                              <div className="flex justify-end gap-2">
                                <span className="text-muted-foreground">Fit:</span>
                                <span className="font-semibold text-foreground">{(lead.company_fit_score * 100).toFixed(0)}%</span>
                              </div>
                              <div className="flex justify-end gap-2">
                                <span className="text-muted-foreground">Signal:</span>
                                <span className="font-semibold text-foreground">{(lead.signal_score * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex gap-2 flex-wrap justify-end">
                            <Link to={`/lead/${lead.id}`}>
                              <Button variant="outline" size="sm" className="gap-1 text-xs">
                                <Eye className="w-3 h-3" /> Details
                              </Button>
                            </Link>
                            {lead.email && (
                              <Button variant="ghost" size="sm" className="gap-1 text-xs" onClick={() => copyToClipboard(lead.email)}>
                                <Copy className="w-3 h-3" /> Copy Email
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
            
            {hasMore && (
              <div className="flex justify-center pt-4">
                <Button 
                  onClick={handleLoadMore} 
                  disabled={loadingMore || activeTab === "hot"}
                  className="gap-2"
                >
                  {loadingMore ? (
                    <>
                      <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
                      Loading next 50...
                    </>
                  ) : (
                    <>Load More (+50)</>
                  )}
                </Button>
              </div>
            )}
          </>
        )}
      </motion.div>
    </div>
  );
}
