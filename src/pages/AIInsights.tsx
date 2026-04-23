import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, BarChart3, TrendingUp, Target, Zap, ChevronRight, Loader } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { aiAPI } from "@/services/api";
import { toast } from "@/hooks/use-toast";

interface InsightsData {
  insights: string;
  recommendations: string[];
  metrics: {
    total_leads: number;
    hot_leads: number;
    conversion_rate: number;
    contacted?: number;
    converted?: number;
    top_industries?: Array<{ name: string; count: number }>;
  };
  model?: string;
}

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function AIInsights() {
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<InsightsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadInsights = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await aiAPI.generateInsights();
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to generate insights";
      setError(message);
      toast({
        title: "Error",
        description: message,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-display font-bold text-foreground flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-primary" />
            AI Intelligence
          </h1>
          <p className="text-muted-foreground text-sm mt-2">
            Data-driven insights and recommendations to improve your lead generation strategy
          </p>
        </div>
        <Button onClick={loadInsights} disabled={isLoading} className="gap-2">
          {isLoading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" /> Generating...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" /> Regenerate Insights
            </>
          )}
        </Button>
      </div>

      {error ? (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="p-6">
            <p className="text-destructive font-medium">{error}</p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Analyzing your lead data with AI...</p>
          </div>
        </div>
      ) : data ? (
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
          {/* Key Metrics */}
          <motion.div variants={item}>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: "Total Leads", value: data.metrics.total_leads, icon: Target, color: "text-primary" },
                { label: "Hot Leads", value: data.metrics.hot_leads, icon: TrendingUp, color: "text-warning" },
                { label: "Conversion Rate", value: `${data.metrics.conversion_rate}%`, icon: BarChart3, color: "text-success" },
                { label: "Contacted", value: data.metrics.contacted || 0, icon: Zap, color: "text-accent" },
              ].map((m) => (
                <Card key={m.label} className="border-border/50">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <m.icon className={`w-5 h-5 ${m.color}`} />
                    </div>
                    <div className="text-2xl font-display font-bold text-foreground">{m.value}</div>
                    <div className="text-xs text-muted-foreground mt-1">{m.label}</div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </motion.div>

          {/* Top Industries */}
          {data.metrics.top_industries && data.metrics.top_industries.length > 0 && (
            <motion.div variants={item}>
              <Card className="border-border/50">
                <CardHeader>
                  <CardTitle className="text-base font-display">Top Industries</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {data.metrics.top_industries.map((ind) => (
                    <div key={ind.name} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                      <span className="text-sm font-medium text-foreground">{ind.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{
                              width: `${Math.min((ind.count / (data.metrics.top_industries?.[0]?.count || 1)) * 100, 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-foreground w-8 text-right">{ind.count}</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Main Insights */}
          <motion.div variants={item}>
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader>
                <CardTitle className="text-lg font-display flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  AI-Generated Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.insights.split('\n\n').map((section, idx) => (
                    <div key={idx} className="text-sm leading-relaxed">
                      {section.split('\n').map((line, lineIdx) => {
                        const trimmed = line.trim();
                        if (!trimmed) return null;

                        // Heading (###)
                        if (trimmed.startsWith('###')) {
                          return (
                            <h3 key={lineIdx} className="font-semibold text-foreground text-base mt-3 mb-2">
                              {trimmed.replace(/^#+\s*/, '')}
                            </h3>
                          );
                        }

                        // Subheading (##)
                        if (trimmed.startsWith('##')) {
                          return (
                            <h4 key={lineIdx} className="font-semibold text-foreground/90 text-sm mt-2 mb-1">
                              {trimmed.replace(/^#+\s*/, '')}
                            </h4>
                          );
                        }

                        // Bold text (**)
                        if (trimmed.includes('**')) {
                          return (
                            <p key={lineIdx} className="text-foreground/80">
                              {trimmed.split(/\*\*(.+?)\*\*/g).map((part, i) =>
                                i % 2 === 1 ? (
                                  <strong key={i}>{part}</strong>
                                ) : (
                                  part
                                )
                              )}
                            </p>
                          );
                        }

                        // Bulleted list
                        if (trimmed.startsWith('-') || trimmed.startsWith('•')) {
                          return (
                            <li key={lineIdx} className="text-foreground/80 ml-4 list-disc">
                              {trimmed.replace(/^[-•]\s*/, '')}
                            </li>
                          );
                        }

                        // Numbered list
                        if (/^\d+\./.test(trimmed)) {
                          return (
                            <li key={lineIdx} className="text-foreground/80 ml-4 list-decimal">
                              {trimmed.replace(/^\d+\.\s*/, '')}
                            </li>
                          );
                        }

                        // Regular paragraph
                        return (
                          <p key={lineIdx} className="text-foreground/80">
                            {trimmed}
                          </p>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <motion.div variants={item}>
              <Card className="border-success/20 bg-success/5">
                <CardHeader>
                  <CardTitle className="text-lg font-display flex items-center gap-2">
                    <Target className="w-5 h-5 text-success" />
                    Recommended Actions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {data.recommendations && data.recommendations.length > 0 ? (
                      data.recommendations.map((rec, idx) => {
                        // Clean up the recommendation text
                        let cleanRec = typeof rec === 'string' ? rec : '';
                        cleanRec = cleanRec.replace(/^[-•*]\s*/, '');
                        cleanRec = cleanRec.replace(/^\d+\.\s*/, '');
                        cleanRec = cleanRec.replace(/^#+\s*/, '');
                        
                        return (
                          <motion.div
                            key={idx}
                            variants={item}
                            className="flex gap-3 p-3 rounded-lg bg-background/50 hover:bg-background transition-colors"
                          >
                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-success/20 flex items-center justify-center text-success font-semibold text-xs">
                              {idx + 1}
                            </div>
                            <div className="flex-1">
                              <p className="text-sm text-foreground/90">{cleanRec}</p>
                            </div>
                          </motion.div>
                        );
                      })
                    ) : (
                      <p className="text-sm text-foreground/60">Loading recommendations...</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Call to Action */}
          <motion.div variants={item}>
            <div className="grid sm:grid-cols-2 gap-4">
              <Link to="/search">
                <Button variant="outline" className="w-full h-auto py-3 gap-2">
                  <Target className="w-4 h-4" />
                  <span>New Lead Search</span>
                </Button>
              </Link>
              <Link to="/all-leads">
                <Button className="w-full h-auto py-3 gap-2">
                  <ArrowRight className="w-4 h-4" />
                  <span>View All Leads</span>
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Footer */}
          {data.model && (
            <motion.div variants={item}>
              <div className="text-xs text-muted-foreground text-center pt-4">
                <p>Powered by {data.model}</p>
              </div>
            </motion.div>
          )}
        </motion.div>
      ) : (
        <Card className="border-border/50">
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">No insights available. Please search for leads first.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
