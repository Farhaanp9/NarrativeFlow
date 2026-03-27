"""Integration tests for the full simulation engine."""

import time

from narrativeflow.engine.agents import ArchetypeConfig
from narrativeflow.engine.simulation import SimulationConfig, SimulationEngine


def _default_archetypes() -> list[ArchetypeConfig]:
    return [
        ArchetypeConfig(
            id=0, name="Credulous Consumer",
            susceptibility=0.8, sharing_tendency=0.7,
            trust_mainstream_media=0.3, trust_social_peers=0.8,
            emotional_reactivity=0.7, correction_receptiveness=0.3,
            population_percentage=25,
        ),
        ArchetypeConfig(
            id=1, name="Critical Thinker",
            susceptibility=0.2, sharing_tendency=0.3,
            trust_mainstream_media=0.8, trust_social_peers=0.3,
            emotional_reactivity=0.2, correction_receptiveness=0.8,
            population_percentage=20,
        ),
        ArchetypeConfig(
            id=2, name="Passive Observer",
            susceptibility=0.5, sharing_tendency=0.2,
            trust_mainstream_media=0.5, trust_social_peers=0.5,
            emotional_reactivity=0.4, correction_receptiveness=0.5,
            population_percentage=35,
        ),
        ArchetypeConfig(
            id=3, name="Active Amplifier",
            susceptibility=0.7, sharing_tendency=0.9,
            trust_mainstream_media=0.2, trust_social_peers=0.9,
            emotional_reactivity=0.8, correction_receptiveness=0.2,
            population_percentage=20,
        ),
    ]


def test_simulation_1000_agents_100_ticks() -> None:
    """Full simulation with 1000 agents should complete 100 ticks and show spread."""
    config = SimulationConfig(
        seed_text="Breaking: Popular supplement found to contain undisclosed chemicals",
        population_size=1000,
        max_ticks=100,
        seed=42,
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    result = engine.run()

    # Simulation should have run
    assert result.total_ticks > 0
    assert result.total_ticks <= 100

    # Some agents should have transitioned from S
    assert result.final_state_counts["S"] < 1000
    assert result.total_transitions["S_to_M"] > 0

    # Metrics should be recorded for each tick
    assert len(engine.metrics_history) == result.total_ticks + 1  # +1 for initial


def test_simulation_runs_under_5_seconds() -> None:
    """1000-agent simulation over 100 ticks should run in under 5 seconds."""
    config = SimulationConfig(
        seed_text="Test headline for performance",
        population_size=1000,
        max_ticks=100,
        seed=99,
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    start = time.perf_counter()
    engine.run()
    elapsed = time.perf_counter() - start

    assert elapsed < 5.0, f"Simulation took {elapsed:.2f}s, expected <5s"


def test_simulation_metrics_per_tick() -> None:
    """Each tick should produce valid metrics with correct state counts."""
    config = SimulationConfig(
        seed_text="Test", population_size=200, max_ticks=50, seed=7,
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    engine.run()

    for metrics in engine.metrics_history:
        total = sum(metrics.state_counts.values())
        assert total == 200, f"Tick {metrics.tick}: state counts sum to {total}, expected 200"
        assert metrics.spread_rate >= 0.0
        assert metrics.peak_velocity >= 0.0


def test_simulation_convergence_stops_early() -> None:
    """Simulation should stop early if all agents leave S state."""
    config = SimulationConfig(
        seed_text="Extremely viral claim",
        population_size=50,
        max_ticks=500,
        seed=42,
    )
    engine = SimulationEngine(config)

    # All agents highly susceptible
    archetypes = [
        ArchetypeConfig(
            id=0, name="Highly Susceptible",
            susceptibility=0.95, sharing_tendency=0.9,
            emotional_reactivity=0.9, population_percentage=100,
        ),
    ]
    engine.initialize(archetypes)
    result = engine.run()

    # Should converge before max_ticks
    assert result.total_ticks < 500


def test_tick_callback_invoked() -> None:
    """on_tick callback should be called for each tick."""
    config = SimulationConfig(
        seed_text="Test", population_size=50, max_ticks=10, seed=1,
    )
    engine = SimulationEngine(config)
    engine.initialize(_default_archetypes())

    ticks_seen: list[int] = []
    engine.run(on_tick=lambda m: ticks_seen.append(m.tick))

    assert len(ticks_seen) > 0
    assert ticks_seen == list(range(1, len(ticks_seen) + 1))


def test_reproducibility_with_seed() -> None:
    """Same RNG seed should produce identical results."""
    config = SimulationConfig(
        seed_text="Reproducibility test", population_size=200, max_ticks=50, seed=42,
    )

    engine1 = SimulationEngine(config)
    engine1.initialize(_default_archetypes())
    result1 = engine1.run()

    engine2 = SimulationEngine(config)
    engine2.initialize(_default_archetypes())
    result2 = engine2.run()

    assert result1.final_state_counts == result2.final_state_counts
    assert result1.total_ticks == result2.total_ticks
