import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, ArrowUpDown, Copy, Eye, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { leadsAPI } from "@/services/api";

interface Lead {
  id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  job_title?: string;
  industry?: string;
  source_url?: string;
  company_fit_score: number;
  signal_score: number;
  signal_keywords: string[];
  status: string;
  created_at: string;
}

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
  const [search, setSearch] = useState("");
  const [filterPriority, setFilterPriority] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");
  const [sortBy, setSortBy] = useState("score");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [skip, setSkip] = useState(0);
  const pageSize = 50;
  const hasMore = leads.length % pageSize === 0 && leads.length > 0;

  const fetchLeads = async (skipVal: number = 0) => {
    try {
      const isLoadMore = skipVal > 0;
      if (isLoadMore) setLoadingMore(true);
      
      const data = await leadsAPI.all(skipVal, pageSize);
      const formatted = data.map((lead: any) => ({
        ...lead,
        company_fit_score: lead.company_fit_score ?? 0,
        signal_score: lead.signal_score ?? 0,
        signal_keywords: lead.signal_keywords ?? [],
      }));
      
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

  useEffect(() => {
    fetchLeads(0);
  }, []);

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

  const filtered = leads.filter((lead) => {
    if (search && !lead.company?.toLowerCase().includes(search.toLowerCase())) return false;
    const priority = calculatePriority(lead.company_fit_score, lead.signal_score);
    if (filterPriority !== "All" && priority !== filterPriority) return false;
    if (filterStatus !== "All" && lead.status !== filterStatus) return false;
    return true;
  });

  if (sortBy === "score") {
    filtered.sort((a, b) => {
      const scoreA = a.company_fit_score * 0.5 + a.signal_score * 0.3;
      const scoreB = b.company_fit_score * 0.5 + b.signal_score * 0.3;
      return scoreB - scoreA;
    });
  }

  if (sortBy === "company") {
    filtered.sort((a, b) => (a.company || "").localeCompare(b.company || ""));
  }

  const highCount = leads.filter((l) => calculatePriority(l.company_fit_score, l.signal_score) === "High").length;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "Email copied to clipboard",
    });
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
          <p className="text-muted-foreground text-sm mt-1">
            {filtered.length} leads • {highCount} high priority {leads.length >= 50 ? `• more available` : ""}
          </p>
        </div>
        <Link to="/leads">
          <Button variant="outline" className="gap-2">
            <Users className="w-4 h-4" /> View Search Results
          </Button>
        </Link>
      </div>

      <Card className="border-border/50 shadow-sm">
        <CardContent className="p-4">
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
              const priority = calculatePriority(lead.company_fit_score, lead.signal_score);
              const combinedScore = lead.company_fit_score * 0.5 + lead.signal_score * 0.3;
              const scoreOut10 = Math.round(combinedScore * 10);

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
                        </div>

                        <div className="flex lg:flex-col items-center lg:items-end gap-3 lg:gap-2 shrink-0 lg:min-w-[160px]">
                          <div className="text-center lg:text-right">
                            <div className="text-3xl font-display font-bold text-primary">{scoreOut10}</div>
                            <div className="text-xs text-muted-foreground">/ 10</div>
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
                  disabled={loadingMore}
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
