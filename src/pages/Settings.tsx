import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { User, Link2, Save, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { companyAPI } from "@/services/api";

const tabs = [
  { label: "Profile", icon: User },
  { label: "Connected Accounts", icon: Link2 },
  { label: "Embedding Test", icon: Sparkles },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("Profile");
  const [profileData, setProfileData] = useState({
    full_name: "",
    email: "",
    username: "",
  });
  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState(3);
  const [queryResults, setQueryResults] = useState<Array<{ index: number; score: number; chunk: string }>>([]);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData({
        full_name: user.full_name || "",
        email: user.email || "",
        username: user.username || "",
      });
    }
  }, [user]);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const handleQuerySubmit = async () => {
    if (!queryText.trim()) {
      setQueryError("Please enter a question to test the embeddings.");
      return;
    }

    setQueryError(null);
    setQueryLoading(true);
    setQueryResults([]);

    try {
      const result = await companyAPI.queryProfile(queryText, topK);
      setQueryResults(result.results || []);
    } catch (error: any) {
      setQueryError(error?.message || "Something went wrong while querying the company embeddings.");
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-display font-bold text-foreground">Settings</h1>

      <div className="flex flex-col lg:flex-row gap-6">
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

        <motion.div key={activeTab} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="flex-1 glass-card rounded-xl p-6">
          {activeTab === "Profile" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Personal Information</h2>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-full gradient-primary flex items-center justify-center text-xl font-bold text-primary-foreground">
                  {getInitials(profileData.full_name)}
                </div>
                <Button variant="outline" size="sm">Change Avatar</Button>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Full Name</label>
                  <input
                    type="text"
                    value={profileData.full_name}
                    onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                    className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Email</label>
                  <input
                    type="email"
                    value={profileData.email}
                    readOnly
                    className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary opacity-60 cursor-not-allowed"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-foreground block mb-1.5">Username</label>
                  <input
                    type="text"
                    value={profileData.username}
                    readOnly
                    className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary opacity-60 cursor-not-allowed"
                  />
                </div>
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
                    <p className="text-xs text-muted-foreground">{acc.connected ? `${acc.email} - Last synced ${acc.lastSync}` : "Not connected"}</p>
                  </div>
                  <Button variant={acc.connected ? "outline" : "gradient"} size="sm">
                    {acc.connected ? "Disconnect" : "Connect"}
                  </Button>
                </div>
              ))}
            </div>
          )}

          {activeTab === "Embedding Test" && (
            <div className="space-y-6">
              <h2 className="font-display font-semibold text-foreground">Embedding Test</h2>
              <p className="text-sm text-muted-foreground">Ask a question about your company profile and see if the embedding system returns the most relevant context.</p>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-foreground block mb-1.5">Test Question</label>
                  <textarea
                    rows={4}
                    value={queryText}
                    onChange={(e) => setQueryText(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    placeholder="What services do we offer in Microsoft Power Platform?"
                  />
                </div>
                <div className="grid sm:grid-cols-2 gap-4 items-end">
                  <div>
                    <label className="text-sm font-medium text-foreground block mb-1.5">Top results</label>
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={topK}
                      onChange={(e) => setTopK(Number(e.target.value))}
                      className="w-full h-10 px-4 rounded-lg bg-muted/50 border border-border text-foreground text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  </div>
                  <Button disabled={queryLoading} onClick={handleQuerySubmit}>
                    {queryLoading ? "Testing..." : "Run embedding test"}
                  </Button>
                </div>
                {queryError && <div className="text-sm text-destructive">{queryError}</div>}
                {queryResults.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="font-medium text-foreground">Top matching snippets</h3>
                    <div className="space-y-3">
                      {queryResults.map((result) => (
                        <div key={result.index} className="p-4 rounded-lg bg-muted/30 border border-border/50">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-foreground">Chunk {result.index + 1}</span>
                            <span className="text-xs text-muted-foreground">Score: {result.score.toFixed(3)}</span>
                          </div>
                          <p className="text-sm text-foreground leading-6">{result.chunk}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
