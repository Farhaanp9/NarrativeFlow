"""Tests for social network graph generation."""

import numpy as np

from narrativeflow.engine.graph import Topology, TopologyParams, generate_graph


def test_barabasi_albert_power_law() -> None:
    """BA graph should have power-law degree distribution: top 10% nodes hold >50% edges."""
    gd = generate_graph(Topology.BARABASI_ALBERT, 1000, TopologyParams(m=3))

    assert gd.n_nodes == 1000
    assert gd.n_edges > 0
    assert gd.adjacency.shape == (1000, 1000)

    # Power-law check: top 10% of nodes by degree should have >30% of total degree
    sorted_deg = np.sort(gd.degree)[::-1]
    top_10_pct = sorted_deg[:100]
    total_degree = sorted_deg.sum()
    assert top_10_pct.sum() / total_degree > 0.30


def test_watts_strogatz_high_clustering() -> None:
    """WS graph should have high clustering coefficient."""
    gd = generate_graph(
        Topology.WATTS_STROGATZ, 500, TopologyParams(k=6, p_rewire=0.1)
    )

    assert gd.n_nodes == 500
    mean_clustering = float(gd.clustering.mean())
    assert mean_clustering > 0.2, f"Mean clustering too low: {mean_clustering}"


def test_stochastic_block_model_communities() -> None:
    """SBM should produce the expected number of communities."""
    params = TopologyParams(n_communities=4, p_within=0.05, p_between=0.001)
    gd = generate_graph(Topology.STOCHASTIC_BLOCK_MODEL, 400, params)

    assert gd.n_nodes == 400
    unique_communities = np.unique(gd.community_ids)
    assert len(unique_communities) == 4


def test_adjacency_matrix_symmetric() -> None:
    """Adjacency matrix should be symmetric (undirected graph)."""
    gd = generate_graph(Topology.BARABASI_ALBERT, 100)
    diff = abs(gd.adjacency - gd.adjacency.T)
    assert diff.sum() == 0


def test_betweenness_normalized() -> None:
    """Betweenness centrality should be in [0, 1]."""
    gd = generate_graph(Topology.BARABASI_ALBERT, 200)
    assert gd.betweenness.min() >= 0.0
    assert gd.betweenness.max() <= 1.0


def test_influence_scores_normalized() -> None:
    """Influence scores (degree centrality) should be in [0, 1]."""
    gd = generate_graph(Topology.WATTS_STROGATZ, 200)
    assert gd.influence_scores.min() >= 0.0
    assert gd.influence_scores.max() <= 1.0


def test_edge_list_matches_adjacency() -> None:
    """Edge list and adjacency matrix should represent the same graph."""
    gd = generate_graph(Topology.BARABASI_ALBERT, 100, TopologyParams(m=2))
    assert len(gd.edge_list) == gd.n_edges
    # Each edge appears twice in adjacency (symmetric)
    assert gd.adjacency.nnz == gd.n_edges * 2
