import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  accent = "default",
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: "default" | "amber" | "cyan" | "danger";
}) {
  const accentColor = {
    default: "text-[var(--color-text-secondary)]",
    amber: "text-[var(--color-amber)]",
    cyan: "text-[var(--color-cyan)]",
    danger: "text-[var(--color-danger)]",
  }[accent];

  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">{label}</p>
          <p className="mt-2 font-mono text-3xl font-medium">{value}</p>
        </div>
        <div className={cn("rounded-md bg-[var(--color-surface-raised)] p-2", accentColor)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </Card>
  );
}
