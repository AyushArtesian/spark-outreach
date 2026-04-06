import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const plans = [
  {
    name: "Starter", price: "$49", desc: "For solo founders", popular: false,
    features: ["100 leads / month", "1 location", "Basic scoring", "Email support", "5 AI outreach messages"],
  },
  {
    name: "Pro", price: "$149", desc: "For growing teams", popular: true,
    features: ["1,000 leads / month", "Unlimited locations", "Advanced AI scoring", "Signal detection", "Unlimited AI outreach", "CRM integration", "Priority support"],
  },
  {
    name: "Agency", price: "$399", desc: "For BD teams", popular: false,
    features: ["5,000 leads / month", "Multi-team access", "Custom AI training", "API access", "Dedicated CSM", "White-label reports", "Everything in Pro"],
  },
];

export default function PricingSection() {
  return (
    <section id="pricing" className="py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-foreground">Simple, Transparent Pricing</h2>
          <p className="text-muted-foreground mt-2">Start free. Scale when you're ready.</p>
        </div>
        <div className="grid md:grid-cols-3 gap-5 max-w-4xl mx-auto">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`p-6 rounded-2xl border shadow-sm ${plan.popular ? "border-primary/30 bg-primary/5 ring-1 ring-primary/20" : "border-border/50 bg-card"}`}
            >
              {plan.popular && <div className="text-xs font-semibold text-primary mb-3">Most Popular</div>}
              <h3 className="font-display font-bold text-foreground text-lg">{plan.name}</h3>
              <p className="text-xs text-muted-foreground">{plan.desc}</p>
              <div className="mt-4 mb-6">
                <span className="text-3xl font-display font-bold text-foreground">{plan.price}</span>
                <span className="text-muted-foreground text-sm">/mo</span>
              </div>
              <ul className="space-y-2 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-foreground">
                    <Check className="w-4 h-4 text-success shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <Link to="/register">
                <Button variant={plan.popular ? "gradient" : "outline"} className="w-full">Get Started</Button>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
