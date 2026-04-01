import { useState } from "react";
import { motion } from "framer-motion";
import { User, Link2, Bell, Gauge, CreditCard, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

const tabs = [
  { label: "Profile", icon: User },
  { label: "Connected Accounts", icon: Link2 },
  { label: "Sending Limits", icon: Gauge },
  { label: "Notifications", icon: Bell },
  { label: "Billing", icon: CreditCard },
];

const invoices = [
  { date: "Mar 1, 2026", amount: "$99.00", status: "Paid" },
  { date: "Feb 1, 2026", amount: "$99.00", status: "Paid" },
  { date: "Jan 1, 2026", amount: "$99.00", status: "Paid" },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("Profile");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-display font-bold text-foreground">Settings</h1>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Sidebar tabs */}
        <div className="lg:w-56 shrink-0">
          <div className="glass-card rounded-xl p-2 space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.label}
                onClick={() => setActiveTab(tab.label)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.label ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                }`}
              >
                <tab.icon className="w-4 h-4" /> {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <motion.div key={activeTab} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="flex-1 glass-card rounded-xl p-6">
          {activeTab === "Profile" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Profile Settings</h2>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-full gradient-primary flex items-center justify-center text-xl font-bold text-primary-foreground">JD</div>
                <Button variant="outline" size="sm">Change Avatar</Button>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                {[
                  { label: "Full Name", value: "John Doe" },
                  { label: "Email", value: "john@company.com" },
                  { label: "Company", value: "Acme Corp" },
                  { label: "Role", value: "Sales Director" },
                ].map((field) => (
                  <div key={field.label}>
                    <label className="text-sm font-medium text-foreground block mb-1.5">{field.label}</label>
                    <input defaultValue={field.value} className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary" />
                  </div>
                ))}
              </div>
              <Button variant="gradient"><Save className="w-4 h-4" /> Save Changes</Button>
            </div>
          )}

          {activeTab === "Connected Accounts" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Connected Accounts</h2>
              {[
                { name: "Gmail", email: "john@company.com", connected: true, lastSync: "2 min ago" },
                { name: "Outlook", email: "", connected: false },
                { name: "LinkedIn", email: "Premium account", connected: true, lastSync: "5 min ago" },
              ].map((acc) => (
                <div key={acc.name} className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50">
                  <div>
                    <h3 className="font-medium text-foreground">{acc.name}</h3>
                    <p className="text-xs text-muted-foreground">{acc.connected ? `${acc.email} • Last synced ${acc.lastSync}` : "Not connected"}</p>
                  </div>
                  <Button variant={acc.connected ? "outline" : "gradient"} size="sm">
                    {acc.connected ? "Disconnect" : "Connect"}
                  </Button>
                </div>
              ))}
            </div>
          )}

          {activeTab === "Sending Limits" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Sending Limits</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">Daily Email Limit</label>
                  <input type="range" min={1} max={200} defaultValue={80} className="w-full accent-primary" />
                  <p className="text-xs text-muted-foreground mt-1">80 emails/day</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground block mb-2">Daily LinkedIn Limit</label>
                  <input type="range" min={1} max={100} defaultValue={30} className="w-full accent-primary" />
                  <p className="text-xs text-muted-foreground mt-1">30 messages/day</p>
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50">
                  <div>
                    <p className="font-medium text-foreground text-sm">Warm-up Mode</p>
                    <p className="text-xs text-muted-foreground">Gradually increase sending volume</p>
                  </div>
                  <Switch />
                </div>
              </div>
            </div>
          )}

          {activeTab === "Notifications" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Notification Preferences</h2>
              {[
                "Email when prospect replies",
                "Daily campaign summary",
                "Hot lead alert",
                "Weekly AI insights report",
                "Campaign completed alert",
              ].map((n) => (
                <div key={n} className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50">
                  <span className="text-sm text-foreground">{n}</span>
                  <Switch defaultChecked />
                </div>
              ))}
            </div>
          )}

          {activeTab === "Billing" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Billing</h2>
              <div className="rounded-lg gradient-primary p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-display font-bold text-primary-foreground text-lg">Pro Plan</h3>
                    <p className="text-primary-foreground/80 text-sm">$99/month • Renews Apr 1, 2026</p>
                  </div>
                  <Button className="bg-background/20 text-primary-foreground border border-primary-foreground/20 hover:bg-background/30">Upgrade</Button>
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  { label: "Prospects", used: "3,240", limit: "5,000" },
                  { label: "Emails", used: "6,800", limit: "10,000" },
                  { label: "Campaigns", used: "5", limit: "∞" },
                ].map((u) => (
                  <div key={u.label} className="text-center p-4 rounded-lg bg-muted/30 border border-border/50">
                    <div className="text-sm font-medium text-foreground">{u.used} / {u.limit}</div>
                    <div className="text-xs text-muted-foreground">{u.label}</div>
                  </div>
                ))}
              </div>
              <div>
                <h3 className="font-medium text-foreground mb-3 text-sm">Invoice History</h3>
                <div className="space-y-2">
                  {invoices.map((inv) => (
                    <div key={inv.date} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                      <span className="text-sm text-foreground">{inv.date}</span>
                      <span className="text-sm text-foreground">{inv.amount}</span>
                      <span className="text-xs text-success">{inv.status}</span>
                      <Button variant="ghost" size="sm" className="text-xs">Download</Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
