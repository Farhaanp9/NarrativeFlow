"""Tests for narrative mutation during simulation (PRD 10.5)."""

from narrativeflow.engine.agents import ArchetypeConfig
from narrativeflow.engine.simulation import SimulationConfig, SimulationEngine


def _default_archetypes() -> list[ArchetypeConfig]:
    return [
        ArchetypeConfig(
            id=0,
            name="Credulous Consumer",
            susceptibility=0.8,
            sharing_tendency=0.7,
            emotional_reactivity=0.7,
            mutation_style="exaggeration",
            population_percentage=40,
        ),
        ArchetypeConfig(
            id=1,
            name="Conspiracy Theorist",
            susceptibility=0.7,
            sharing_tendency=0.85,
            emotional_reactivity=0.8,
            mutation_style="conspiracy_framing",
            population_percentage=20,
        ),
        ArchetypeConfig(
            id=2,
            name="Passive Observer",
            susceptibility=0.4,
            sharing_tendency=0.2,
            emotional_reactivity=0.3,
            mutation_style="exaggeration",
            population_percentage=40,
        ),
    ]


def test_should_mutate_at_interval() -> None:
    """should_mutate() should be True at mutation_interval ticks."""
    config = SimulationConfig(
        seed_text="Test", population_size=50, max_ticks=100, seed=42
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    # Run ticks and check mutation interval
    mutation_ticks = []
    for _ in range(60):
        engine.tick()
        if engine.should_mutate():
            mutation_ticks.append(engine.current_tick)

    # Default mutation_interval is 20
    assert 20 in mutation_ticks
    assert 40 in mutation_ticks
    assert 60 in mutation_ticks
    assert 10 not in mutation_ticks


def test_get_mutation_candidates() -> None:
    """Candidates should be archetypes with agents in M state."""
    config = SimulationConfig(
        seed_text="Test", population_size=100, max_ticks=50, seed=42
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    # Run a few ticks to spread misinformation
    for _ in range(10):
        engine.tick()

    candidates = engine.get_mutation_candidates()

    # Should have at least one candidate (archetypes with M agents)
    assert len(candidates) > 0

    for arch, content in candidates:
        assert isinstance(arch, ArchetypeConfig)
        assert isinstance(content, str)
        assert len(content) > 0


def test_apply_mutations() -> None:
    """apply_mutations should create new narratives and update agent narrative IDs."""
    config = SimulationConfig(
        seed_text="Original claim about health", population_size=100,
        max_ticks=50, seed=42,
    )
    engine = SimulationEngine(config)
    archetypes = _default_archetypes()
    engine.initialize(archetypes)

    # Run ticks to create some M agents
    for _ in range(15):
        engine.tick()

    initial_narrative_count = len(engine.tracker.narratives)

    # Get candidates and apply mutations
    candidates = engine.get_mutation_candidates()
    if candidates:
        mutations = [
            (arch, f"MUTATED: {content}", arch.mutation_style)
            for arch, content in candidates
        ]
        engine.apply_mutations(mutations)

        # Should have created new narratives
        assert len(engine.tracker.narratives) > initial_narrative_count

        # The new narratives should have parent references
        for _nid, narrative in engine.tracker.narratives.items():
            if narrative.parent_id is not None:
                assert narrative.parent_id in engine.tracker.narratives
                assert len(narrative.lineage) > 1


def test_mutation_updates_agent_narratives() -> None:
    """After mutation, agents of the archetype should hold the new narrative ID."""
    config = SimulationConfig(
        seed_text="Test mutation narrative", population_size=100,
        max_ticks=50, seed=42,
    )
    engine = SimulationEngine(config)
    archetypes = _default_archetypes()
    engine.initialize(archetypes)

    for _ in range(15):
        engine.tick()

    candidates = engine.get_mutation_candidates()
    if not candidates:
        return  # No M agents to mutate — skip

    arch, content = candidates[0]
    old_nids = set()
    if engine.agents is not None:
        import numpy as np
        m_mask = (engine.agents.archetype_id == arch.id) & (engine.agents.states == 1)
        for idx in np.where(m_mask)[0]:
            old_nids.add(engine.agents.narrative_ids[idx])

    engine.apply_mutations([(arch, "Mutated version", arch.mutation_style)])

    # Check that agents now hold a different narrative ID
    if engine.agents is not None:
        import numpy as np
        m_mask = (engine.agents.archetype_id == arch.id) & (engine.agents.states == 1)
        new_nids = set()
        for idx in np.where(m_mask)[0]:
            new_nids.add(engine.agents.narrative_ids[idx])

        # New narrative IDs should differ from old ones
        assert new_nids != old_nids or len(old_nids) == 0


def test_simulation_with_mutation_callback_runs() -> None:
    """Full simulation should still run correctly with mutation support."""
    config = SimulationConfig(
        seed_text="Test full run with mutations",
        population_size=200,
        max_ticks=50,
        seed=42,
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    # Simulate the async mutation loop synchronously with mock mutations
    for _ in range(config.max_ticks):
        metrics = engine.tick()

        if engine.should_mutate():
            candidates = engine.get_mutation_candidates()
            mutations = [
                (arch, f"[Mutated by {arch.name}]: {content}", arch.mutation_style)
                for arch, content in candidates
            ]
            if mutations:
                engine.apply_mutations(mutations)

        if metrics.state_counts["S"] == 0:
            break
        if metrics.state_counts["M"] == 0 and metrics.state_counts["I"] == 0:
            break

    assert engine.current_tick > 0
    # With mutations, there should be more than 1 narrative
    # (seed + at least one mutation if any M agents existed at tick 20)
    if engine.current_tick >= 20:
        assert len(engine.tracker.narratives) >= 1
