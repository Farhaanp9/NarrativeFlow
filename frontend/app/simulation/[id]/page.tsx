"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import Link from "next/link";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { useSimulationStore } from "@/stores/simulationStore";
import { getSimulation, getGraph } from "@/lib/api";
import { getWsUrl } from "@/lib/ws";
import { SpreadTimeline } from "@/components/simulation/SpreadTimeline";
import { MetricsBar } from "@/components/simulation/MetricsBar";
import { TickControls } from "@/components/simulation/TickControls";
import { Badge } from "@/components/ui/badge";
import { FileText, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TickData } from "@/lib/types";

const NetworkGraph = dynamic(
  () => import("@/components/simulation/NetworkGraph"),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[400px] bg-card animate-pulse rounded-lg" />
    ),
  }
);

export default function SimulationPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const store = useSimulationStore();

  const { sendMessage, readyState } = useWebSocket(getWsUrl(id), {
    onMessage: async (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "completed") {
          store.setStatus("completed");
          // Apply final node states if present
          if (data.node_states) {
            store.setNodeStates(data.node_states);
          }
          // Re-fetch metrics history if we missed ticks
          try {
            const sim = await getSimulation(id);
            if (sim.metrics_history && store.tickHistory.length < sim.metrics_history.length) {
              store.loadMetricsHistory(sim.metrics_history);
            }
          } catch {
            // best effort
          }
        } else if (data.tick !== undefined && data.state_counts) {
          store.appendTick(data as TickData);
          if (store.status === "initializing") {
            store.setStatus("running");
          }
        }
      } catch {
        // ignore parse errors
      }
    },
    shouldReconnect: () => true,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
  });

  // Load simulation metadata and graph on mount
  useEffect(() => {
    store.setSimulation(id);

    const load = async () => {
      try {
        const sim = await getSimulation(id);
        store.setStatus(sim.status as "initializing" | "running" | "completed" | "failed");
        useSimulationStore.setState({ isPaused: sim.status === "paused" });

        // Load existing metrics history for completed/reconnected sims
        if (sim.metrics_history) {
          store.loadMetricsHistory(sim.metrics_history);
        }

        // Try to load graph data
        try {
          const graphData = await getGraph(id);
          store.setGraphData(graphData.nodes, graphData.edges);
          // Apply node states if included (completed simulations)
          if (graphData.node_states) {
            store.setNodeStates(graphData.node_states as Record<string, string>);
          }
        } catch {
          // Graph may not be ready yet during initialization
        }
      } catch {
        store.setStatus("failed");
      }
    };
    load();

    return () => {
      store.reset();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Retry loading graph if not available initially
  useEffect(() => {
    if (store.graphNodes.length > 0) return;
    if (store.status === "failed") return;

    const interval = setInterval(async () => {
      try {
        const graphData = await getGraph(id);
        store.setGraphData(graphData.nodes, graphData.edges);
        // Ticks that arrived before the graph only carried changes
        if (graphData.node_states) {
          store.setNodeStates(graphData.node_states as Record<string, string>);
        }
        clearInterval(interval);
      } catch {
        // keep retrying
      }
    }, 2000);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, store.graphNodes.length, store.status]);

  const connectionStatus = {
    [ReadyState.CONNECTING]: "Connecting...",
    [ReadyState.OPEN]: "Connected",
    [ReadyState.CLOSING]: "Closing",
    [ReadyState.CLOSED]: "Disconnected",
    [ReadyState.UNINSTANTIATED]: "",
  }[readyState];

  return (
    <main className="flex-1 flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-[#0A0E1A]/90 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
            NarrativeFlow
          </Link>
          <span className="text-muted-foreground">/</span>
          <span className="text-sm font-mono">{id.slice(0, 8)}</span>
          <Badge
            variant="secondary"
            className={cn(
              "border",
              store.status === "running" && "animate-glow-pulse bg-green-500/20 text-green-400 border-green-500/30",
              store.status === "completed" && "bg-blue-500/20 text-blue-400 border-blue-500/30",
              store.status === "failed" && "bg-red-500/20 text-red-400 border-red-500/30",
              store.status === "initializing" && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30 animate-pulse",
            )}
          >
            {store.status}
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className={cn("h-1.5 w-1.5 rounded-full", readyState === ReadyState.OPEN ? "bg-green-400" : "bg-red-400")} />
            {connectionStatus}
          </span>
          {store.status === "completed" && (
            <Link
              href={`/reports/${id}`}
              className="flex items-center gap-1.5 text-sm text-foreground underline underline-offset-4 hover:text-foreground/80 transition-colors"
            >
              <FileText className="h-3.5 w-3.5" />
              View Report
            </Link>
          )}
        </div>
      </div>

      {/* Status banners */}
      {store.status === "initializing" && (
        <div className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-yellow-500/5 via-yellow-500/10 to-yellow-500/5 border-b border-yellow-500/10 text-sm text-yellow-400/80 text-center">
          <Loader2 className="h-4 w-4 animate-spin" />
          Initializing simulation — generating archetypes and building network...
        </div>
      )}
      {store.status === "failed" && (
        <div className="px-4 py-3 bg-destructive/10 border-b border-destructive text-sm text-destructive text-center">
          Simulation failed. <Link href="/" className="underline">Try again</Link>
        </div>
      )}

      {/* Main content: 60/40 split */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-0 overflow-hidden">
        {/* Left: Network Graph */}
        <div className="overflow-hidden relative">
          <NetworkGraph />
        </div>

        {/* Right: Sidebar */}
        <div className="border-l border-border p-5 space-y-5 overflow-y-auto bg-background">
          <TickControls sendMessage={sendMessage} />

          <div className="h-px bg-white/5" />

          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Spread Timeline</h3>
            <SpreadTimeline />
          </div>

          <div className="h-px bg-white/5" />

          <div>
            <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">Metrics</h3>
            <MetricsBar />
          </div>
        </div>
      </div>
    </main>
  );
}
