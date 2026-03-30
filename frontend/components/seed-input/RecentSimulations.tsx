"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listSimulations } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import type { SimulationSummary } from "@/lib/types";

export function RecentSimulations() {
  const [simulations, setSimulations] = useState<SimulationSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSimulations()
      .then((data) => setSimulations(data.slice(0, 10)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return null;
  }

  if (simulations.length === 0) {
    return null;
  }

  const statusVariant = (status: string) => {
    if (status === "completed") return "secondary" as const;
    if (status === "running") return "default" as const;
    if (status === "failed") return "destructive" as const;
    return "outline" as const;
  };

  return (
    <div className="w-full max-w-2xl space-y-3">
      <h2 className="text-sm font-medium text-muted-foreground">
        Recent Simulations
      </h2>
      <div className="space-y-2">
        {simulations.map((sim) => (
          <Link
            key={sim.id}
            href={
              sim.status === "completed"
                ? `/reports/${sim.id}`
                : `/simulation/${sim.id}`
            }
            className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{sim.seed_text}</p>
              <p className="text-xs text-muted-foreground font-mono">
                {sim.population_size} agents &middot; {sim.topology} &middot;
                tick {sim.current_tick}
              </p>
            </div>
            <Badge variant={statusVariant(sim.status)}>{sim.status}</Badge>
          </Link>
        ))}
      </div>
    </div>
  );
}
