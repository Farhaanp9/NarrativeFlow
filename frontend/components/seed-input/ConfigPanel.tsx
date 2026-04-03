"use client";

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
import { Settings2, ChevronDown } from "lucide-react";
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
      <CollapsibleTrigger className="group flex w-full items-center justify-between rounded-md px-4 py-2 text-sm text-muted-foreground hover:bg-white/5 transition-colors">
        <span className="flex items-center gap-2">
          <Settings2 className="h-4 w-4" />
          Advanced Configuration
        </span>
        <ChevronDown className="h-4 w-4 transition-transform group-data-[state=open]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-4 pt-4">
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            Population Size: {populationSize}
          </label>
          <input
            type="range"
            value={populationSize}
            onChange={(e) => setPopulationSize(Number(e.target.value))}
            min={50}
            max={5000}
            step={50}
            className="w-full h-1 appearance-none bg-white/10 rounded-full [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white cursor-pointer"
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
          <input
            type="range"
            value={maxTicks}
            onChange={(e) => setMaxTicks(Number(e.target.value))}
            min={50}
            max={500}
            step={10}
            className="w-full h-1 appearance-none bg-white/10 rounded-full [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white cursor-pointer"
          />
        </div>

        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            Archetype Count: {archetypeCount}
          </label>
          <input
            type="range"
            value={archetypeCount}
            onChange={(e) => setArchetypeCount(Number(e.target.value))}
            min={5}
            max={30}
            step={1}
            className="w-full h-1 appearance-none bg-white/10 rounded-full [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white cursor-pointer"
          />
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
