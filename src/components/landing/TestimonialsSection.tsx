import { motion } from "framer-motion";
import { Star } from "lucide-react";

const testimonials = [
  { name: "Sarah Chen", role: "Founder, DevScale", text: "We closed 3 enterprise deals in the first month. The AI matching is incredibly accurate — it found leads we never would have discovered manually.", rating: 5 },
  { name: "Marcus Johnson", role: "BD Lead, CloudForge", text: "The 'why this lead' explanations are a game-changer. My team makes decisions 5x faster because they trust the scoring.", rating: 5 },
  { name: "Anna Weber", role: "CEO, PixelCraft", text: "Replaced our entire manual lead research process. The context-aware matching saves us 20+ hours per week.", rating: 5 },
];

export default function TestimonialsSection() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-foreground">Trusted by Growth Teams</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-5">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-6 rounded-2xl bg-card border border-border/50 shadow-sm"
            >
              <div className="flex gap-1 mb-3">
                {Array.from({ length: t.rating }).map((_, j) => (
                  <Star key={j} className="w-4 h-4 fill-warning text-warning" />
                ))}
              </div>
              <p className="text-sm text-foreground mb-4 leading-relaxed">"{t.text}"</p>
              <div>
                <div className="text-sm font-semibold text-foreground">{t.name}</div>
                <div className="text-xs text-muted-foreground">{t.role}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
