import { motion } from "framer-motion";
import { Sparkles, User, Mail, Lock, Building, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden py-12">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/15 rounded-full blur-[120px]" />

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative w-full max-w-md mx-4">
        <div className="glass-card rounded-2xl p-8">
          <div className="flex items-center justify-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="font-display font-bold text-2xl text-foreground">LeadIntel AI</span>
          </div>

          <h1 className="text-xl font-display font-bold text-foreground text-center mb-2">Start Your Free Trial</h1>
          <p className="text-center text-sm text-muted-foreground mb-6">14 days free. No credit card required.</p>

          <div className="space-y-4">
            <Button variant="outline" className="w-full h-11">
              <img src="https://www.google.com/favicon.ico" className="w-4 h-4" alt="" /> Continue with Google
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border" /></div>
              <div className="relative flex justify-center"><span className="bg-card px-3 text-xs text-muted-foreground">or</span></div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Full Name</label>
                <input placeholder="John Doe" className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground block mb-1.5">Company</label>
                <input placeholder="Acme Corp" className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Email</label>
              <input type="email" placeholder="john@company.com" className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>

            <div>
              <label className="text-sm font-medium text-foreground block mb-1.5">Password</label>
              <input type="password" placeholder="••••••••" className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
            </div>

            <div>
            <label className="text-sm font-medium text-foreground block mb-1.5">I am a...</label>
              <select className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary">
                <option>Founder</option>
                <option>Business Development</option>
                <option>Sales Team</option>
              </select>
            </div>

            <label className="flex items-start gap-2 text-sm text-muted-foreground">
              <input type="checkbox" className="mt-1 accent-primary" />
              I agree to the Terms of Service and Privacy Policy
            </label>

            <Link to="/dashboard">
              <Button variant="gradient" className="w-full h-11">
                Create Account <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>

          <p className="text-center text-sm text-muted-foreground mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-primary hover:underline font-medium">Log In</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
