import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function CTASection() {
  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-3xl gradient-primary p-12 text-center relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_50%,rgba(255,255,255,0.1),transparent)]" />
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-display font-bold text-primary-foreground">
              Stop Guessing. Start Closing.
            </h2>
            <p className="text-primary-foreground/80 mt-3 max-w-lg mx-auto">
              Let AI find the companies most likely to become your next clients.
            </p>
            <Link to="/register">
              <Button size="xl" className="mt-6 bg-background text-foreground hover:bg-background/90 gap-2">
                Get Started Free <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
