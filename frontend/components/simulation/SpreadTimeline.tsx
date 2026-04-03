"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { useSimulationStore } from "@/stores/simulationStore";
import { SMIR_COLORS } from "@/lib/types";

const LABELS: Record<string, string> = {
  S: "Susceptible",
  M: "Misinformed",
  I: "Informed",
  R: "Resistant",
};

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card border border-border rounded-lg px-3 py-2 text-xs space-y-1 min-w-[140px]">
      <p className="font-mono text-muted-foreground">Tick {label}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
            {LABELS[entry.dataKey] ?? entry.dataKey}
          </span>
          <span className="font-mono font-medium" style={{ color: entry.color }}>
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export function SpreadTimeline() {
  const tickHistory = useSimulationStore((s) => s.tickHistory);

  const data = tickHistory
    .filter((t) => t.state_counts != null)
    .map((t) => ({
      tick: t.tick,
      S: t.state_counts.S,
      M: t.state_counts.M,
      I: t.state_counts.I,
      R: t.state_counts.R,
    }));

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <defs>
            <linearGradient id="gradS" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SMIR_COLORS.S} stopOpacity={0.3} />
              <stop offset="100%" stopColor={SMIR_COLORS.S} stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="gradM" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SMIR_COLORS.M} stopOpacity={0.3} />
              <stop offset="100%" stopColor={SMIR_COLORS.M} stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="gradI" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SMIR_COLORS.I} stopOpacity={0.3} />
              <stop offset="100%" stopColor={SMIR_COLORS.I} stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="gradR" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SMIR_COLORS.R} stopOpacity={0.2} />
              <stop offset="100%" stopColor={SMIR_COLORS.R} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
          <XAxis
            dataKey="tick"
            stroke="rgba(255,255,255,0.2)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="rgba(255,255,255,0.2)"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            width={35}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(255,255,255,0.1)" }} />
          <Area type="monotone" dataKey="S" stroke={SMIR_COLORS.S} fill="url(#gradS)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="M" stroke={SMIR_COLORS.M} fill="url(#gradM)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="I" stroke={SMIR_COLORS.I} fill="url(#gradI)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="R" stroke={SMIR_COLORS.R} fill="url(#gradR)" strokeWidth={1.5} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
