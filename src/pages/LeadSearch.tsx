import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, MapPin, Briefcase, Building2, Users, Sparkles, Check, Loader2, ArrowRight, Brain, Radar, Target, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { leadsAPI } from "@/services/api";
import { toast } from "@/hooks/use-toast";
import { logActivityEvent } from "@/lib/activityTimeline";

const serviceOptions = [
  // Software Development
  "Web App Development",
  "Mobile App Development",
  "eCommerce Web Development",
  "eCommerce App Development",
  "Product Development",
  "MVP Development",
  "Microsoft MAUI",
  "Salesforce Development",
  
  // Power Platform Services
  "Business Application Development",
  "Microsoft Power Pages",
  "Microsoft Power Apps",
  "Microsoft Power Automate",
  "Microsoft Power BI",
  "Microsoft Copilot Studio",
  "Microsoft Fabric",
  
  // Digital Transformation
  "Digital Transformation",
  "Power Platform Adoption",
  
  // Cloud Consulting
  "Azure Consulting",
  "DevOps Consulting & Engineering",
  "Cloud Migration",
  
  // Migrations
  "InfoPath to Power Apps",
  
  // Microsoft Dynamics 365
  "Microsoft Dynamics 365",
  
  // Additional services
  "Data Engineering",
  "UI/UX Design",
  "Cybersecurity",
  "AI/ML Development",
];

const industryFilters = [
  "All",
  "Automotive",
  "Healthcare",
  "Financial",
  "Internet of Things",
  "eCommerce",
  "Auction Software",
  "SaaS",
  "FinTech",
  "EdTech",
  "Real Estate",
];

const companySizes = ["1-10", "11-50", "51-200", "200-1000", "1000+"];

const processingSteps = [
  { icon: Brain, label: "Analyzing your company context", duration: 1200 },
  { icon: Radar, label: "Scanning market in target location", duration: 1800 },
  { icon: Target, label: "Matching opportunities with your strengths", duration: 1500 },
  { icon: Sparkles, label: "Scoring and ranking leads", duration: 1000 },
];

interface SavedSearchView {
  id: string;
  name: string;
  isDefault?: boolean;
  location: string;
  selectedServices: string[];
  selectedIndustry: string;
  selectedSizes: string[];
}

const SAVED_SEARCH_VIEWS_KEY = "lead_search_saved_views_v1";
const DEFAULT_SEARCH_VIEW_KEY = "lead_search_default_view_id_v1";

export default function LeadSearch() {
  const navigate = useNavigate();
  const [location, setLocation] = useState("");
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState("All");
  const [selectedSizes, setSelectedSizes] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [savedViews, setSavedViews] = useState<SavedSearchView[]>([]);
  const [viewName, setViewName] = useState("");
  const [activeViewId, setActiveViewId] = useState<string | null>(null);
  const [defaultViewId, setDefaultViewId] = useState<string | null>(null);
  const [defaultApplied, setDefaultApplied] = useState(false);

  const toggleService = (s: string) => setSelectedServices((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);
  const toggleSize = (s: string) => setSelectedSizes((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(SAVED_SEARCH_VIEWS_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      if (Array.isArray(parsed)) {
        setSavedViews(parsed);
      }
      const savedDefaultId = localStorage.getItem(DEFAULT_SEARCH_VIEW_KEY);
      if (savedDefaultId) {
        setDefaultViewId(savedDefaultId);
      }
    } catch {
      setSavedViews([]);
      setDefaultViewId(null);
    }
  }, []);

  const persistViews = (next: SavedSearchView[]) => {
    setSavedViews(next);
    localStorage.setItem(SAVED_SEARCH_VIEWS_KEY, JSON.stringify(next));
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

    if (!location || selectedServices.length === 0) {
      toast({
        title: "Not enough filters",
        description: "Add at least location and one service before saving.",
      });
      return;
    }

    const snapshot: SavedSearchView = {
      id: activeViewId || `search_view_${Date.now()}`,
      name,
      location,
      selectedServices,
      selectedIndustry,
      selectedSizes,
    };

    const existingByName = savedViews.find((view) => view.name.toLowerCase() === name.toLowerCase());
    let next: SavedSearchView[];
    if (activeViewId) {
      next = savedViews.map((view) => (view.id === activeViewId ? snapshot : view));
    } else if (existingByName) {
      snapshot.id = existingByName.id;
      next = savedViews.map((view) => (view.id === existingByName.id ? snapshot : view));
    } else {
      next = [snapshot, ...savedViews].slice(0, 12);
    }

    persistViews(next);
    setActiveViewId(snapshot.id);
    setViewName(snapshot.name);
    toast({
      title: "Search view saved",
      description: `"${snapshot.name}" is ready to reuse.`,
    });
  };

  const applyView = (view: SavedSearchView) => {
    setLocation(view.location);
    setSelectedServices(view.selectedServices || []);
    setSelectedIndustry(view.selectedIndustry || "All");
    setSelectedSizes(view.selectedSizes || []);
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
      localStorage.removeItem(DEFAULT_SEARCH_VIEW_KEY);
      setDefaultViewId(null);
      setDefaultApplied(true);
      return;
    }
    applyView(defaultView);
    setDefaultApplied(true);
  }, [defaultApplied, defaultViewId, savedViews]);

  const toggleDefaultView = (id: string) => {
    if (defaultViewId === id) {
      localStorage.removeItem(DEFAULT_SEARCH_VIEW_KEY);
      setDefaultViewId(null);
      toast({
        title: "Default cleared",
        description: "This search view will no longer auto-load.",
      });
      return;
    }

    localStorage.setItem(DEFAULT_SEARCH_VIEW_KEY, id);
    setDefaultViewId(id);
    const selected = savedViews.find((view) => view.id === id);
    toast({
      title: "Default view set",
      description: selected ? `"${selected.name}" will auto-load on page open.` : "Default view will auto-load.",
    });
  };

  const deleteView = (id: string) => {
    const next = savedViews.filter((view) => view.id !== id);
    persistViews(next);
    if (activeViewId === id) {
      setActiveViewId(null);
      setViewName("");
    }
    if (defaultViewId === id) {
      localStorage.removeItem(DEFAULT_SEARCH_VIEW_KEY);
      setDefaultViewId(null);
    }
  };

  const handleGenerate = async () => {
    setIsProcessing(true);
    setCurrentStep(0);
    setCompletedSteps([]);

    try {
      // Step 1: Analyze context
      setTimeout(() => {
        setCurrentStep(0);
        setTimeout(() => {
          setCompletedSteps((prev) => [...prev, 0]);
        }, processingSteps[0].duration);
      }, 100);

      // Step 2: Scan market
      setTimeout(() => {
        setCurrentStep(1);
        setTimeout(() => {
          setCompletedSteps((prev) => [...prev, 1]);
        }, processingSteps[1].duration);
      }, processingSteps[0].duration + 100);

      // Step 3: Match opportunities
      setTimeout(() => {
        setCurrentStep(2);
        setTimeout(() => {
          setCompletedSteps((prev) => [...prev, 2]);
        }, processingSteps[2].duration);
      }, processingSteps[0].duration + processingSteps[1].duration + 100);

      // Step 4: Score and rank (during this step, call the API)
      setTimeout(async () => {
        setCurrentStep(3);
        
        try {
          // Build search query from form inputs
          const query = `Find companies in ${selectedIndustry === "All" ? "all industries" : selectedIndustry} located in ${location} with size ${selectedSizes.length > 0 ? selectedSizes.join(", ") : "all sizes"} that need ${selectedServices.join(", ")}`;
          
          // Call the API
          const results = await leadsAPI.search({
            query: query,
            filters: {
              industry: selectedIndustry === "All" ? undefined : selectedIndustry,
              location: location,
              company_sizes: selectedSizes.length > 0 ? selectedSizes : undefined,
              services: selectedServices,
            },
            top_k: 50,
            sort_by: "combined",
          });

          // Store results in localStorage
          localStorage.setItem("searchResults", JSON.stringify(results));
          localStorage.setItem("searchQuery", query);
          logActivityEvent({
            type: "search",
            title: "Lead search executed",
            description: `${results.length || 0} leads for ${location} (${selectedIndustry})`,
          });

          setTimeout(() => {
            setCompletedSteps((prev) => [...prev, 3]);
            setTimeout(() => navigate("/leads"), 500);
          }, processingSteps[3].duration);
        } catch (error) {
          console.error("Search error:", error);
          toast({
            title: "Search Error",
            description: error instanceof Error ? error.message : "Failed to search leads",
            variant: "destructive",
          });
          setIsProcessing(false);
        }
      }, processingSteps[0].duration + processingSteps[1].duration + processingSteps[2].duration + 100);
    } catch (error) {
      console.error("Error:", error);
      toast({
        title: "Error",
        description: "An error occurred during the search",
        variant: "destructive",
      });
      setIsProcessing(false);
    }
  };

  if (isProcessing) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="w-full max-w-lg">
          <Card className="border-border/50 shadow-lg">
            <CardContent className="p-8 text-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-6"
              >
                <Sparkles className="w-8 h-8 text-primary-foreground" />
              </motion.div>
              <h2 className="text-xl font-display font-bold text-foreground mb-2">Finding Your Best Leads</h2>
              <p className="text-sm text-muted-foreground mb-8">Our AI is analyzing the market for you</p>

              <div className="space-y-4 text-left">
                {processingSteps.map((step, i) => {
                  const completed = completedSteps.includes(i);
                  const active = currentStep === i && !completed;
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex items-center gap-3 p-3 rounded-xl transition-all ${
                        completed ? "bg-success/5" : active ? "bg-primary/5" : "bg-muted/20"
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        completed ? "bg-success/10 text-success" : active ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                      }`}>
                        {completed ? <Check className="w-4 h-4" /> : active ? <Loader2 className="w-4 h-4 animate-spin" /> : <step.icon className="w-4 h-4" />}
                      </div>
                      <span className={`text-sm font-medium ${completed ? "text-success" : active ? "text-foreground" : "text-muted-foreground"}`}>
                        {step.label}
                      </span>
                    </motion.div>
                  );
                })}
              </div>

              <div className="mt-8">
                <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden">
                  <motion.div
                    className="h-full gradient-primary"
                    initial={{ width: "0%" }}
                    animate={{ width: `${((completedSteps.length) / processingSteps.length) * 100}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-2">{completedSteps.length} of {processingSteps.length} steps complete</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Search Leads</h1>
        <p className="text-muted-foreground text-sm mt-1">Tell us where to look and what you're offering</p>
      </div>

      <Card className="border-border/50 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base font-display">Saved Search Views</CardTitle>
          <CardDescription>Reuse common search setups instantly</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Save current setup as..."
              value={viewName}
              onChange={(e) => setViewName(e.target.value)}
              className="sm:max-w-xs"
            />
            <Button variant="outline" onClick={saveCurrentView}>
              {activeViewId ? "Update View" : "Save View"}
            </Button>
          </div>
          {savedViews.length > 0 ? (
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
          ) : (
            <p className="text-xs text-muted-foreground">No saved search views yet.</p>
          )}
        </CardContent>
      </Card>

      {/* Location */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <MapPin className="w-4 h-4 text-primary" /> Target Location
            </CardTitle>
            <CardDescription>Where should we search for companies?</CardDescription>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="e.g., San Francisco, CA or London, UK"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="text-base"
            />
          </CardContent>
        </Card>
      </motion.div>

      {/* Service Focus */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-primary" /> Service Focus
            </CardTitle>
            <CardDescription>What services are you looking to sell?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {serviceOptions.map((s) => {
                const active = selectedServices.includes(s);
                return (
                  <button
                    key={s}
                    onClick={() => toggleService(s)}
                    className={`px-3 py-1.5 text-sm font-medium rounded-full border transition-all ${
                      active ? "bg-primary/10 text-primary border-primary/30" : "bg-muted/30 text-muted-foreground border-border/50 hover:border-primary/20"
                    }`}
                  >
                    {active && <Check className="w-3 h-3 inline mr-1" />}{s}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Filter className="w-4 h-4 text-primary" /> Filters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">Industry</label>
              <div className="flex flex-wrap gap-2">
                {industryFilters.map((ind) => (
                  <button
                    key={ind}
                    onClick={() => setSelectedIndustry(ind)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                      selectedIndustry === ind ? "bg-primary/10 text-primary border-primary/30" : "bg-muted/30 text-muted-foreground border-border/50 hover:border-primary/20"
                    }`}
                  >
                    {ind}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-2 block">Company Size</label>
              <div className="flex flex-wrap gap-2">
                {companySizes.map((size) => {
                  const active = selectedSizes.includes(size);
                  return (
                    <button
                      key={size}
                      onClick={() => toggleSize(size)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                        active ? "bg-primary/10 text-primary border-primary/30" : "bg-muted/30 text-muted-foreground border-border/50 hover:border-primary/20"
                      }`}
                    >
                      <Users className="w-3 h-3 inline mr-1" />{size}
                    </button>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Generate */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="flex justify-center pt-2 pb-6">
        <Button
          variant="gradient"
          size="xl"
          className="gap-2 min-w-[240px]"
          onClick={handleGenerate}
          disabled={!location || selectedServices.length === 0}
        >
          <Sparkles className="w-5 h-5" /> Generate Leads
        </Button>
      </motion.div>
    </div>
  );
}
