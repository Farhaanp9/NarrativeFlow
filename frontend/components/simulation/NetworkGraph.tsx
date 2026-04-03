"use client";

import { useEffect, useRef } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { useSimulationStore } from "@/stores/simulationStore";
import { SMIR_COLORS } from "@/lib/types";

export default function NetworkGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  const sigmaRef = useRef<Sigma | null>(null);

  const graphNodes = useSimulationStore((s) => s.graphNodes);
  const graphEdges = useSimulationStore((s) => s.graphEdges);
  const nodeStates = useSimulationStore((s) => s.nodeStates);

  // Initialize graph and Sigma on mount
  useEffect(() => {
    if (!containerRef.current || graphNodes.length === 0) return;

    // Clean up previous instance
    if (sigmaRef.current) {
      sigmaRef.current.kill();
      sigmaRef.current = null;
    }

    const graph = new Graph();

    // Add nodes
    for (const node of graphNodes) {
      graph.addNode(String(node.id), {
        label: `Agent ${node.id}`,
        size: 5 + node.influence * 15,
        color: SMIR_COLORS.S,
        x: Math.random(),
        y: Math.random(),
      });
    }

    // Add edges
    for (const edge of graphEdges) {
      const key = `${edge.source}-${edge.target}`;
      if (!graph.hasEdge(key)) {
        graph.addEdgeWithKey(key, String(edge.source), String(edge.target), {
          color: "rgba(255, 255, 255, 0.06)",
          size: 0.3,
        });
      }
    }

    // Compute layout
    forceAtlas2.assign(graph, {
      iterations: 200,
      settings: {
        gravity: 5,
        scalingRatio: 8,
        barnesHutOptimize: true,
        barnesHutTheta: 0.5,
        slowDown: 5,
        strongGravityMode: true,
      },
    });

    graphRef.current = graph;

    // Create Sigma renderer
    const sigma = new Sigma(graph, containerRef.current, {
      renderLabels: false,
      renderEdgeLabels: false,
      defaultEdgeColor: "rgba(255, 255, 255, 0.06)",
      defaultNodeColor: SMIR_COLORS.S,
      labelColor: { color: "#E8EAF0" },
      labelRenderedSizeThreshold: 12,
      hideEdgesOnMove: true,
    });

    sigmaRef.current = sigma;

    return () => {
      sigma.kill();
      sigmaRef.current = null;
      graphRef.current = null;
    };
  }, [graphNodes, graphEdges]);

  // Update node colors when states change
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || Object.keys(nodeStates).length === 0) return;

    for (const [nodeId, state] of Object.entries(nodeStates)) {
      if (graph.hasNode(nodeId)) {
        const color =
          SMIR_COLORS[state as keyof typeof SMIR_COLORS] ?? SMIR_COLORS.S;
        graph.setNodeAttribute(nodeId, "color", color);
      }
    }
  }, [nodeStates]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[400px] bg-[#050810] rounded-none"
    />
  );
}
