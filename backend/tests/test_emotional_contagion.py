"""Tests for emotional contagion and network amplification (PRD 10.4)."""

import numpy as np
from scipy import sparse

from narrativeflow.engine.agents import AgentPopulation, M, S
from narrativeflow.engine.propagation import (
    PropagationConfig,
    compute_s_to_m,
    resolve_transitions,
)


def _banded_adj(n: int, bandwidth: int = 3) -> sparse.csr_matrix:
    """Create a banded adjacency matrix."""
    rows, cols, data = [], [], []
    for i in range(n):
        for j in range(max(0, i - bandwidth), min(n, i + bandwidth + 1)):
            if i != j:
                rows.append(i)
                cols.append(j)
                data.append(1.0)
    return sparse.csr_matrix(
        (np.array(data, dtype=np.float32), (rows, cols)), shape=(n, n)
    )


def test_emotional_exposure_boosts_susceptibility() -> None:
    """Agents with emotional_exposure > 0 should have higher P(S→M)."""
    pop = AgentPopulation(3)
    pop.states[0] = S
    pop.states[1] = M
    pop.states[2] = S
    pop.susceptibility[:] = 0.5
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.5

    adj = sparse.csr_matrix(
        np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.float32)
    )
    config = PropagationConfig(beta_m=0.3)

    # Without emotional exposure
    p_base = compute_s_to_m(pop, adj, config, 1.0, 0.5, tick=0)

    # With emotional exposure
    pop.emotional_exposure[0] = 0.5
    pop.emotional_exposure[2] = 0.5
    p_boosted = compute_s_to_m(pop, adj, config, 1.0, 0.5, tick=0)

    assert p_boosted[0] > p_base[0], "Emotional exposure should boost S→M probability"
    assert p_boosted[2] > p_base[2], "Emotional exposure should boost S→M probability"


def test_emotional_exposure_decays_over_ticks() -> None:
    """Emotional exposure should decay each tick."""
    n = 50
    pop = AgentPopulation(n)
    pop.susceptibility[:] = 0.95
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.5
    pop.emotional_reactivity[:] = 0.9

    pop.states[:10] = M
    for i in range(10):
        pop.narrative_ids[i] = "seed"

    adj = _banded_adj(n, 5)
    config = PropagationConfig(beta_m=0.5)
    rng = np.random.default_rng(42)

    # Run multiple ticks to ensure some S→M transitions happen
    for tick in range(5):
        resolve_transitions(pop, adj, config, 1.5, 0.9, tick, rng, "seed")

    exposure_after = pop.emotional_exposure.copy()

    # By now there should have been transitions generating emotional exposure
    assert exposure_after.max() > 0, "Should have emotional exposure after transitions"

    # Run more ticks — far agents' exposure should decay
    saved_exposure = pop.emotional_exposure.copy()
    # Set all agents to R so no new transitions generate exposure
    pop.states[:] = 3  # R
    resolve_transitions(pop, adj, config, 1.5, 0.9, 10, rng, "seed")

    # All exposure should have decayed since no new S→M happened
    assert pop.emotional_exposure.max() < saved_exposure.max(), (
        "Emotional exposure should decay when no new transitions occur"
    )


def test_network_amplification_betweenness() -> None:
    """Agents with high betweenness should spread misinformation more effectively."""
    pop = AgentPopulation(3)
    pop.states[0] = S
    pop.states[1] = M  # spreader
    pop.states[2] = S
    pop.susceptibility[:] = 0.5
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.5

    adj = sparse.csr_matrix(
        np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=np.float32)
    )
    config = PropagationConfig(beta_m=0.3)

    # Low betweenness for spreader
    pop.betweenness[1] = 0.0
    p_low = compute_s_to_m(pop, adj, config, 1.0, 0.5, tick=0)

    # High betweenness for spreader (bridge node)
    pop.betweenness[1] = 1.0
    p_high = compute_s_to_m(pop, adj, config, 1.0, 0.5, tick=0)

    assert p_high[0] > p_low[0], (
        "High-betweenness M neighbor should increase S→M probability"
    )


def test_state_transition_history_recorded() -> None:
    """State transitions should be recorded in agent history."""
    n = 50
    pop = AgentPopulation(n)
    pop.susceptibility[:] = 0.9
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.5

    pop.states[:5] = M
    for i in range(5):
        pop.narrative_ids[i] = "seed"

    adj = _banded_adj(n, 5)
    config = PropagationConfig(beta_m=0.5)
    rng = np.random.default_rng(42)

    # Run a few ticks
    for tick in range(10):
        resolve_transitions(pop, adj, config, 1.0, 0.7, tick, rng, "seed")

    # Check that some agents have transition history
    has_history = sum(1 for h in pop.state_transitions if len(h) > 0)
    assert has_history > 0, "Some agents should have transition history"

    # Verify transition format: (tick, from_state, to_state)
    for agent_history in pop.state_transitions:
        for entry in agent_history:
            assert len(entry) == 3
            tick_num, from_s, to_s = entry
            assert isinstance(tick_num, int)
            assert from_s != to_s, "Transition should be between different states"


def test_changed_indices_returned() -> None:
    """resolve_transitions should return indices of agents that changed state."""
    n = 50
    pop = AgentPopulation(n)
    pop.susceptibility[:] = 0.9
    pop.activity_rate[:] = 1.0
    pop.influence_score[:] = 0.5

    pop.states[:5] = M
    for i in range(5):
        pop.narrative_ids[i] = "seed"

    adj = _banded_adj(n, 5)
    config = PropagationConfig(beta_m=0.5)
    rng = np.random.default_rng(42)

    total_changed = 0
    for tick in range(5):
        result = resolve_transitions(pop, adj, config, 1.0, 0.7, tick, rng, "seed")
        total_changed += len(result.changed_indices)
        # changed_indices should match the sum of transitions
        total_counts = sum(result.counts.values())
        assert len(result.changed_indices) == total_counts

    assert total_changed > 0, "Some agents should have changed state"
