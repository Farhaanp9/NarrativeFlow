"use client";

import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { TOPOLOGY_LABELS, type Topology } from "@/lib/types";

interface ConfigPanelProps {
  populationSize: number;
  setPopulationSize: (v: number) => void;
  topology: Topology;
  setTopology: (v: Topology) => void;
  maxTicks: number;
  setMaxTicks: (v: number) => void;
  archetypeCount: number;
  setArchetypeCount: (v: number) => void;
}

export function ConfigPanel({
  populationSize,
  setPopulationSize,
  topology,
  setTopology,
  maxTicks,
  setMaxTicks,
  archetypeCount,
  setArchetypeCount,
}: ConfigPanelProps) {
  return (
    <Collapsible defaultOpen={false}>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-md px-4 py-2 text-sm text-muted-foreground hover:bg-accent">
        Advanced Configuration
        <span className="text-xs">click to expand</span>
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-4 pt-4">
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            Population Size: {populationSize}
          </label>
          <Slider
            value={[populationSize]}
            onValueChange={(v) => setPopulationSize(Array.isArray(v) ? v[0] : v)}
            min={50}
            max={5000}
            step={50}
          />
        </div>

        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            Network Topology
          </label>
          <Select value={topology} onValueChange={(v) => setTopology(v as Topology)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(TOPOLOGY_LABELS).map(([value, label]) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            Simulation Duration: {maxTicks} ticks
          </label>
          <Slider
            value={[maxTicks]}
            onValueChange={(v) => setMaxTicks(Array.isArray(v) ? v[0] : v)}
            min={50}
            max={500}
            step={10}
          />
        </div>

        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            Archetype Count: {archetypeCount}
          </label>
          <Slider
            value={[archetypeCount]}
            onValueChange={(v) => setArchetypeCount(Array.isArray(v) ? v[0] : v)}
            min={5}
            max={30}
            step={1}
          />
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
