"""Tests for agent population initialization and state management."""

import numpy as np

from narrativeflow.engine.agents import AgentPopulation, ArchetypeConfig, S


def _make_archetypes() -> list[ArchetypeConfig]:
    return [
        ArchetypeConfig(id=0, name="Skeptic", susceptibility=0.2, population_percentage=40),
        ArchetypeConfig(id=1, name="Believer", susceptibility=0.8, population_percentage=30),
        ArchetypeConfig(id=2, name="Neutral", susceptibility=0.5, population_percentage=30),
    ]


def test_population_array_shapes() -> None:
    pop = AgentPopulation(100)
    assert pop.states.shape == (100,)
    assert pop.susceptibility.shape == (100,)
    assert pop.confidence.shape == (100,)
    assert pop.ticks_in_state.shape == (100,)
    assert len(pop.narrative_ids) == 100


def test_all_agents_start_susceptible() -> None:
    pop = AgentPopulation(50)
    assert (pop.states == S).all()
    counts = pop.get_state_counts()
    assert counts == {"S": 50, "M": 0, "I": 0, "R": 0}


def test_from_archetypes_distributes_correctly() -> None:
    archetypes = _make_archetypes()
    n = 1000
    rng = np.random.default_rng(42)
    influence = rng.random(n).astype(np.float32)
    communities = np.zeros(n, dtype=np.int32)

    pop = AgentPopulation.from_archetypes(archetypes, n, influence, communities, rng=rng)

    assert pop.n == n
    assert pop.states.shape == (n,)

    # Check archetype distribution roughly matches percentages (±5%)
    for arch in archetypes:
        count = int((pop.archetype_id == arch.id).sum())
        expected = n * arch.population_percentage / 100
        assert abs(count - expected) < n * 0.05, (
            f"Archetype {arch.name}: expected ~{expected}, got {count}"
        )


def test_from_archetypes_applies_variation() -> None:
    """Agent traits should vary around archetype baseline, not be identical."""
    archetypes = [ArchetypeConfig(id=0, name="Test", susceptibility=0.5, population_percentage=100)]
    n = 500
    rng = np.random.default_rng(42)
    influence = np.ones(n, dtype=np.float32) * 0.5
    communities = np.zeros(n, dtype=np.int32)

    pop = AgentPopulation.from_archetypes(archetypes, n, influence, communities, rng=rng)

    # Not all identical
    assert pop.susceptibility.std() > 0.01
    # But centered near baseline
    assert abs(pop.susceptibility.mean() - 0.5) < 0.05


def test_get_by_state_mask() -> None:
    pop = AgentPopulation(10)
    pop.states[3] = 1  # M
    pop.states[7] = 2  # I

    s_mask = pop.get_by_state(S)
    assert s_mask.sum() == 8
    assert not s_mask[3]
    assert not s_mask[7]


def test_increment_ticks_in_state() -> None:
    pop = AgentPopulation(5)
    pop.states[0] = 1  # M
    pop.states[1] = 2  # I
    # agents 2,3,4 are S

    pop.increment_ticks_in_state()

    assert pop.ticks_in_state[0] == 1  # M agent incremented
    assert pop.ticks_in_state[1] == 1  # I agent incremented
    assert pop.ticks_in_state[2] == 0  # S agent not incremented
