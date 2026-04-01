import { motion } from "framer-motion";
import { Search, MessageSquare, GitBranch, BarChart3, Mail, Brain } from "lucide-react";

const features = [
  { icon: Search, title: "AI Prospect Scraping", desc: "Automatically find and enrich thousands of ideal prospects from LinkedIn, Apollo, and more." },
  { icon: MessageSquare, title: "Hyper-Personalized Messages", desc: "AI crafts unique messages referencing recent posts, company news, and pain points." },
  { icon: GitBranch, title: "Smart Follow-up Sequences", desc: "Multi-step sequences that adapt based on prospect behavior and engagement." },
  { icon: BarChart3, title: "Lead Scoring Engine", desc: "AI scores every prospect based on engagement signals to prioritize hot leads." },
  { icon: Mail, title: "Open/Reply Tracking", desc: "Real-time tracking of opens, clicks, and replies across all channels." },
  { icon: Brain, title: "AI Learning Loop", desc: "Your AI improves with every campaign, learning what messages convert best." },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-24 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">
            Everything You Need to <span className="gradient-text">Close More Deals</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            A complete AI outreach platform that handles prospecting, messaging, and optimization.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card rounded-xl p-6 hover:border-primary/30 transition-all duration-300 group"
            >
              <div className="w-12 h-12 rounded-lg gradient-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <f.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2 text-foreground">{f.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
