"use client";

import { useSimulationStore } from "@/stores/simulationStore";
import { SMIR_COLORS } from "@/lib/types";

export function MetricsBar() {
  const stateCounts = useSimulationStore((s) => s.stateCounts);
  const spreadRate = useSimulationStore((s) => s.spreadRate);
  const peakVelocity = useSimulationStore((s) => s.peakVelocity);
  const activeNarratives = useSimulationStore((s) => s.activeNarratives);

  const total = stateCounts.S + stateCounts.M + stateCounts.I + stateCounts.R;

  return (
    <div className="grid grid-cols-2 gap-3">
      <MetricCard
        label="Susceptible"
        value={stateCounts.S}
        pct={total > 0 ? ((stateCounts.S / total) * 100).toFixed(1) : "0"}
        color={SMIR_COLORS.S}
      />
      <MetricCard
        label="Misinformed"
        value={stateCounts.M}
        pct={total > 0 ? ((stateCounts.M / total) * 100).toFixed(1) : "0"}
        color={SMIR_COLORS.M}
      />
      <MetricCard
        label="Informed"
        value={stateCounts.I}
        pct={total > 0 ? ((stateCounts.I / total) * 100).toFixed(1) : "0"}
        color={SMIR_COLORS.I}
      />
      <MetricCard
        label="Resistant"
        value={stateCounts.R}
        pct={total > 0 ? ((stateCounts.R / total) * 100).toFixed(1) : "0"}
        color={SMIR_COLORS.R}
      />
      <MetricCard
        label="Spread Rate"
        value={spreadRate.toFixed(4)}
        color="#F1F5F9"
      />
      <MetricCard
        label="Peak Velocity"
        value={peakVelocity.toFixed(4)}
        color="#F1F5F9"
      />
      <MetricCard
        label="Active Narratives"
        value={activeNarratives}
        color="#F1F5F9"
      />
    </div>
  );
}

function MetricCard({
  label,
  value,
  pct,
  color,
}: {
  label: string;
  value: number | string;
  pct?: string;
  color: string;
}) {
  return (
    <div className="bg-card rounded-lg p-3 border border-border">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-mono font-semibold" style={{ color }}>
        {value}
        {pct && <span className="text-xs text-muted-foreground ml-1">({pct}%)</span>}
      </p>
    </div>
  );
}
