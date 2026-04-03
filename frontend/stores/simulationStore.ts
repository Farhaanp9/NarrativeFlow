import { create } from "zustand";
import type {
  GraphEdge,
  GraphNode,
  SimulationStatus,
  TickData,
} from "@/lib/types";

interface SimulationState {
  simulationId: string | null;
  status: SimulationStatus;

  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];

  currentTick: number;
  stateCounts: { S: number; M: number; I: number; R: number };
  spreadRate: number;
  peakVelocity: number;
  activeNarratives: number;
  nodeStates: Record<string, string>;

  tickHistory: TickData[];

  isPaused: boolean;
  speed: number;

  setSimulation: (id: string) => void;
  setGraphData: (nodes: GraphNode[], edges: GraphEdge[]) => void;
  appendTick: (tick: TickData) => void;
  setNodeStates: (states: Record<string, string>) => void;
  loadMetricsHistory: (ticks: TickData[]) => void;
  setStatus: (status: SimulationStatus) => void;
  togglePause: () => void;
  setSpeed: (speed: number) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationState>((set) => ({
  simulationId: null,
  status: "initializing",

  graphNodes: [],
  graphEdges: [],

  currentTick: 0,
  stateCounts: { S: 0, M: 0, I: 0, R: 0 },
  spreadRate: 0,
  peakVelocity: 0,
  activeNarratives: 0,
  nodeStates: {},

  tickHistory: [],

  isPaused: false,
  speed: 5,

  setSimulation: (id) => set({ simulationId: id }),

  setGraphData: (nodes, edges) => set({ graphNodes: nodes, graphEdges: edges }),

  appendTick: (tick) =>
    set((state) => ({
      currentTick: tick.tick,
      stateCounts: tick.state_counts,
      spreadRate: tick.spread_rate,
      peakVelocity: tick.peak_velocity,
      activeNarratives: tick.active_narratives,
      nodeStates: tick.node_states ?? state.nodeStates,
      tickHistory: [...state.tickHistory, tick],
    })),

  setNodeStates: (states) => set({ nodeStates: states }),

  loadMetricsHistory: (ticks) =>
    set(() => {
      const last = ticks[ticks.length - 1];
      return {
        tickHistory: ticks,
        currentTick: last?.tick ?? 0,
        stateCounts: last?.state_counts ?? { S: 0, M: 0, I: 0, R: 0 },
        spreadRate: last?.spread_rate ?? 0,
        peakVelocity: last?.peak_velocity ?? 0,
        activeNarratives: last?.active_narratives ?? 0,
      };
    }),

  setStatus: (status) => set({ status }),

  togglePause: () => set((state) => ({ isPaused: !state.isPaused })),

  setSpeed: (speed) => set({ speed }),

  reset: () =>
    set({
      simulationId: null,
      status: "initializing",
      graphNodes: [],
      graphEdges: [],
      currentTick: 0,
      stateCounts: { S: 0, M: 0, I: 0, R: 0 },
      spreadRate: 0,
      peakVelocity: 0,
      activeNarratives: 0,
      nodeStates: {},
      tickHistory: [],
      isPaused: false,
      speed: 5,
    }),
}));
