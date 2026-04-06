import { motion } from "framer-motion";
import { Brain, Target, TrendingUp, Search, Shield, Zap } from "lucide-react";

const features = [
  { icon: Brain, title: "Context-Aware AI", desc: "AI learns your services, past wins, and strengths to find leads that actually convert." },
  { icon: Search, title: "Market Scanning", desc: "Scans companies in your target location for hiring signals, funding, and growth patterns." },
  { icon: Target, title: "Precision Matching", desc: "Matches opportunities with your proven expertise — not just keyword overlap." },
  { icon: TrendingUp, title: "Lead Scoring", desc: "Every lead gets a conversion probability score with clear reasoning." },
  { icon: Shield, title: "Signal Detection", desc: "Detects hiring, funding, expansion, and technology signals in real-time." },
  { icon: Zap, title: "Instant Outreach", desc: "AI-generated outreach messages personalized to each lead's context." },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } };

export default function FeaturesSection() {
  return (
    <section id="features" className="py-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-foreground">Intelligent Lead Discovery</h2>
          <p className="text-muted-foreground mt-2 max-w-lg mx-auto">Not another generic scraper. This platform understands your business and finds opportunities that match.</p>
        </div>
        <motion.div variants={container} initial="hidden" whileInView="show" viewport={{ once: true }} className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f) => (
            <motion.div key={f.title} variants={item} className="p-6 rounded-2xl bg-card border border-border/50 shadow-sm hover:shadow-md hover:border-primary/20 transition-all">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <f.icon className="w-5 h-5 text-primary" />
              </div>
              <h3 className="font-display font-semibold text-foreground mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
