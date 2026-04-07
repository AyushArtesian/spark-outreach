import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronRight, ChevronLeft, Loader2 } from "lucide-react";

const API_BASE = "http://localhost:8000/api/v1";

const getToken = () => localStorage.getItem("auth_token");

async function apiCall(endpoint: string, options: RequestInit & { requiresAuth?: boolean } = {}) {
  const { requiresAuth = false, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...fetchOptions.headers,
  };

  if (requiresAuth) {
    const token = getToken();
    if (!token) {
      throw new Error("No authentication token found");
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.statusText}`);
  }

  return response.json();
}

export default function CompanySetup() {
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [companyData, setCompanyData] = useState({
    company_name: "",
    company_size: "",
    company_stage: "",
    company_description: "",
    company_website: "",
    upwork_id: "",
    github_url: "",
    linkedin_url: "",
    portfolio_urls: [] as string[],
    services: [] as string[],
    expertise_areas: [] as string[],
    technologies: [] as string[],
    target_industries: [] as string[],
    target_locations: [] as string[],
    team_size: "",
    team_expertise: [] as string[],
    projects: [] as any[],
    min_deal_size: "",
    max_deal_size: "",
    preferred_company_stages: [] as string[],
  });

  // Load existing profile on mount
  useEffect(() => {
    const loadProfile = async () => {
      setIsLoading(true);
      try {
        const profile = await apiCall("/company/profile", { requiresAuth: true });
        if (profile) {
          setCompanyData((prev) => ({
            ...prev,
            ...profile,
            company_website: profile.company_website || "",
            upwork_id: profile.upwork_id || "",
            github_url: profile.github_url || "",
            linkedin_url: profile.linkedin_url || "",
            portfolio_urls: Array.isArray(profile.portfolio_urls) ? profile.portfolio_urls : [],
            services: Array.isArray(profile.services) ? profile.services : [],
            expertise_areas: Array.isArray(profile.expertise_areas) ? profile.expertise_areas : [],
            technologies: Array.isArray(profile.technologies) ? profile.technologies : [],
            target_industries: Array.isArray(profile.target_industries) ? profile.target_industries : [],
            target_locations: Array.isArray(profile.target_locations) ? profile.target_locations : [],
            team_expertise: Array.isArray(profile.team_expertise) ? profile.team_expertise : [],
            projects: Array.isArray(profile.projects) ? profile.projects : [],
            preferred_company_stages: Array.isArray(profile.preferred_company_stages) ? profile.preferred_company_stages : [],
          }));
        }
      } catch (err: any) {
        // Profile doesn't exist yet, that's okay for new users
        console.log("No existing profile found");
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      loadProfile();
    }
  }, [user]);

  const steps = [
    { title: "Basic Info", description: "Company name and stage" },
    { title: "Services & Expertise", description: "What you offer" },
    { title: "Projects & Portfolio", description: "Your work samples" },
    { title: "Target Market", description: "Industries and locations" },
    { title: "Review & Launch", description: "Finalize and generate intelligence" },
  ];

  const handleInputChange = (field: string, value: any) => {
    setCompanyData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayAdd = (field: string, value: string) => {
    if (value.trim()) {
      setCompanyData((prev) => ({
        ...prev,
        [field]: [...(prev[field as keyof typeof companyData] as string[]), value],
      }));
    }
  };

  const handleArrayRemove = (field: string, index: number) => {
    setCompanyData((prev) => ({
      ...prev,
      [field]: (prev[field as keyof typeof companyData] as string[]).filter((_, i) => i !== index),
    }));
  };

  const handleSaveProgress = async () => {
    setIsSaving(true);
    setError("");
    try {
      await apiCall("/company/profile", {
        method: "PUT",
        body: JSON.stringify(companyData),
        requiresAuth: true,
      });
    } catch (err: any) {
      setError(err.message || "Failed to save progress");
    } finally {
      setIsSaving(false);
    }
  };

  const handleNextStep = async () => {
    await handleSaveProgress();
    if (step < steps.length - 1) {
      setStep(step + 1);
    }
  };

  const handlePrevStep = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const handleComplete = async () => {
    setIsSaving(true);
    setError("");
    try {
      // Save profile
      await apiCall("/company/profile", {
        method: "PUT",
        body: JSON.stringify(companyData),
        requiresAuth: true,
      });

      // Generate embeddings
      await apiCall("/company/profile/generate-embeddings", {
        method: "POST",
        requiresAuth: true,
      });

      // Generate ICP and signals
      await apiCall("/company/profile/generate-icp", {
        method: "POST",
        requiresAuth: true,
      });

      // Mark as complete
      await apiCall("/company/profile/complete-setup", {
        method: "POST",
        requiresAuth: true,
      });

      // Redirect to dashboard
      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(err.message || "Failed to complete setup");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold text-foreground">Company Setup</h1>
        <p className="text-muted-foreground mt-2">
          Let's understand your company context to find better leads
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center justify-between">
        {steps.map((s, i) => (
          <div key={i} className="flex items-center">
            <button
              onClick={() => setStep(i)}
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                i === step
                  ? "bg-primary text-primary-foreground"
                  : i < step
                  ? "bg-success text-success-foreground"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {i < step ? "✓" : i + 1}
            </button>
            {i < steps.length - 1 && (
              <div className={`h-1 w-12 mx-2 ${i < step ? "bg-success" : "bg-muted"}`} />
            )}
          </div>
        ))}
      </div>

      {/* Step Title */}
      <div>
        <h2 className="text-2xl font-display font-bold text-foreground">{steps[step].title}</h2>
        <p className="text-muted-foreground">{steps[step].description}</p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Step Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          className="space-y-6"
        >
          {/* Step 0: Basic Info */}
          {step === 0 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Company Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Company Name</label>
                    <Input
                      placeholder="e.g., Acme Software Solutions"
                      value={companyData.company_name}
                      onChange={(e) => handleInputChange("company_name", e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">Company Size</label>
                      <select
                        value={companyData.company_size}
                        onChange={(e) => handleInputChange("company_size", e.target.value)}
                        className="w-full h-10 px-3 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="">Select size...</option>
                        <option value="1-10">1-10 people</option>
                        <option value="11-50">11-50 people</option>
                        <option value="51-200">51-200 people</option>
                        <option value="201-1000">201-1000 people</option>
                        <option value="1000+">1000+ people</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">Company Stage</label>
                      <select
                        value={companyData.company_stage}
                        onChange={(e) => handleInputChange("company_stage", e.target.value)}
                        className="w-full h-10 px-3 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="">Select stage...</option>
                        <option value="early-stage">Early Stage</option>
                        <option value="growth">Growth</option>
                        <option value="mature">Mature</option>
                        <option value="enterprise">Enterprise</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Description</label>
                    <textarea
                      placeholder="Brief description of your company..."
                      value={companyData.company_description}
                      onChange={(e) => handleInputChange("company_description", e.target.value)}
                      className="w-full h-24 p-3 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                    />
                  </div>
                </CardContent>
              </Card>
              {/* Portfolio Links */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Portfolio & Online Presence</CardTitle>
                  <CardDescription>Add links to your website and professional profiles</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Company Website</label>
                    <Input
                      placeholder="https://example.com"
                      value={companyData.company_website}
                      onChange={(e) => handleInputChange("company_website", e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">Upwork URL or Slug</label>
                      <Input
                        placeholder="https://www.upwork.com/agencies/your-agency/"
                        value={companyData.upwork_id}
                        onChange={(e) => handleInputChange("upwork_id", e.target.value)}
                      />
                    </div>

                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">GitHub URL</label>
                      <Input
                        placeholder="https://github.com/username"
                        value={companyData.github_url}
                        onChange={(e) => handleInputChange("github_url", e.target.value)}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">LinkedIn URL</label>
                    <Input
                      placeholder="https://linkedin.com/company/your-company"
                      value={companyData.linkedin_url}
                      onChange={(e) => handleInputChange("linkedin_url", e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Other Portfolio URLs</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="portfolio-input"
                        placeholder="e.g., https://portfolio.example.com"
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleArrayAdd("portfolio_urls", (e.target as HTMLInputElement).value);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          const input = document.getElementById("portfolio-input") as HTMLInputElement;
                          handleArrayAdd("portfolio_urls", input.value);
                          input.value = "";
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {companyData.portfolio_urls.map((url, i) => (
                        <div key={i} className="bg-blue-500/10 text-blue-600 px-3 py-1 rounded-full text-sm flex items-center gap-2 max-w-xs truncate">
                          <span className="truncate">{url}</span>
                          <button onClick={() => handleArrayRemove("portfolio_urls", i)} className="hover:text-blue-600/60 flex-shrink-0">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>            </div>
          )}

          {/* Step 1: Services & Expertise */}
          {step === 1 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Services & Expertise</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Services */}
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Services</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="service-input"
                        placeholder="e.g., Web Development"
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleArrayAdd("services", (e.target as HTMLInputElement).value);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          const input = document.getElementById("service-input") as HTMLInputElement;
                          handleArrayAdd("services", input.value);
                          input.value = "";
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {companyData.services.map((service, i) => (
                        <div key={i} className="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm flex items-center gap-2">
                          {service}
                          <button onClick={() => handleArrayRemove("services", i)} className="hover:text-primary/60">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Technologies */}
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Technologies</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="tech-input"
                        placeholder="e.g., React, Node.js"
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleArrayAdd("technologies", (e.target as HTMLInputElement).value);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          const input = document.getElementById("tech-input") as HTMLInputElement;
                          handleArrayAdd("technologies", input.value);
                          input.value = "";
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {companyData.technologies.map((tech, i) => (
                        <div key={i} className="bg-accent/10 text-accent px-3 py-1 rounded-full text-sm flex items-center gap-2">
                          {tech}
                          <button onClick={() => handleArrayRemove("technologies", i)} className="hover:text-accent/60">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Team Expertise */}
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Team Expertise</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="expertise-input"
                        placeholder="e.g., Full Stack Development"
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleArrayAdd("team_expertise", (e.target as HTMLInputElement).value);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          const input = document.getElementById("expertise-input") as HTMLInputElement;
                          handleArrayAdd("team_expertise", input.value);
                          input.value = "";
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {companyData.team_expertise.map((exp, i) => (
                        <div key={i} className="bg-success/10 text-success px-3 py-1 rounded-full text-sm flex items-center gap-2">
                          {exp}
                          <button onClick={() => handleArrayRemove("team_expertise", i)} className="hover:text-success/60">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 2: Projects */}
          {step === 2 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Projects & Portfolio</CardTitle>
                  <CardDescription>Describe your past work to help us understand your expertise</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {companyData.projects.length === 0 ? (
                    <p className="text-muted-foreground text-sm">No projects added yet</p>
                  ) : (
                    companyData.projects.map((project, i) => (
                      <div key={i} className="p-4 border border-border rounded-lg space-y-2">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-semibold text-foreground">{project.title}</h4>
                            <p className="text-sm text-muted-foreground">{project.description}</p>
                          </div>
                          <button
                            onClick={() => {
                              setCompanyData((prev) => ({
                                ...prev,
                                projects: prev.projects.filter((_, idx) => idx !== i),
                              }));
                            }}
                            className="text-red-500 hover:text-red-600"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    ))
                  )}

                  <div className="border-t pt-4 space-y-4">
                    <h4 className="font-medium text-foreground">Add New Project</h4>
                    <Input placeholder="Project Title" id="project-title" />
                    <textarea
                      placeholder="Project Description"
                      id="project-desc"
                      className="w-full h-20 p-3 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                    />
                    <Button
                      onClick={() => {
                        const title = (document.getElementById("project-title") as HTMLInputElement).value;
                        const desc = (document.getElementById("project-desc") as HTMLTextAreaElement).value;
                        if (title && desc) {
                          setCompanyData((prev) => ({
                            ...prev,
                            projects: [...prev.projects, { title, description: desc, technologies: [] }],
                          }));
                          (document.getElementById("project-title") as HTMLInputElement).value = "";
                          (document.getElementById("project-desc") as HTMLTextAreaElement).value = "";
                        }
                      }}
                    >
                      Add Project
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 3: Target Market */}
          {step === 3 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Target Market</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Industries */}
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Target Industries</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="industry-input"
                        placeholder="e.g., SaaS, FinTech"
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleArrayAdd("target_industries", (e.target as HTMLInputElement).value);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          const input = document.getElementById("industry-input") as HTMLInputElement;
                          handleArrayAdd("target_industries", input.value);
                          input.value = "";
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {companyData.target_industries.map((ind, i) => (
                        <div key={i} className="bg-primary/10 text-primary px-3 py-1 rounded-full text-sm flex items-center gap-2">
                          {ind}
                          <button onClick={() => handleArrayRemove("target_industries", i)} className="hover:text-primary/60">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Locations */}
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-2">Target Locations</label>
                    <div className="flex gap-2 mb-2">
                      <Input
                        id="location-input"
                        placeholder="e.g., US, UK, Canada"
                        onKeyPress={(e) => {
                          if (e.key === "Enter") {
                            handleArrayAdd("target_locations", (e.target as HTMLInputElement).value);
                            (e.target as HTMLInputElement).value = "";
                          }
                        }}
                      />
                      <Button
                        onClick={() => {
                          const input = document.getElementById("location-input") as HTMLInputElement;
                          handleArrayAdd("target_locations", input.value);
                          input.value = "";
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {companyData.target_locations.map((loc, i) => (
                        <div key={i} className="bg-accent/10 text-accent px-3 py-1 rounded-full text-sm flex items-center gap-2">
                          {loc}
                          <button onClick={() => handleArrayRemove("target_locations", i)} className="hover:text-accent/60">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Deal Size */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">Min Deal Size</label>
                      <Input
                        placeholder="e.g., $10k, $50k"
                        value={companyData.min_deal_size}
                        onChange={(e) => handleInputChange("min_deal_size", e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium text-foreground block mb-2">Max Deal Size</label>
                      <Input
                        placeholder="e.g., $100k, $500k"
                        value={companyData.max_deal_size}
                        onChange={(e) => handleInputChange("max_deal_size", e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 4: Review */}
          {step === 4 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Review Your Profile</CardTitle>
                  <CardDescription>We'll now generate your ideal customer profile and lead signals</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 p-4 bg-muted/30 rounded-lg">
                    <div>
                      <p className="text-xs text-muted-foreground">Company</p>
                      <p className="font-semibold text-foreground">{companyData.company_name}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Stage</p>
                      <p className="font-semibold text-foreground">{companyData.company_stage}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-xs text-muted-foreground mb-1">Services</p>
                      <div className="flex flex-wrap gap-2">
                        {companyData.services.map((s, i) => (
                          <span key={i} className="text-xs bg-primary/20 text-primary px-2 py-1 rounded">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="col-span-2">
                      <p className="text-xs text-muted-foreground mb-1">Target Industries</p>
                      <div className="flex flex-wrap gap-2">
                        {companyData.target_industries.map((i, idx) => (
                          <span key={idx} className="text-xs bg-accent/20 text-accent px-2 py-1 rounded">
                            {i}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
                    <p className="text-sm text-success font-medium">✓ All set!</p>
                    <p className="text-xs text-success/80 mt-1">
                      We'll now generate your Ideal Customer Profile, extract key signals, and create embeddings for intelligent lead matching.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between gap-4 pt-6 border-t border-border">
        <Button
          variant="outline"
          onClick={handlePrevStep}
          disabled={step === 0 || isSaving}
        >
          <ChevronLeft className="w-4 h-4" /> Previous
        </Button>

        {step === steps.length - 1 ? (
          <Button
            variant="gradient"
            onClick={handleComplete}
            disabled={isSaving || !companyData.company_name}
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Generating Intelligence...
              </>
            ) : (
              <>Complete Setup <ChevronRight className="w-4 h-4" /></>
            )}
          </Button>
        ) : (
          <Button
            variant="gradient"
            onClick={handleNextStep}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Saving...
              </>
            ) : (
              <>Next <ChevronRight className="w-4 h-4" /></>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
