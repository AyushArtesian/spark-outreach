import { motion } from "framer-motion";
import { Building2, Search, Brain, Star, Send } from "lucide-react";

const steps = [
  { icon: Building2, title: "Setup Your Profile", desc: "Tell the AI about your services, tech stack, and past projects." },
  { icon: Search, title: "Choose Location & Service", desc: "Select where to search and what you're offering." },
  { icon: Brain, title: "AI Scans the Market", desc: "Our AI analyzes companies, detects signals, and matches opportunities." },
  { icon: Star, title: "Review Ranked Leads", desc: "See scored leads with clear reasoning — why each one is a fit." },
  { icon: Send, title: "Take Action", desc: "Use AI-generated outreach messages to reach your best leads first." },
];

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-foreground">How It Works</h2>
          <p className="text-muted-foreground mt-2">Five simple steps to high-quality leads</p>
        </div>
        <div className="max-w-2xl mx-auto space-y-0">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex gap-4"
            >
              <div className="flex flex-col items-center">
                <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center text-primary-foreground font-bold text-sm shrink-0">
                  {i + 1}
                </div>
                {i < steps.length - 1 && <div className="w-px flex-1 bg-border my-1" />}
              </div>
              <div className="pb-8">
                <h3 className="font-display font-semibold text-foreground">{step.title}</h3>
                <p className="text-sm text-muted-foreground mt-1">{step.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
