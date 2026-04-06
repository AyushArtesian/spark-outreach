import { useState } from "react";
import { motion } from "framer-motion";
import { User, Bell, Shield, Mail, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const tabs = [
  { id: "profile", label: "Profile", icon: User },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "integrations", label: "Integrations", icon: Mail },
];

const notifications = [
  { label: "New high-priority lead found", desc: "Get notified when AI finds a lead scoring 8+", default: true },
  { label: "Daily lead digest", desc: "Summary of new leads each morning", default: true },
  { label: "Lead status changes", desc: "When a contacted lead responds", default: false },
  { label: "Weekly AI insights", desc: "AI performance and market trends report", default: true },
  { label: "Search completed", desc: "When a lead search finishes processing", default: true },
];

export default function LeadSettings() {
  const [activeTab, setActiveTab] = useState("profile");
  const [notifState, setNotifState] = useState(notifications.map((n) => n.default));

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">Manage your account and preferences</p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar Tabs */}
        <div className="md:w-48 shrink-0">
          <nav className="flex md:flex-col gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-left",
                  activeTab === tab.id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
              >
                <tab.icon className="w-4 h-4" /> {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-6">
          {activeTab === "profile" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <Card className="border-border/50 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base font-display">Personal Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center text-xl font-bold text-primary-foreground">JD</div>
                    <Button variant="outline" size="sm">Change Avatar</Button>
                  </div>
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div><label className="text-sm font-medium text-foreground mb-1.5 block">Full Name</label><Input defaultValue="John Doe" /></div>
                    <div><label className="text-sm font-medium text-foreground mb-1.5 block">Email</label><Input defaultValue="john@acmesoftware.com" /></div>
                    <div><label className="text-sm font-medium text-foreground mb-1.5 block">Company</label><Input defaultValue="Acme Software Solutions" /></div>
                    <div><label className="text-sm font-medium text-foreground mb-1.5 block">Role</label><Input defaultValue="Founder & CEO" /></div>
                  </div>
                  <div className="flex justify-end">
                    <Button className="gap-2" onClick={() => toast({ title: "Profile updated!" })}><Save className="w-4 h-4" /> Save Changes</Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {activeTab === "notifications" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Card className="border-border/50 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base font-display">Notification Preferences</CardTitle>
                  <CardDescription>Choose what you'd like to be notified about</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {notifications.map((n, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/30 transition-colors">
                      <div>
                        <div className="text-sm font-medium text-foreground">{n.label}</div>
                        <div className="text-xs text-muted-foreground">{n.desc}</div>
                      </div>
                      <Switch checked={notifState[i]} onCheckedChange={(v) => { const s = [...notifState]; s[i] = v; setNotifState(s); }} />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {activeTab === "integrations" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              {[
                { name: "Gmail", desc: "Send outreach emails directly", connected: true },
                { name: "LinkedIn", desc: "Import prospect data", connected: true },
                { name: "Slack", desc: "Get lead notifications in Slack", connected: false },
                { name: "HubSpot CRM", desc: "Sync leads to your CRM", connected: false },
              ].map((int) => (
                <Card key={int.name} className="border-border/50 shadow-sm">
                  <CardContent className="p-4 flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-foreground">{int.name}</div>
                      <div className="text-xs text-muted-foreground">{int.desc}</div>
                    </div>
                    {int.connected ? (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-success font-medium">Connected</span>
                        <Button variant="outline" size="sm">Disconnect</Button>
                      </div>
                    ) : (
                      <Button variant="default" size="sm">Connect</Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
