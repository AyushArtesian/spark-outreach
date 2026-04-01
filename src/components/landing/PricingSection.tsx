import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const plans = [
  {
    name: "Starter",
    price: "$49",
    desc: "Perfect for solo outreachers",
    features: ["500 prospects/mo", "1,000 emails/mo", "3 campaigns", "Basic AI personalization", "Email support"],
    popular: false,
  },
  {
    name: "Pro",
    price: "$99",
    desc: "For growing sales teams",
    features: ["5,000 prospects/mo", "10,000 emails/mo", "Unlimited campaigns", "Advanced AI + follow-ups", "LinkedIn integration", "Priority support"],
    popular: true,
  },
  {
    name: "Agency",
    price: "$299",
    desc: "For agencies & large teams",
    features: ["Unlimited prospects", "50,000 emails/mo", "Multi-client management", "Custom AI training", "API access", "Dedicated account manager"],
    popular: false,
  },
];

export default function PricingSection() {
  return (
    <section id="pricing" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">
            Simple, Transparent <span className="gradient-text">Pricing</span>
          </h2>
          <p className="text-muted-foreground text-lg">Start free. Upgrade when you're ready.</p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`glass-card rounded-2xl p-8 relative ${plan.popular ? "border-primary/50 glow-primary scale-105" : ""}`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full gradient-primary text-xs font-bold text-primary-foreground">
                  Most Popular
                </div>
              )}
              <h3 className="font-display font-bold text-xl mb-1 text-foreground">{plan.name}</h3>
              <p className="text-sm text-muted-foreground mb-4">{plan.desc}</p>
              <div className="mb-6">
                <span className="text-4xl font-display font-bold text-foreground">{plan.price}</span>
                <span className="text-muted-foreground">/mo</span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-foreground">
                    <Check className="w-4 h-4 text-success shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/register">
                <Button variant={plan.popular ? "gradient" : "outline"} className="w-full">
                  Get Started
                </Button>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
