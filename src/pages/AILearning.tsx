import { motion } from "framer-motion";
import { Brain, TrendingUp, TrendingDown, Sparkles, Check, Copy } from "lucide-react";
import { Button } from "@/components/ui/button";

const workingItems = [
  { label: "\"Quick question about {{company}}\"", stat: "58% open rate" },
  { label: "\"I noticed {{company}} just...\"", stat: "52% open rate" },
  { label: "\"Worth a quick chat?\" CTA", stat: "16% click rate" },
  { label: "Tuesday 10AM sends", stat: "61% open rate" },
];

const notWorkingItems = [
  { label: "Generic \"Hope you're doing well\" openers", stat: "12% open rate" },
  { label: "Emails longer than 150 words", stat: "8% reply rate" },
  { label: "Weekend sends", stat: "18% open rate" },
];

const templates = [
  { title: "The Compliment + Ask", replyRate: "18%", message: "Hi {{first_name}},\n\nLoved your recent post about {{recent_post}}. Really insightful!\n\nWe help companies like {{company}} automate outreach while keeping it personal. Would love to share how.\n\nWorth 15 min this week?" },
  { title: "The Data Hook", replyRate: "16%", message: "Hi {{first_name}},\n\n87% of SaaS companies waste 40+ hrs/week on manual outreach. We cut that to zero.\n\nCurious how? Happy to show you in a quick demo." },
  { title: "The Mutual Connection", replyRate: "21%", message: "Hi {{first_name}},\n\nI was chatting with a fellow {{industry}} founder who mentioned your work at {{company}}. Impressive growth!\n\nWe specialize in helping companies at your stage scale outbound. Open to connecting?" },
];

export default function AILearningPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-display font-bold text-foreground">AI Learning Center</h1>
      <p className="text-muted-foreground text-sm">Your AI gets smarter with every campaign</p>

      {/* Score Card */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-xl p-8 text-center">
        <div className="relative w-32 h-32 mx-auto mb-4">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--muted))" strokeWidth="8" />
            <circle cx="50" cy="50" r="42" fill="none" stroke="url(#gradient)" strokeWidth="8" strokeDasharray={`${78 * 2.64} 264`} strokeLinecap="round" />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="hsl(263, 70%, 58%)" />
                <stop offset="100%" stopColor="hsl(187, 92%, 43%)" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div>
              <div className="text-2xl font-display font-bold text-foreground">78</div>
              <div className="text-xs text-muted-foreground">/100</div>
            </div>
          </div>
        </div>
        <h2 className="font-display font-semibold text-foreground mb-1">AI Optimization Score</h2>
        <p className="text-sm text-muted-foreground">Your AI has analyzed 3,240 messages and 284 replies</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {[
            { label: "Messages Analyzed", value: "3,240" },
            { label: "Reply Patterns", value: "284" },
            { label: "A/B Tests Run", value: "42" },
            { label: "Optimizations", value: "156" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-lg font-bold text-foreground">{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </div>
          ))}
        </div>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* What's Working */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card rounded-xl p-6 border-success/20">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-success" />
            <h3 className="font-display font-semibold text-foreground">What's Working</h3>
          </div>
          <div className="space-y-3">
            {workingItems.map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 rounded-lg bg-success/5 border border-success/10">
                <span className="text-sm text-foreground">{item.label}</span>
                <span className="text-xs text-success font-medium">{item.stat}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* What's Not Working */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card rounded-xl p-6 border-destructive/20">
          <div className="flex items-center gap-2 mb-4">
            <TrendingDown className="w-5 h-5 text-destructive" />
            <h3 className="font-display font-semibold text-foreground">What's Not Working</h3>
          </div>
          <div className="space-y-3">
            {notWorkingItems.map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 rounded-lg bg-destructive/5 border border-destructive/10">
                <span className="text-sm text-foreground">{item.label}</span>
                <span className="text-xs text-destructive font-medium">{item.stat}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Winning Templates */}
      <div>
        <h3 className="font-display font-semibold text-foreground mb-4">Winning Message Templates</h3>
        <div className="grid md:grid-cols-3 gap-6">
          {templates.map((t, i) => (
            <motion.div key={t.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 + i * 0.1 }} className="glass-card rounded-xl p-6">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm text-foreground">{t.title}</h4>
                <span className="text-xs text-success font-medium">{t.replyRate} reply</span>
              </div>
              <pre className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed mb-4 font-sans">{t.message}</pre>
              <Button variant="outline" size="sm" className="w-full"><Copy className="w-3.5 h-3.5" /> Use This Template</Button>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
