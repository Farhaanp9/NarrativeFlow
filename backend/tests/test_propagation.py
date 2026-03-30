"""Tests for SMIR propagation model transition equations."""

import numpy as np
from scipy import sparse

from narrativeflow.engine.agents import AgentPopulation, I, M, S
from narrativeflow.engine.propagation import (
    PropagationConfig,
    compute_confidence,
    compute_hardening,
    compute_m_to_i,
    compute_s_to_i,
    compute_s_to_m,
    resolve_transitions,
)


def _make_pair(
    state_a: int = S, state_b: int = M
) -> tuple[AgentPopulation, sparse.csr_matrix]:
    """Create a 2-agent population connected by an edge."""
    pop = AgentPopulation(2)
    pop.states[0] = state_a
    pop.states[1] = state_b
    pop.susceptibility[:] = 0.8
    pop.trust_threshold[:] = 0.7
    pop.open_mindedness[:] = 0.6
    pop.influence_score[:] = 0.5
    pop.activity_rate[:] = 1.0  # always active

    adj = sparse.csr_matrix(np.array([[0, 1], [1, 0]], dtype=np.float32))
    return pop, adj


def test_s_to_m_with_m_neighbor() -> None:
    """S agent adjacent to M agent should have nonzero P(S→M)."""
    pop, adj = _make_pair(S, M)
    config = PropagationConfig(beta_m=0.3)
    probs = compute_s_to_m(pop, adj, config, virality=1.0, emotional_charge=0.5, tick=0)
    # Agent 0 is S with M neighbor → should have positive probability
    assert probs[0] > 0.0
    # Agent 1 is M → probability should be 0
    assert probs[1] == 0.0


def test_s_to_m_no_m_neighbors() -> None:
    """S agents with no M neighbors should have P(S→M) = 0."""
    pop, adj = _make_pair(S, S)
    config = PropagationConfig()
    probs = compute_s_to_m(pop, adj, config, virality=1.0, emotional_charge=0.5, tick=0)
    assert (probs == 0.0).all()


def test_s_to_m_increases_with_susceptibility() -> None:
    """Higher susceptibility should yield higher P(S→M)."""
    pop, adj = _make_pair(S, M)
    config = PropagationConfig(beta_m=0.3)

    pop.susceptibility[0] = 0.2
    p_low = compute_s_to_m(pop, adj, config, virality=1.0, emotional_charge=0.5, tick=0)[0]

    pop.susceptibility[0] = 0.9
    p_high = compute_s_to_m(pop, adj, config, virality=1.0, emotional_charge=0.5, tick=0)[0]

    assert p_high > p_low


def test_s_to_i_with_i_neighbor() -> None:
    """S agent adjacent to I agent should have nonzero P(S→I)."""
    pop, adj = _make_pair(S, I)
    config = PropagationConfig(beta_i=0.2)
    probs = compute_s_to_i(pop, adj, config, correction_strength=0.5)
    assert probs[0] > 0.0
    assert probs[1] == 0.0


def test_m_to_i_correction() -> None:
    """M agent adjacent to I agent should have nonzero P(M→I)."""
    pop, adj = _make_pair(M, I)
    config = PropagationConfig(gamma=0.2)
    probs = compute_m_to_i(pop, adj, config)
    assert probs[0] > 0.0
    assert probs[1] == 0.0


def test_m_to_i_decreases_with_confidence() -> None:
    """Higher confidence (longer in M state) should reduce P(M→I)."""
    pop, adj = _make_pair(M, I)
    config = PropagationConfig(gamma=0.3, confidence_lambda=0.1)

    pop.ticks_in_state[0] = 1
    p_early = compute_m_to_i(pop, adj, config)[0]

    pop.ticks_in_state[0] = 50
    p_late = compute_m_to_i(pop, adj, config)[0]

    assert p_late < p_early, "Correction should be harder when confidence is high"


def test_hardening_sigmoid_shape() -> None:
    """Hardening probability should follow sigmoid: low before threshold, high after."""
    pop = AgentPopulation(1)
    pop.states[0] = M
    config = PropagationConfig(hardening_threshold=30, hardening_steepness=0.2)

    pop.ticks_in_state[0] = 5
    p_early = compute_hardening(pop, config)[0]

    pop.ticks_in_state[0] = 30  # at threshold
    p_mid = compute_hardening(pop, config)[0]

    pop.ticks_in_state[0] = 60
    p_late = compute_hardening(pop, config)[0]

    assert p_early < 0.1, f"Too high before threshold: {p_early}"
    assert 0.4 < p_mid < 0.6, f"Not near 0.5 at threshold: {p_mid}"
    assert p_late > 0.9, f"Too low after threshold: {p_late}"


def test_confidence_accumulation() -> None:
    """Confidence should grow from 0 toward 1 over time."""
    ticks = np.array([0, 10, 50, 200], dtype=np.int32)
    conf = compute_confidence(ticks, lambda_=0.05)

    assert conf[0] == 0.0  # no time, no confidence
    assert 0.0 < conf[1] < conf[2] < conf[3]  # monotonically increasing
    assert conf[3] > 0.99  # approaches 1 for large t


def test_novelty_decay_reduces_virality() -> None:
    """S→M probability should decrease over time due to novelty decay."""
    pop, adj = _make_pair(S, M)
    config = PropagationConfig(beta_m=0.3, novelty_decay=0.99)

    p_early = compute_s_to_m(pop, adj, config, virality=1.5, emotional_charge=0.6, tick=0)[0]
    p_late = compute_s_to_m(pop, adj, config, virality=1.5, emotional_charge=0.6, tick=100)[0]

    assert p_late < p_early, "Novelty decay should reduce transmission over time"


def test_isolated_node_never_transitions() -> None:
    """An agent with no neighbors should never change state."""
    pop = AgentPopulation(2)
    pop.states[0] = S
    pop.states[1] = M
    pop.susceptibility[:] = 1.0
    pop.activity_rate[:] = 1.0

    # No edges
    adj = sparse.csr_matrix((2, 2), dtype=np.float32)
    config = PropagationConfig(beta_m=0.5)

    probs = compute_s_to_m(pop, adj, config, virality=1.0, emotional_charge=1.0, tick=0)
    assert probs[0] == 0.0


def test_resolve_transitions_changes_states() -> None:
    """Over multiple ticks, S agents should transition to M in a connected network."""
    n = 100
    pop = AgentPopulation(n)
    pop.susceptibility[:] = 0.9
    pop.trust_threshold[:] = 0.5
    pop.open_mindedness[:] = 0.5
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.5

    # Seed 10% as M
    pop.states[:10] = M
    for i in range(10):
        pop.narrative_ids[i] = "seed"

    # Banded graph: each node connected to ±5 neighbors (denser than chain)
    rows, cols, data_list = [], [], []
    for i in range(n):
        for j in range(max(0, i - 5), min(n, i + 6)):
            if i != j:
                rows.append(i)
                cols.append(j)
                data_list.append(1.0)
    adj = sparse.csr_matrix(
        (np.array(data_list, dtype=np.float32), (rows, cols)), shape=(n, n)
    )

    config = PropagationConfig(beta_m=0.4)
    rng = np.random.default_rng(42)

    total_s_to_m = 0
    for tick in range(10):
        result = resolve_transitions(pop, adj, config, 1.0, 0.6, tick, rng, "seed")
        total_s_to_m += result.counts["S_to_M"]
    assert total_s_to_m > 0, "At least some S agents should become M over 10 ticks"


def test_misinfo_spreads_faster_than_truth() -> None:
    """β_M > β_I should result in more S→M than S→I transitions over many ticks.

    S→M base_p = β_M × susceptibility × virality × emotional_charge
    S→I base_p = β_I × trust_threshold × correction_strength
    We set params so that S→M effective rate clearly exceeds S→I.
    """
    n = 300
    pop = AgentPopulation(n)
    pop.susceptibility[:] = 0.7
    pop.trust_threshold[:] = 0.3  # low trust reduces S→I
    pop.open_mindedness[:] = 0.3
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.3

    # Interleave M and I agents so both are adjacent to S agents
    for i in range(0, 30, 2):
        pop.states[i] = M
        pop.narrative_ids[i] = "seed"
    for i in range(1, 30, 2):
        pop.states[i] = I

    # Banded graph: each node connected to ±3 neighbors
    rng = np.random.default_rng(123)
    rows, cols, data_list = [], [], []
    for i in range(n):
        for j in range(max(0, i - 3), min(n, i + 4)):
            if i != j:
                rows.append(i)
                cols.append(j)
                data_list.append(1.0)
    adj = sparse.csr_matrix(
        (np.array(data_list, dtype=np.float32), (rows, cols)), shape=(n, n)
    )

    # β_M much higher than β_I, with high virality and emotional charge
    config = PropagationConfig(beta_m=0.35, beta_i=0.05)

    total_s_to_m = 0
    total_s_to_i = 0
    for tick in range(80):
        result = resolve_transitions(
            pop, adj, config, virality=1.5, emotional_charge=0.8, tick=tick, rng=rng,
            seed_narrative_id="seed", correction_strength=0.3,
        )
        total_s_to_m += result.counts["S_to_M"]
        total_s_to_i += result.counts["S_to_I"]

    assert total_s_to_m > total_s_to_i, (
        f"Misinformation ({total_s_to_m}) should spread faster than truth ({total_s_to_i})"
    )
