"""Report generation module — wraps LLM client for simulation reports."""

from narrativeflow.engine.metrics import TickMetrics
from narrativeflow.engine.simulation import SimulationConfig
from narrativeflow.llm.client import LLMClient


async def generate_report(
    llm: LLMClient,
    config: SimulationConfig,
    metrics_history: list[TickMetrics],
    total_transitions: dict[str, int],
) -> str:
    """Generate a markdown report summarizing simulation results.

    Args:
        llm: LLM client for report synthesis.
        config: Simulation configuration.
        metrics_history: Full tick-by-tick metrics.
        total_transitions: Cumulative transition counts.

    Returns:
        Markdown report string.
    """
    if not metrics_history:
        return _empty_report(config)

    final = metrics_history[-1]
    final_counts = final.state_counts

    return await llm.generate_report(
        seed_text=config.seed_text,
        population_size=config.population_size,
        topology=config.topology.value,
        total_ticks=final.tick,
        final_counts=final_counts,
        peak_velocity=final.peak_velocity,
        total_transitions=total_transitions,
    )


def _empty_report(config: SimulationConfig) -> str:
    """Return a placeholder report when no simulation data is available."""
    return (
        "# Simulation Report\n\n"
        "## Executive Summary\n\n"
        f'Simulation for "{config.seed_text}" produced no results. '
        "The simulation may not have run any ticks.\n"
    )
