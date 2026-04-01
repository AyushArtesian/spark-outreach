import { motion } from "framer-motion";
import { Check, Edit, RefreshCw, SkipForward, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

const messages = [
  { id: 1, name: "David Kim", title: "CEO", company: "NexGen AI", confidence: 94, message: "Hi {{first_name}},\n\nI saw {{company}} just launched a new AI product — impressive!\n\nWe help AI startups like yours scale outbound by 3x. Would love to share how.\n\nWorth a quick 15-min call?" },
  { id: 2, name: "Rachel Torres", title: "VP Marketing", company: "ScaleUp", confidence: 89, message: "Hi {{first_name}},\n\nI noticed {{company}} is hiring aggressively — a sign of great growth!\n\nWe've helped similar companies automate their outreach while maintaining a personal touch.\n\nOpen to a brief chat this week?" },
  { id: 3, name: "Tom Bradley", title: "Founder", company: "LaunchPad", confidence: 92, message: "Hi {{first_name}},\n\nLoved your recent post about {{recent_post}}.\n\nAt OutreachAI, we help founders like you book 40+ meetings/month on autopilot.\n\nCurious to see how? Happy to show you a quick demo." },
  { id: 4, name: "Amanda Lee", title: "Sales Director", company: "RevBoost", confidence: 87, message: "Hi {{first_name}},\n\nI saw {{company}} is expanding into new markets. Exciting times!\n\nWe specialize in helping sales teams like yours reach new prospects with AI-personalized outreach.\n\nWould a 10-min call make sense?" },
];

export default function ReviewQueuePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Message Review Queue</h1>
          <p className="text-muted-foreground text-sm">{messages.length} messages waiting for approval</p>
        </div>
        <Button variant="gradient"><Check className="w-4 h-4" /> Approve All ({messages.length})</Button>
      </div>

      <div className="space-y-4">
        {messages.map((m, i) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass-card rounded-xl p-6"
          >
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="lg:w-48 shrink-0">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center text-xs font-bold text-primary-foreground">
                    {m.name.split(" ").map(n => n[0]).join("")}
                  </div>
                  <div>
                    <div className="font-medium text-sm text-foreground">{m.name}</div>
                    <div className="text-xs text-muted-foreground">{m.title}</div>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">{m.company}</div>
                <div className="mt-2 flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3 text-accent" />
                  <span className="text-xs text-accent font-medium">{m.confidence}% match</span>
                </div>
              </div>

              <div className="flex-1 rounded-lg bg-muted/30 border border-border/50 p-4">
                <pre className="text-sm text-foreground whitespace-pre-wrap leading-relaxed font-sans">
                  {m.message.replace(/\{\{(\w+)\}\}/g, (_, token) => `{{${token}}}`)}
                </pre>
              </div>

              <div className="flex lg:flex-col gap-2 lg:w-32 shrink-0">
                <Button variant="success" size="sm" className="flex-1"><Check className="w-3.5 h-3.5" /> Approve</Button>
                <Button variant="outline" size="sm" className="flex-1"><Edit className="w-3.5 h-3.5" /> Edit</Button>
                <Button variant="outline" size="sm" className="flex-1"><RefreshCw className="w-3.5 h-3.5" /> Rewrite</Button>
                <Button variant="ghost" size="sm" className="flex-1"><SkipForward className="w-3.5 h-3.5" /> Skip</Button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
