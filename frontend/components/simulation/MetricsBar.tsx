"use client";

import { TrendingUp, Zap, MessageSquare } from "lucide-react";
import { useSimulationStore } from "@/stores/simulationStore";
import { SMIR_COLORS } from "@/lib/types";

function formatRate(value: number): string {
  if (value === 0) return "0";
  if (value < 0.01) return value.toExponential(1);
  if (value < 1) return value.toFixed(2);
  return value.toFixed(1);
}

function SmirStackedBar({ stateCounts, total }: { stateCounts: { S: number; M: number; I: number; R: number }; total: number }) {
  if (total === 0) return null;
  const segments = [
    { key: "S", color: SMIR_COLORS.S, value: stateCounts.S },
    { key: "M", color: SMIR_COLORS.M, value: stateCounts.M },
    { key: "I", color: SMIR_COLORS.I, value: stateCounts.I },
    { key: "R", color: SMIR_COLORS.R, value: stateCounts.R },
  ];
  return (
    <div className="flex h-2 w-full rounded-full overflow-hidden bg-white/5">
      {segments.map((seg) => (
        <div
          key={seg.key}
          className="h-full transition-all duration-500 ease-out first:rounded-l-full last:rounded-r-full"
          style={{ width: `${(seg.value / total) * 100}%`, backgroundColor: seg.color }}
        />
      ))}
    </div>
  );
}

function SmirCard({
  label,
  value,
  total,
  color,
  borderClass,
}: {
  label: string;
  value: number;
  total: number;
  color: string;
  borderClass: string;
}) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className={`bg-card border border-border rounded-xl p-3 ${borderClass}`}>
      <div className="flex items-center justify-between mb-1.5">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-xs font-mono text-muted-foreground/60">{pct.toFixed(1)}%</p>
      </div>
      <p className="text-xl font-mono font-semibold mb-2" style={{ color }}>
        {value.toLocaleString()}
      </p>
      <div className="h-1 w-full rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function DerivedMetricCard({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-card border border-border rounded-xl p-2.5 text-center">
      <div className="flex items-center justify-center gap-1 mb-1">
        {icon}
        <p className="text-[10px] text-muted-foreground">{label}</p>
      </div>
      <p className="text-base font-mono font-semibold text-foreground">{value}</p>
    </div>
  );
}

export function MetricsBar() {
  const stateCounts = useSimulationStore((s) => s.stateCounts);
  const spreadRate = useSimulationStore((s) => s.spreadRate);
  const peakVelocity = useSimulationStore((s) => s.peakVelocity);
  const activeNarratives = useSimulationStore((s) => s.activeNarratives);

  const total = stateCounts.S + stateCounts.M + stateCounts.I + stateCounts.R;

  return (
    <div className="space-y-4">
      <SmirStackedBar stateCounts={stateCounts} total={total} />
      <div className="grid grid-cols-2 gap-2.5">
        <SmirCard label="Susceptible" value={stateCounts.S} total={total} color={SMIR_COLORS.S} borderClass="smir-border-s" />
        <SmirCard label="Misinformed" value={stateCounts.M} total={total} color={SMIR_COLORS.M} borderClass="smir-border-m" />
        <SmirCard label="Informed" value={stateCounts.I} total={total} color={SMIR_COLORS.I} borderClass="smir-border-i" />
        <SmirCard label="Resistant" value={stateCounts.R} total={total} color={SMIR_COLORS.R} borderClass="smir-border-r" />
      </div>
      <div className="grid grid-cols-3 gap-2.5">
        <DerivedMetricCard label="Spread Rate" value={formatRate(spreadRate)} icon={<TrendingUp className="h-3.5 w-3.5 text-muted-foreground/50" />} />
        <DerivedMetricCard label="Peak Velocity" value={formatRate(peakVelocity)} icon={<Zap className="h-3.5 w-3.5 text-muted-foreground/50" />} />
        <DerivedMetricCard label="Narratives" value={String(activeNarratives)} icon={<MessageSquare className="h-3.5 w-3.5 text-muted-foreground/50" />} />
      </div>
    </div>
  );
}
