import { motion } from "framer-motion";
import { Target, Search, Pencil, Send, TrendingUp } from "lucide-react";

const steps = [
  { icon: Target, title: "Define Audience", desc: "Set your ideal customer profile — industry, role, company size, pain points." },
  { icon: Search, title: "AI Finds Prospects", desc: "Our AI scrapes and enriches thousands of matching prospects automatically." },
  { icon: Pencil, title: "AI Writes Messages", desc: "Hyper-personalized messages crafted using prospect data and AI insights." },
  { icon: Send, title: "You Approve & Send", desc: "Review AI-generated messages, tweak if needed, and send with one click." },
  { icon: TrendingUp, title: "AI Learns & Improves", desc: "Every reply teaches the AI what works — your results improve over time." },
];

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Five simple steps to autopilot your outreach pipeline.
          </p>
        </motion.div>

        <div className="relative">
          {/* Connecting line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-primary/50 via-accent/50 to-primary/50 -translate-y-1/2" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8">
            {steps.map((s, i) => (
              <motion.div
                key={s.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="relative text-center"
              >
                <div className="relative z-10 w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <s.icon className="w-7 h-7 text-primary-foreground" />
                  <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-accent text-accent-foreground text-xs font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                </div>
                <h3 className="font-display font-semibold mb-2 text-foreground">{s.title}</h3>
                <p className="text-sm text-muted-foreground">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
