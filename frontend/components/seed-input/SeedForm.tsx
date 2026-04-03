"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Play, Loader2 } from "lucide-react";
import { ConfigPanel } from "./ConfigPanel";
import { createSimulation } from "@/lib/api";
import type { Topology } from "@/lib/types";

const VALID_TOPOLOGIES: Topology[] = [
  "barabasi_albert",
  "watts_strogatz",
  "stochastic_block_model",
];

export function SeedForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Pre-fill from query params (used by "Run Again" button)
  const [seedText, setSeedText] = useState(
    searchParams.get("seed_text") ?? ""
  );
  const [populationSize, setPopulationSize] = useState(
    Number(searchParams.get("population_size")) || 500
  );
  const rawTopo = searchParams.get("topology") ?? "barabasi_albert";
  const [topology, setTopology] = useState<Topology>(
    VALID_TOPOLOGIES.includes(rawTopo as Topology)
      ? (rawTopo as Topology)
      : "barabasi_albert"
  );
  const [maxTicks, setMaxTicks] = useState(
    Number(searchParams.get("max_ticks")) || 100
  );
  const [archetypeCount, setArchetypeCount] = useState(
    Number(searchParams.get("archetype_count")) || 15
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!seedText.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const { id } = await createSimulation({
        seed_text: seedText.trim(),
        population_size: populationSize,
        topology,
        archetype_count: archetypeCount,
        max_ticks: maxTicks,
        tick_speed: 5,
      });
      router.push(`/simulation/${id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create simulation"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl bg-card rounded-2xl border border-border p-6 space-y-5">
      <div>
        <h2 className="text-lg font-semibold">Seed a Simulation</h2>
        <p className="text-sm text-muted-foreground">Describe a scenario to simulate</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Textarea
          placeholder='Enter a headline, claim, or event (e.g., "New study links popular sweetener to cancer risk")'
          value={seedText}
          onChange={(e) => setSeedText(e.target.value)}
          rows={3}
          className="resize-none"
        />

        <ConfigPanel
          populationSize={populationSize}
          setPopulationSize={setPopulationSize}
          topology={topology}
          setTopology={setTopology}
          maxTicks={maxTicks}
          setMaxTicks={setMaxTicks}
          archetypeCount={archetypeCount}
          setArchetypeCount={setArchetypeCount}
        />

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button
          type="submit"
          disabled={!seedText.trim() || loading}
          className="w-full h-10 bg-white text-black font-medium hover:bg-white/90 transition-colors cursor-pointer"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Initializing Simulation...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Run Simulation
            </>
          )}
        </Button>
      </form>
    </div>
  );
}
