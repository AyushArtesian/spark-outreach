import { motion } from "framer-motion";
import { Star } from "lucide-react";

const testimonials = [
  { name: "Alex Chen", role: "CEO, SaaSMetrics", text: "OutreachAI booked 47 meetings in our first month. The AI personalization is unlike anything I've seen.", avatar: "AC" },
  { name: "Maria Gonzalez", role: "VP Sales, CloudStack", text: "We replaced 3 SDRs with OutreachAI and got better results. 62% open rate and 18% reply rate.", avatar: "MG" },
  { name: "James Wright", role: "Founder, AgencyFlow", text: "The AI learning loop is genius. Our response rates improve every single week without us doing anything.", avatar: "JW" },
];

export default function TestimonialsSection() {
  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">
            Loved by <span className="gradient-text">Sales Teams</span>
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card rounded-xl p-6"
            >
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, j) => (
                  <Star key={j} className="w-4 h-4 fill-warning text-warning" />
                ))}
              </div>
              <p className="text-foreground mb-6 text-sm leading-relaxed">"{t.text}"</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center text-sm font-bold text-primary-foreground">
                  {t.avatar}
                </div>
                <div>
                  <div className="font-semibold text-sm text-foreground">{t.name}</div>
                  <div className="text-xs text-muted-foreground">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
