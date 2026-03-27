"""Social network graph generation and analysis using python-igraph."""

from enum import StrEnum

import igraph as ig
import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from scipy import sparse


class Topology(StrEnum):
    """Supported network topologies."""

    BARABASI_ALBERT = "barabasi_albert"
    WATTS_STROGATZ = "watts_strogatz"
    STOCHASTIC_BLOCK_MODEL = "stochastic_block_model"


class TopologyParams(BaseModel):
    """Parameters for graph generation, varies by topology type."""

    # Barabási-Albert
    m: int = Field(default=3, description="Edges per new node (BA)")
    # Watts-Strogatz
    k: int = Field(default=6, description="Each node connected to k nearest neighbors (WS)")
    p_rewire: float = Field(default=0.1, description="Rewiring probability (WS)")
    # Stochastic Block Model
    n_communities: int = Field(default=5, description="Number of communities (SBM)")
    p_within: float = Field(default=0.05, description="Intra-community edge probability (SBM)")
    p_between: float = Field(default=0.001, description="Inter-community edge probability (SBM)")


class GraphData:
    """Generated graph with precomputed metrics."""

    def __init__(
        self,
        adjacency: sparse.csr_matrix,
        edge_list: list[tuple[int, int]],
        betweenness: NDArray[np.float32],
        clustering: NDArray[np.float32],
        degree: NDArray[np.int32],
        community_ids: NDArray[np.int32],
        influence_scores: NDArray[np.float32],
        n_nodes: int,
        n_edges: int,
    ) -> None:
        self.adjacency = adjacency
        self.edge_list = edge_list
        self.betweenness = betweenness
        self.clustering = clustering
        self.degree = degree
        self.community_ids = community_ids
        self.influence_scores = influence_scores
        self.n_nodes = n_nodes
        self.n_edges = n_edges


def generate_graph(
    topology: Topology,
    n: int,
    params: TopologyParams | None = None,
    seed: int | None = None,
) -> GraphData:
    """Generate a social network graph with the specified topology.

    Args:
        topology: Which network model to use.
        n: Number of nodes (agents).
        params: Topology-specific parameters.

    Returns:
        GraphData with adjacency matrix and precomputed node metrics.
    """
    if params is None:
        params = TopologyParams()

    if seed is not None:
        import random as _random
        _random.seed(seed)

    if topology == Topology.BARABASI_ALBERT:
        graph = ig.Graph.Barabasi(n=n, m=params.m, directed=False)
    elif topology == Topology.WATTS_STROGATZ:
        graph = ig.Graph.Watts_Strogatz(dim=1, size=n, nei=params.k // 2, p=params.p_rewire)
    elif topology == Topology.STOCHASTIC_BLOCK_MODEL:
        graph = _generate_sbm(n, params)
    else:
        raise ValueError(f"Unknown topology: {topology}")

    return _analyze_graph(graph)


def _generate_sbm(n: int, params: TopologyParams) -> ig.Graph:
    """Generate a Stochastic Block Model graph."""
    k = params.n_communities
    # Distribute nodes roughly equally across communities
    sizes = [n // k] * k
    sizes[-1] += n - sum(sizes)  # remainder to last community

    # Build preference matrix: high intra-community, low inter-community
    pref_matrix = []
    for i in range(k):
        row = []
        for j in range(k):
            row.append(params.p_within if i == j else params.p_between)
        pref_matrix.append(row)

    graph = ig.Graph.SBM(pref_matrix, sizes, directed=False)
    # Store ground-truth community assignments
    community_ids = []
    for i, size in enumerate(sizes):
        community_ids.extend([i] * size)
    graph.vs["block"] = community_ids
    return graph


def _analyze_graph(graph: ig.Graph) -> GraphData:
    """Compute all node metrics on a generated graph."""
    n = graph.vcount()

    # Betweenness centrality (normalized)
    betweenness_raw = graph.betweenness()
    max_b = max(betweenness_raw) if betweenness_raw else 1.0
    if max_b == 0:
        max_b = 1.0
    betweenness = np.array(betweenness_raw, dtype=np.float32) / max_b

    # Local clustering coefficient
    clustering = np.array(graph.transitivity_local_undirected(mode="zero"), dtype=np.float32)

    # Degree
    degree = np.array(graph.degree(), dtype=np.int32)

    # Community detection (Louvain / multilevel)
    if hasattr(graph.vs, "attributes") and "block" in graph.vs.attributes():
        community_ids = np.array(graph.vs["block"], dtype=np.int32)
    else:
        communities = graph.community_multilevel()
        community_ids = np.array(communities.membership, dtype=np.int32)

    # Influence score: normalized degree centrality (simple, effective)
    max_deg = max(degree) if len(degree) > 0 else 1
    if max_deg == 0:
        max_deg = 1
    influence_scores = degree.astype(np.float32) / max_deg

    # Adjacency as sparse CSR matrix
    edges = graph.get_edgelist()
    if edges:
        rows, cols = zip(*edges, strict=False)
        data = np.ones(len(rows) * 2, dtype=np.float32)
        row_idx = np.array(list(rows) + list(cols), dtype=np.int32)
        col_idx = np.array(list(cols) + list(rows), dtype=np.int32)
        adjacency = sparse.csr_matrix((data, (row_idx, col_idx)), shape=(n, n))
    else:
        adjacency = sparse.csr_matrix((n, n), dtype=np.float32)

    return GraphData(
        adjacency=adjacency,
        edge_list=edges,
        betweenness=betweenness,
        clustering=clustering,
        degree=degree,
        community_ids=community_ids,
        influence_scores=influence_scores,
        n_nodes=n,
        n_edges=graph.ecount(),
    )
