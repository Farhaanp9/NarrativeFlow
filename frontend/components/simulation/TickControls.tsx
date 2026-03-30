"use client";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
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
    togglePause();
    sendMessage?.(
      JSON.stringify({ action: isPaused ? "resume" : "pause" })
    );
  };

  const handleSpeedChange = (value: number | readonly number[]) => {
    const newSpeed = Array.isArray(value) ? value[0] : value;
    setSpeed(newSpeed);
    sendMessage?.(
      JSON.stringify({ action: "set_speed", value: newSpeed })
    );
  };

  return (
    <div className="flex items-center gap-4">
      <Button
        variant="outline"
        size="sm"
        onClick={handlePauseToggle}
        disabled={!isRunning}
      >
        {isPaused ? "Resume" : "Pause"}
      </Button>

      <div className="flex items-center gap-2 flex-1">
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          Speed:
        </span>
        <Slider
          value={[speed]}
          onValueChange={handleSpeedChange}
          min={1}
          max={50}
          step={1}
          className="flex-1"
        />
        <span className="text-xs font-mono w-8 text-right">{speed}x</span>
      </div>

      <span className="text-sm font-mono text-muted-foreground whitespace-nowrap">
        Tick {currentTick}
      </span>
    </div>
  );
}
