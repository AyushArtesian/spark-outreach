import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type FunnelStage = {
  key: string;
  label: string;
  count: number;
  colorClass?: string;
};

interface LeadHealthFunnelProps {
  stages: FunnelStage[];
  title?: string;
  subtitle?: string;
  className?: string;
}

const pct = (value: number) => `${value.toFixed(1)}%`;

export default function LeadHealthFunnel({
  stages,
  title = "Lead Health Funnel",
  subtitle = "Track drop-offs across your outreach pipeline",
  className,
}: LeadHealthFunnelProps) {
  return (
    <Card className={cn("border-border/50", className)}>
      <CardHeader>
        <CardTitle className="text-base font-display">{title}</CardTitle>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {stages.map((stage, index) => {
            const prev = stages[index - 1]?.count ?? 0;
            const conversionFromPrev = index === 0 ? 100 : prev > 0 ? (stage.count / prev) * 100 : 0;
            const dropOffFromPrev = index === 0 ? 0 : Math.max(0, 100 - conversionFromPrev);

            return (
              <div key={stage.key} className="rounded-xl border border-border/60 bg-muted/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-muted-foreground">{stage.label}</span>
                  <span className={cn("text-xs font-semibold", stage.colorClass || "text-foreground")}>
                    {stage.count.toLocaleString()}
                  </span>
                </div>
                <div className="mt-2 h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className={cn("h-full rounded-full", stage.colorClass ? stage.colorClass.replace("text-", "bg-") : "bg-primary")}
                    style={{
                      width: `${Math.min(100, Math.max(6, conversionFromPrev))}%`,
                    }}
                  />
                </div>
                <div className="mt-2 text-[11px] text-muted-foreground">
                  {index === 0 ? (
                    <span>Baseline</span>
                  ) : (
                    <span>
                      {pct(conversionFromPrev)} from previous • {pct(dropOffFromPrev)} drop-off
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
