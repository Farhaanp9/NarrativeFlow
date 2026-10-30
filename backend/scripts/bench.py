"""Engine throughput benchmark: no LLM, no API, no database.

For each topology and population size, builds the graph and agents with
the built-in archetypes (what the app uses when no LLM is reachable), then
times a fixed number of ticks, continuing past convergence. Prints one row
per configuration with the median over the runs.

Usage: cd backend && uv run python scripts/bench.py [--ticks 100] [--runs 3]
"""

import argparse
import platform
import statistics
import time

from narrativeflow.engine.agents import ArchetypeConfig
from narrativeflow.engine.graph import Topology
from narrativeflow.engine.simulation import SimulationConfig, SimulationEngine
from narrativeflow.llm.client import _get_default_archetypes


def default_archetypes() -> list[ArchetypeConfig]:
    return [
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
        for i, p in enumerate(_get_default_archetypes(8))
    ]


def run_once(topology: Topology, n: int, ticks: int, seed: int) -> tuple[float, float]:
    """Return (setup seconds, seconds for `ticks` ticks)."""
    config = SimulationConfig(
        seed_text="bench", population_size=n, topology=topology, seed=seed
    )
    engine = SimulationEngine(config)
    start = time.perf_counter()
    engine.initialize(default_archetypes())
    setup = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(ticks):
        engine.tick()
    return setup, time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--sizes", type=int, nargs="+", default=[1000, 5000, 10000])
    args = parser.parse_args()

    print(f"Python {platform.python_version()} on {platform.platform()}")
    print(f"{args.ticks} ticks per run, median of {args.runs} runs (seeds 0..{args.runs - 1})")
    print()
    print(f"{'topology':<24} {'agents':>7} {'setup s':>8} {'tick s':>8} {'ticks/s':>8}")
    for topology in Topology:
        for n in args.sizes:
            results = [run_once(topology, n, args.ticks, seed) for seed in range(args.runs)]
            setup = statistics.median(r[0] for r in results)
            wall = statistics.median(r[1] for r in results)
            rate = statistics.median(args.ticks / r[1] for r in results)
            print(f"{topology.value:<24} {n:>7} {setup:>8.2f} {wall:>8.2f} {rate:>8.1f}")


if __name__ == "__main__":
    main()
