"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useSimulationStore } from "@/stores/simulationStore";
import { SMIR_COLORS } from "@/lib/types";

export function SpreadTimeline() {
  const tickHistory = useSimulationStore((s) => s.tickHistory);

  const data = tickHistory.map((t) => ({
    tick: t.tick,
    S: t.state_counts.S,
    M: t.state_counts.M,
    I: t.state_counts.I,
    R: t.state_counts.R,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="tick"
            stroke="#94A3B8"
            fontSize={11}
            tickLine={false}
          />
          <YAxis stroke="#94A3B8" fontSize={11} tickLine={false} />
          <Legend
            wrapperStyle={{ fontSize: 12 }}
            formatter={(value: string) => {
              const labels: Record<string, string> = {
                S: "Susceptible",
                M: "Misinformed",
                I: "Informed",
                R: "Resistant",
              };
              return labels[value] ?? value;
            }}
          />
          <Line
            type="monotone"
            dataKey="S"
            stroke={SMIR_COLORS.S}
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="M"
            stroke={SMIR_COLORS.M}
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="I"
            stroke={SMIR_COLORS.I}
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="R"
            stroke={SMIR_COLORS.R}
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
