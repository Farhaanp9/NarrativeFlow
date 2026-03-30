export type SimulationStatus =
  | "initializing"
  | "running"
  | "completed"
  | "failed"
  | "paused";

export type Topology =
  | "barabasi_albert"
  | "watts_strogatz"
  | "stochastic_block_model";

export interface TopologyParams {
  m?: number;
  k?: number;
  p_rewire?: number;
  n_communities?: number;
  p_within?: number;
  p_between?: number;
}

export interface SimulationCreateRequest {
  seed_text: string;
  population_size: number;
  topology: Topology;
  topology_params?: TopologyParams;
  archetype_count: number;
  max_ticks: number;
  tick_speed: number;
}

export interface SimulationSummary {
  id: string;
  status: SimulationStatus;
  seed_text: string;
  population_size: number;
  topology: string;
  current_tick: number;
  created_at: string;
}

export interface SimulationDetail extends SimulationSummary {
  max_ticks: number;
  completed_at: string | null;
  final_state_counts: Record<string, number> | null;
  peak_velocity: number | null;
  total_transitions: Record<string, number> | null;
  metrics_history: TickData[] | null;
}

export interface TickData {
  tick: number;
  state_counts: { S: number; M: number; I: number; R: number };
  spread_rate: number;
  peak_velocity: number;
  active_narratives: number;
  dominant_narrative_id: string | null;
  node_states?: Record<string, string>;
}

export interface GraphNode {
  id: number;
  community: number;
  influence: number;
  degree: number;
}

export interface GraphEdge {
  source: number;
  target: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ReportResponse {
  simulation_id: string;
  content: string;
  generated_at: string;
}

export interface ReportDataResponse {
  simulation_id: string;
  config: Record<string, unknown>;
  final_state_counts: Record<string, number>;
  total_transitions: Record<string, number>;
  metrics_history: TickData[];
}

export const SMIR_COLORS = {
  S: "#4ADE80",
  M: "#EF4444",
  I: "#3B82F6",
  R: "#6B7280",
} as const;

export const TOPOLOGY_LABELS: Record<Topology, string> = {
  barabasi_albert: "Scale-Free (Barabási-Albert)",
  watts_strogatz: "Small-World (Watts-Strogatz)",
  stochastic_block_model: "Modular (Stochastic Block Model)",
};
