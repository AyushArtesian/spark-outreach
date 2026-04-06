import { useState } from "react";
import { motion } from "framer-motion";
import { Building2, Code, Briefcase, Globe, Target, Save, Check, X, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/hooks/use-toast";

const serviceOptions = ["Web Development", "Mobile App Development", "Cloud Migration", "AI/ML Development", "DevOps Consulting", "Data Engineering", "UI/UX Design", "Cybersecurity", "Blockchain", "QA & Testing"];
const techOptions = ["React", "Node.js", "Python", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "TensorFlow", "PostgreSQL", "MongoDB", "TypeScript", "Go", "Rust", "Flutter", "Swift"];
const industryOptions = ["SaaS", "FinTech", "Healthcare", "E-commerce", "EdTech", "Real Estate", "Logistics", "Media", "Insurance", "Manufacturing"];
const projectTypes = ["Fixed Price", "Time & Material", "Dedicated Team", "Staff Augmentation", "Consulting"];

function TagSelector({ options, selected, onToggle, label }: { options: string[]; selected: string[]; onToggle: (v: string) => void; label: string }) {
  return (
    <div>
      <label className="text-sm font-medium text-foreground mb-2 block">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const active = selected.includes(opt);
          return (
            <button
              key={opt}
              onClick={() => onToggle(opt)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                active
                  ? "bg-primary/10 text-primary border-primary/30"
                  : "bg-muted/30 text-muted-foreground border-border/50 hover:border-primary/20 hover:text-foreground"
              }`}
            >
              {active && <Check className="w-3 h-3 inline mr-1" />}
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function CompanySetup() {
  const [services, setServices] = useState<string[]>(["Web Development", "Cloud Migration", "AI/ML Development"]);
  const [techStack, setTechStack] = useState<string[]>(["React", "Node.js", "Python", "AWS", "Docker"]);
  const [industries, setIndustries] = useState<string[]>(["SaaS", "FinTech"]);
  const [projectType, setProjectType] = useState<string[]>(["Dedicated Team", "Time & Material"]);
  const [companyName, setCompanyName] = useState("Acme Software Solutions");
  const [website, setWebsite] = useState("https://acmesoftware.com");
  const [description, setDescription] = useState("Full-stack software development company specializing in cloud-native applications, AI/ML solutions, and enterprise digital transformation. 8 years of experience serving Fortune 500 and high-growth startups.");
  const [pastProjects, setPastProjects] = useState("1. Built a real-time fraud detection system for NovaPay (FinTech)\n2. Cloud migration for GreenLeaf Health — AWS, 40% cost reduction\n3. AI-powered recommendation engine for ShopStream (E-commerce)\n4. DevOps pipeline automation for DataVault (SaaS)");
  const [portfolioLinks, setPortfolioLinks] = useState(["https://acmesoftware.com/case-studies", ""]);

  const toggle = (list: string[], setList: (v: string[]) => void, val: string) => {
    setList(list.includes(val) ? list.filter((x) => x !== val) : [...list, val]);
  };

  const completionItems = [
    { label: "Company Info", done: !!companyName && !!website },
    { label: "Services", done: services.length > 0 },
    { label: "Tech Stack", done: techStack.length > 0 },
    { label: "Past Projects", done: !!pastProjects },
    { label: "Target Industries", done: industries.length > 0 },
  ];
  const completionPercent = Math.round((completionItems.filter((i) => i.done).length / completionItems.length) * 100);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Company Context Setup</h1>
          <p className="text-muted-foreground text-sm mt-1">Help our AI understand your business to find better leads</p>
        </div>
        <Button
          variant="gradient"
          className="gap-2"
          onClick={() => toast({ title: "Profile saved!", description: "Your company context has been updated." })}
        >
          <Save className="w-4 h-4" /> Save Profile
        </Button>
      </div>

      {/* Progress */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="border-border/50 shadow-sm">
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-foreground">Profile Completion</span>
              <span className="text-sm font-bold text-primary">{completionPercent}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-muted">
              <motion.div
                className="h-full rounded-full gradient-primary"
                initial={{ width: 0 }}
                animate={{ width: `${completionPercent}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
            </div>
            <div className="flex flex-wrap gap-3 mt-3">
              {completionItems.map((ci) => (
                <span key={ci.label} className={`text-xs flex items-center gap-1 ${ci.done ? "text-success" : "text-muted-foreground"}`}>
                  {ci.done ? <Check className="w-3 h-3" /> : <span className="w-3 h-3 rounded-full border border-border inline-block" />}
                  {ci.label}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Company Info */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Building2 className="w-4 h-4 text-primary" /> Company Information
            </CardTitle>
            <CardDescription>Basic details about your company</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Company Name</label>
                <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">Website</label>
                <Input value={website} onChange={(e) => setWebsite(e.target.value)} />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Company Description</label>
              <Textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Services */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-primary" /> Services Offered
            </CardTitle>
            <CardDescription>Select all services your company provides</CardDescription>
          </CardHeader>
          <CardContent>
            <TagSelector options={serviceOptions} selected={services} onToggle={(v) => toggle(services, setServices, v)} label="" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Tech Stack */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Code className="w-4 h-4 text-primary" /> Tech Stack
            </CardTitle>
            <CardDescription>Technologies your team works with</CardDescription>
          </CardHeader>
          <CardContent>
            <TagSelector options={techOptions} selected={techStack} onToggle={(v) => toggle(techStack, setTechStack, v)} label="" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Past Projects */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-primary" /> Past Projects & Portfolio
            </CardTitle>
            <CardDescription>Help AI match leads with your proven experience</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Key Projects</label>
              <Textarea rows={5} value={pastProjects} onChange={(e) => setPastProjects(e.target.value)} placeholder="Describe your most relevant past projects..." />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1.5 block">Portfolio Links</label>
              <div className="space-y-2">
                {portfolioLinks.map((link, i) => (
                  <div key={i} className="flex gap-2">
                    <Input value={link} onChange={(e) => { const n = [...portfolioLinks]; n[i] = e.target.value; setPortfolioLinks(n); }} placeholder="https://..." />
                    {portfolioLinks.length > 1 && (
                      <Button variant="ghost" size="icon" onClick={() => setPortfolioLinks(portfolioLinks.filter((_, j) => j !== i))}>
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={() => setPortfolioLinks([...portfolioLinks, ""])} className="gap-1">
                  <Plus className="w-3 h-3" /> Add Link
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Target Industries & Project Type */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <Card className="border-border/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base font-display flex items-center gap-2">
              <Target className="w-4 h-4 text-primary" /> Targeting Preferences
            </CardTitle>
            <CardDescription>Define your ideal client profile</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <TagSelector options={industryOptions} selected={industries} onToggle={(v) => toggle(industries, setIndustries, v)} label="Target Industries" />
            <TagSelector options={projectTypes} selected={projectType} onToggle={(v) => toggle(projectType, setProjectType, v)} label="Preferred Project Type" />
          </CardContent>
        </Card>
      </motion.div>

      {/* Bottom Save */}
      <div className="flex justify-end pb-4">
        <Button
          variant="gradient"
          size="lg"
          className="gap-2"
          onClick={() => toast({ title: "Profile saved!", description: "Your company context has been updated." })}
        >
          <Save className="w-4 h-4" /> Save & Continue
        </Button>
      </div>
    </div>
  );
}
