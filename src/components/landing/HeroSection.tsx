import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const demoMessage = `Hi Sarah,\n\nI noticed Acme Corp just raised a Series B — congrats! 🎉\n\nI help fast-growing SaaS companies like yours cut outbound costs by 60% using AI-powered personalization.\n\nWould love to share how we helped a similar company book 40 meetings in 30 days.\n\nWorth a quick chat?`;

export default function HeroSection() {
  const [displayText, setDisplayText] = useState("");
  const [charIndex, setCharIndex] = useState(0);

  useEffect(() => {
    if (charIndex < demoMessage.length) {
      const timeout = setTimeout(() => {
        setDisplayText(demoMessage.slice(0, charIndex + 1));
        setCharIndex((i) => i + 1);
      }, 25);
      return () => clearTimeout(timeout);
    }
  }, [charIndex]);

  return (
    <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/15 rounded-full blur-[120px]" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 mb-6">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">AI-Powered Outreach Engine</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-bold leading-tight mb-6">
              Turn Strangers Into Clients{" "}
              <span className="gradient-text">— On Autopilot</span>
            </h1>

            <p className="text-lg text-muted-foreground mb-8 max-w-lg">
              Let AI find your ideal prospects, craft hyper-personalized messages, and follow up automatically. More meetings, zero grunt work.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/register">
                <Button variant="gradient" size="xl">
                  Start Free Trial <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="outline" size="xl">
                  See How It Works
                </Button>
              </a>
            </div>

            <div className="mt-8 flex items-center gap-6 text-sm text-muted-foreground">
              <span>✓ No credit card required</span>
              <span>✓ 14-day free trial</span>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="relative"
          >
            <div className="glass-card rounded-2xl p-6 glow-primary">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-destructive/80" />
                <div className="w-3 h-3 rounded-full bg-warning/80" />
                <div className="w-3 h-3 rounded-full bg-success/80" />
                <span className="ml-2 text-xs text-muted-foreground">AI Writing Message...</span>
              </div>
              <div className="bg-background/50 rounded-lg p-4 font-mono text-sm leading-relaxed min-h-[240px]">
                <pre className="whitespace-pre-wrap text-foreground/90">{displayText}</pre>
                <span className="inline-block w-0.5 h-4 bg-accent animate-blink ml-0.5" />
              </div>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-accent font-medium">92% Personalization Score</span>
                <Button variant="gradient" size="sm">Send Message</Button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
