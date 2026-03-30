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
    onMessage: (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "completed") {
          store.setStatus("completed");
        } else if (data.tick !== undefined) {
          store.appendTick(data as TickData);
          if (store.status !== "running") {
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

        // Load existing metrics history for completed/reconnected sims
        if (sim.metrics_history) {
          for (const tick of sim.metrics_history) {
            store.appendTick(tick);
          }
        }

        // Try to load graph data
        try {
          const graphData = await getGraph(id);
          store.setGraphData(graphData.nodes, graphData.edges);
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
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm text-muted-foreground hover:text-foreground">
            NarrativeFlow
          </Link>
          <span className="text-muted-foreground">/</span>
          <span className="text-sm font-mono">{id.slice(0, 8)}</span>
          <Badge variant={store.status === "running" ? "default" : "secondary"}>
            {store.status}
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">{connectionStatus}</span>
          {store.status === "completed" && (
            <Link
              href={`/reports/${id}`}
              className="text-sm text-primary hover:underline"
            >
              View Report
            </Link>
          )}
        </div>
      </div>

      {/* Status banners */}
      {store.status === "initializing" && (
        <div className="px-4 py-3 bg-card border-b border-border text-sm text-muted-foreground text-center animate-pulse">
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
        <div className="p-4 overflow-hidden">
          <NetworkGraph />
        </div>

        {/* Right: Sidebar */}
        <div className="border-l border-border p-4 space-y-4 overflow-y-auto">
          <TickControls sendMessage={sendMessage} />

          <div>
            <h3 className="text-sm font-medium mb-2">Spread Timeline</h3>
            <SpreadTimeline />
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Metrics</h3>
            <MetricsBar />
          </div>
        </div>
      </div>
    </main>
  );
}
