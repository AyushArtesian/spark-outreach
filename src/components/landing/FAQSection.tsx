import { motion } from "framer-motion";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const faqs = [
  { q: "How does the AI personalize messages?", a: "Our AI analyzes prospect data including LinkedIn activity, company news, job changes, and industry trends to craft unique messages for each prospect." },
  { q: "Can I connect my own email accounts?", a: "Yes! We support Gmail, Outlook, and custom SMTP servers. You can connect multiple accounts for higher sending volumes." },
  { q: "Is there a risk of getting flagged as spam?", a: "We use smart sending limits, warm-up protocols, and human-like sending patterns to maintain high deliverability rates." },
  { q: "How many prospects can I find per month?", a: "It depends on your plan — from 500/mo on Starter to unlimited on Agency. All prospects are enriched with verified emails." },
  { q: "Can I use OutreachAI for LinkedIn outreach?", a: "Absolutely. We support LinkedIn connection requests, DMs, and InMails alongside email outreach." },
  { q: "What happens during the free trial?", a: "You get full Pro features for 14 days. No credit card required. Cancel anytime." },
];

export default function FAQSection() {
  return (
    <section className="py-24">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-display font-bold mb-4">
            Frequently Asked <span className="gradient-text">Questions</span>
          </h2>
        </motion.div>

        <Accordion type="single" collapsible className="space-y-3">
          {faqs.map((faq, i) => (
            <AccordionItem key={i} value={`faq-${i}`} className="glass-card rounded-xl px-6 border-border/50">
              <AccordionTrigger className="text-left font-medium text-foreground hover:no-underline">
                {faq.q}
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground">
                {faq.a}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
