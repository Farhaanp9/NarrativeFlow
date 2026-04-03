"use client";

import { Button } from "@/components/ui/button";
import { Pause, Play, SkipForward, Gauge } from "lucide-react";
import { useSimulationStore } from "@/stores/simulationStore";

interface TickControlsProps {
  sendMessage?: (msg: string) => void;
}

export function TickControls({ sendMessage }: TickControlsProps) {
  const currentTick = useSimulationStore((s) => s.currentTick);
  const isPaused = useSimulationStore((s) => s.isPaused);
  const speed = useSimulationStore((s) => s.speed);
  const status = useSimulationStore((s) => s.status);
  const togglePause = useSimulationStore((s) => s.togglePause);
  const setSpeed = useSimulationStore((s) => s.setSpeed);

  const isRunning = status === "running";

  const handlePauseToggle = () => {
    const action = isPaused ? "resume" : "pause";
    sendMessage?.(JSON.stringify({ action }));
    togglePause();
  };

  const handleStep = () => {
    sendMessage?.(JSON.stringify({ action: "step" }));
  };

  const handleSpeedChange = (value: number) => {
    sendMessage?.(JSON.stringify({ action: "set_speed", value }));
    setSpeed(value);
  };

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={handlePauseToggle}
        disabled={!isRunning}
        className="border-white/10 hover:bg-white/5 h-8 w-8 p-0"
      >
        {isPaused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={handleStep}
        disabled={!isRunning || !isPaused}
        className="border-white/10 hover:bg-white/5 h-8 w-8 p-0"
      >
        <SkipForward className="h-3.5 w-3.5" />
      </Button>

      <div className="flex items-center gap-2 flex-1 ml-2">
        <Gauge className="h-3.5 w-3.5 text-muted-foreground/50 shrink-0" />
        <input
          type="range"
          value={speed}
          onChange={(e) => handleSpeedChange(Number(e.target.value))}
          min={1}
          max={50}
          step={1}
          className="flex-1 h-1 appearance-none bg-white/10 rounded-full [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white cursor-pointer"
        />
        <span className="text-xs font-mono text-muted-foreground w-7 text-right">{speed}x</span>
      </div>

      <span className="text-xs font-mono text-foreground/80 whitespace-nowrap bg-white/5 rounded-md px-2 py-1">
        {currentTick}
      </span>
    </div>
  );
}
