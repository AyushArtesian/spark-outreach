import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowRight, Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const stepNames = ["Target Audience", "Prospect Sources", "Message Templates", "Sending Settings", "Review & Launch"];

export default function NewCampaignPage() {
  const [step, setStep] = useState(0);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Link to="/campaigns"><Button variant="ghost" size="sm"><ArrowLeft className="w-4 h-4" /> Back</Button></Link>
        <h1 className="text-2xl font-display font-bold text-foreground">New Campaign</h1>
      </div>

      {/* Step Progress */}
      <div className="flex items-center gap-2">
        {stepNames.map((name, i) => (
          <div key={name} className="flex items-center gap-2 flex-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-all ${
              i < step ? "gradient-primary text-primary-foreground" : i === step ? "border-2 border-primary text-primary" : "border border-border text-muted-foreground"
            }`}>
              {i < step ? <Check className="w-4 h-4" /> : i + 1}
            </div>
            <span className={`text-xs hidden sm:block ${i === step ? "text-foreground font-medium" : "text-muted-foreground"}`}>{name}</span>
            {i < stepNames.length - 1 && <div className={`flex-1 h-0.5 ${i < step ? "gradient-primary" : "bg-border"}`} />}
          </div>
        ))}
      </div>

      <motion.div key={step} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="glass-card rounded-xl p-8">
        {step === 0 && (
          <div className="space-y-6">
            <h2 className="font-display font-semibold text-lg text-foreground">Define Your Target Audience</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Campaign Name</label>
                <input className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" placeholder="e.g., SaaS Founders Q1 2026" />
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Industry</label>
                  <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>SaaS</option><option>E-commerce</option><option>Healthcare</option><option>Finance</option><option>Real Estate</option><option>Agency</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Job Title</label>
                  <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>CEO / Founder</option><option>VP Sales</option><option>Marketing Director</option><option>CTO</option>
                  </select>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Company Size</label>
                  <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                    <option>1-10</option><option>11-50</option><option>51-200</option><option>200-1000</option><option>1000+</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Location</label>
                  <input className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" placeholder="e.g., United States" />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Pain Points</label>
                <textarea className="w-full h-24 px-4 py-3 rounded-lg bg-muted/50 border border-border text-foreground text-sm resize-none focus:outline-none focus:ring-1 focus:ring-primary" placeholder="Describe what problems your prospects face..." />
              </div>
              <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 flex items-center gap-3">
                <Sparkles className="w-5 h-5 text-accent shrink-0" />
                <p className="text-sm text-foreground">Based on your inputs, we found <span className="font-bold text-accent">8,420</span> matching prospects</p>
              </div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-6">
            <h2 className="font-display font-semibold text-lg text-foreground">Select Prospect Sources</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {["LinkedIn", "Apollo", "CSV Upload", "Manual Entry"].map((s) => (
                <div key={s} className="glass-card rounded-lg p-5 cursor-pointer hover:border-primary/50 transition-all">
                  <h3 className="font-semibold text-foreground mb-1">{s}</h3>
                  <p className="text-xs text-muted-foreground mb-3">Import prospects from {s}</p>
                  <Button variant="outline" size="sm">Connect</Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h2 className="font-display font-semibold text-lg text-foreground">Craft Your Messages</h2>
            <div className="flex gap-2">
              {["Email", "LinkedIn DM", "Connection Request"].map((ch) => (
                <button key={ch} className="px-4 py-1.5 rounded-full text-sm bg-muted/50 text-muted-foreground hover:text-foreground transition-colors">{ch}</button>
              ))}
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Tone</label>
                <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm"><option>Professional</option><option>Friendly</option><option>Bold</option><option>Consultative</option></select>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Length</label>
                <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm"><option>Short (3 lines)</option><option>Medium (5 lines)</option><option>Long (8 lines)</option></select>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Focus</label>
                <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm"><option>Pain Point</option><option>Case Study</option><option>Question</option><option>Compliment + Ask</option></select>
              </div>
            </div>
            <Button variant="gradient"><Sparkles className="w-4 h-4" /> Generate with AI</Button>
            <div className="rounded-lg bg-muted/30 border border-border p-4">
              <p className="text-sm text-foreground leading-relaxed">
                Hi <span className="text-accent font-medium">{"{{first_name}}"}</span>,<br /><br />
                I noticed <span className="text-accent font-medium">{"{{company}}"}</span> just expanded into new markets — congrats!<br /><br />
                We help companies like yours reduce outbound costs by 60% with AI personalization. Would love to share how we helped a similar company book 40 meetings in 30 days.<br /><br />
                Worth a quick chat this week?
              </p>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="font-display font-semibold text-lg text-foreground">Sending Settings</h2>
            <div className="space-y-4">
              <div className="glass-card rounded-lg p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground text-sm">Gmail</p>
                  <p className="text-xs text-muted-foreground">john@company.com</p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-success/10 text-success">Connected ✅</span>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Time Window</label>
                  <div className="flex gap-2">
                    <input type="time" defaultValue="09:00" className="flex-1 h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm" />
                    <input type="time" defaultValue="17:00" className="flex-1 h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Daily Limit</label>
                  <input type="range" min={1} max={200} defaultValue={80} className="w-full accent-primary" />
                  <p className="text-xs text-muted-foreground mt-1">80 emails/day</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-6">
            <h2 className="font-display font-semibold text-lg text-foreground">Review & Launch</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Campaign Name</span>
                <span className="text-foreground font-medium">SaaS Founders Q1 2026</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Target Audience</span>
                <span className="text-foreground font-medium">SaaS • CEO / Founder • 51-200</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Prospects</span>
                <span className="text-accent font-medium">8,420 matching</span>
              </div>
              <div className="flex justify-between py-2 border-b border-border/50">
                <span className="text-muted-foreground">Estimated Completion</span>
                <span className="text-foreground font-medium">~45 days</span>
              </div>
            </div>
            <div className="flex gap-3">
              <Button variant="gradient" size="lg" className="flex-1">🚀 Launch Campaign</Button>
              <Button variant="outline" size="lg">Save as Draft</Button>
            </div>
          </div>
        )}
      </motion.div>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>
          <ArrowLeft className="w-4 h-4" /> Previous
        </Button>
        {step < 4 && (
          <Button variant="gradient" onClick={() => setStep(step + 1)}>
            Next <ArrowRight className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
