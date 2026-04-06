import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const faqs = [
  { q: "How does the AI know which leads are good for me?", a: "You set up your company profile — services, tech stack, past projects, and target industries. The AI uses this context to match and score every lead based on how well they align with your proven capabilities." },
  { q: "Is this just another lead scraper?", a: "No. Generic scrapers give you bulk data. We give you ranked, scored leads with clear reasoning — why each company is a fit, what signals we detected, and a suggested outreach message." },
  { q: "What signals does the AI detect?", a: "Hiring activity, funding rounds, technology adoption, expansion plans, RFPs, growth indicators, and more. Each signal is factored into the lead score." },
  { q: "How accurate is the lead scoring?", a: "Our users report a 23% average conversion rate on high-priority leads — compared to 2-3% industry average for cold outreach." },
  { q: "Can I integrate with my CRM?", a: "Yes. We support HubSpot, Salesforce, and Pipedrive integrations on Pro and Agency plans. You can also export leads as CSV." },
  { q: "Is there a free trial?", a: "Yes! Start with 25 free leads — no credit card required. See the quality before you commit." },
];

export default function FAQSection() {
  return (
    <section id="faq" className="py-20 bg-muted/30">
      <div className="container mx-auto px-4 max-w-2xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-display font-bold text-foreground">Frequently Asked Questions</h2>
        </div>
        <Accordion type="single" collapsible className="space-y-2">
          {faqs.map((faq, i) => (
            <AccordionItem key={i} value={`faq-${i}`} className="bg-card border border-border/50 rounded-xl px-5">
              <AccordionTrigger className="text-sm font-medium text-foreground hover:no-underline">{faq.q}</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground">{faq.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
