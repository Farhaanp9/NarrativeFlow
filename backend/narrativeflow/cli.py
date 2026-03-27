"""Typer CLI entry point for NarrativeFlow."""

import asyncio
import sys
from typing import Annotated

import typer

from narrativeflow import __version__

app = typer.Typer(
    name="narrativeflow",
    help="NarrativeFlow — Multi-agent misinformation simulation engine",
)


@app.command()
def version() -> None:
    """Print the current version."""
    typer.echo(f"NarrativeFlow v{__version__}")


@app.command()
def simulate(
    seed_text: Annotated[str, typer.Argument(help="Headline or claim to simulate")],
    agents: Annotated[int, typer.Option(help="Population size")] = 500,
    ticks: Annotated[int, typer.Option(help="Maximum ticks")] = 100,
    topology: Annotated[str, typer.Option(help="Graph topology")] = "barabasi_albert",
    archetypes: Annotated[int, typer.Option(help="Number of archetypes")] = 15,
    seed: Annotated[int | None, typer.Option(help="RNG seed")] = None,
) -> None:
    """Run a simulation from the command line."""
    asyncio.run(_simulate_async(
        seed_text, agents, ticks, topology, archetypes, seed
    ))


async def _simulate_async(
    seed_text: str,
    agents_count: int,
    max_ticks: int,
    topology: str,
    archetype_count: int,
    rng_seed: int | None,
) -> None:
    """Async simulation runner for CLI."""
    from narrativeflow.config import get_settings
    from narrativeflow.engine.agents import ArchetypeConfig
    from narrativeflow.engine.graph import Topology
    from narrativeflow.engine.narratives import NarrativeSeed
    from narrativeflow.engine.simulation import (
        SimulationConfig,
        SimulationEngine,
    )
    from narrativeflow.llm.client import LLMClient

    settings = get_settings()
    llm = LLMClient(settings)

    typer.echo(f"NarrativeFlow v{__version__}")
    typer.echo(f"Seed: \"{seed_text}\"")
    typer.echo(
        f"Config: {agents_count} agents, {max_ticks} ticks, "
        f"{topology} topology"
    )
    typer.echo("")

    # 1. Generate archetypes
    typer.echo("Generating archetypes...")
    profiles = await llm.generate_archetypes(seed_text, archetype_count)
    typer.echo(f"  Generated {len(profiles)} archetypes:")
    for p in profiles:
        typer.echo(
            f"    - {p.name} ({p.population_percentage:.0f}%)"
        )
    typer.echo("")

    # Convert to engine format
    engine_archetypes = [
        ArchetypeConfig(
            id=i,
            name=p.name,
            susceptibility=p.susceptibility,
            sharing_tendency=p.sharing_tendency,
            trust_mainstream_media=p.trust_mainstream_media,
            trust_social_peers=p.trust_social_peers,
            emotional_reactivity=p.emotional_reactivity,
            correction_receptiveness=p.correction_receptiveness,
            mutation_style=p.mutation_style.value,
            population_percentage=p.population_percentage,
        )
        for i, p in enumerate(profiles)
    ]

    # 2. Extract narrative
    typer.echo("Extracting narrative...")
    narrative_output = await llm.extract_narrative(seed_text)
    seed_narrative = NarrativeSeed(
        content=narrative_output.primary_claim or seed_text,
        claims=[
            narrative_output.primary_claim,
            *narrative_output.secondary_claims,
        ],
        entities=narrative_output.entities,
        tone=narrative_output.tone,
        category=narrative_output.category,
        virality_estimate=narrative_output.virality_estimate,
        emotional_charge=narrative_output.emotional_charge,
        novelty_score=narrative_output.novelty_score,
    )
    typer.echo(
        f"  Virality: {seed_narrative.virality_estimate:.2f}, "
        f"Emotion: {seed_narrative.emotional_charge:.2f}"
    )
    typer.echo("")

    # 3. Run simulation
    try:
        topo = Topology(topology)
    except ValueError:
        typer.echo(
            f"Invalid topology '{topology}'. "
            f"Use: barabasi_albert, watts_strogatz, "
            f"stochastic_block_model",
            err=True,
        )
        raise typer.Exit(code=1)  # noqa: B904

    config = SimulationConfig(
        seed_text=seed_text,
        population_size=agents_count,
        topology=topo,
        max_ticks=max_ticks,
        seed=rng_seed,
    )
    engine = SimulationEngine(config)
    engine.initialize(engine_archetypes, seed_narrative)

    typer.echo(f"Running simulation ({agents_count} agents)...")

    def on_tick(metrics: object) -> None:
        from narrativeflow.engine.metrics import TickMetrics

        assert isinstance(metrics, TickMetrics)
        counts = metrics.state_counts
        bar_width = 40
        total = sum(counts.values()) or 1
        s_w = int(counts["S"] / total * bar_width)
        m_w = int(counts["M"] / total * bar_width)
        i_w = int(counts["I"] / total * bar_width)
        r_w = bar_width - s_w - m_w - i_w

        bar = (
            f"\r  Tick {metrics.tick:>4d}/{max_ticks} "
            f"[{'█' * s_w}{'░' * m_w}{'▓' * i_w}{'▒' * r_w}] "
            f"S:{counts['S']:>4d} M:{counts['M']:>4d} "
            f"I:{counts['I']:>4d} R:{counts['R']:>4d}"
        )
        sys.stdout.write(bar)
        sys.stdout.flush()

    result = engine.run(on_tick=on_tick)

    typer.echo("")  # newline after progress bar
    typer.echo("")
    typer.echo("Simulation Complete")
    typer.echo(f"  Total ticks: {result.total_ticks}")
    typer.echo(f"  Final state: {result.final_state_counts}")
    typer.echo(f"  Peak velocity: {result.peak_velocity:.4f}")
    typer.echo(f"  Transitions: {result.total_transitions}")
    typer.echo("")

    # 4. Generate report
    typer.echo("Generating report...")
    report = await llm.generate_report(
        seed_text=seed_text,
        population_size=agents_count,
        topology=topology,
        total_ticks=result.total_ticks,
        final_counts=result.final_state_counts,
        peak_velocity=result.peak_velocity,
        total_transitions=result.total_transitions,
    )
    typer.echo("")
    typer.echo(report)


if __name__ == "__main__":
    app()
