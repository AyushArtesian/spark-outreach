import { motion } from "framer-motion";
import { ArrowRight, Sparkles, Target, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function HeroSection() {
  return (
    <section className="relative py-20 lg:py-32 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.08),transparent_60%)]" />
      <div className="container mx-auto px-4 relative">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-sm text-primary font-medium mb-6">
            <Sparkles className="w-4 h-4" /> AI-Powered Lead Intelligence
          </div>
          <h1 className="text-4xl md:text-6xl font-display font-bold text-foreground leading-tight">
            Find the Right Leads,{" "}
            <span className="gradient-text">Not Just More Leads</span>
          </h1>
          <p className="text-lg text-muted-foreground mt-6 max-w-xl mx-auto">
            Our AI understands your company, matches it with market opportunities, and delivers leads ranked by conversion probability — so you target the right companies first.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center mt-8">
            <Link to="/register">
              <Button variant="gradient" size="xl" className="gap-2">
                Start Finding Leads <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
            <a href="#how-it-works">
              <Button variant="outline" size="xl">See How It Works</Button>
            </a>
          </div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="grid grid-cols-3 gap-6 mt-16 max-w-lg mx-auto">
            {[
              { icon: Target, value: "23.4%", label: "Avg Conversion" },
              { icon: TrendingUp, value: "8.2x", label: "ROI Improvement" },
              { icon: Sparkles, value: "92%", label: "Match Accuracy" },
            ].map((s) => (
              <div key={s.label} className="text-center">
                <s.icon className="w-5 h-5 text-primary mx-auto mb-1" />
                <div className="text-2xl font-display font-bold text-foreground">{s.value}</div>
                <div className="text-xs text-muted-foreground">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
