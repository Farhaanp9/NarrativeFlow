"""Main simulation engine — tick loop orchestrator."""

from collections.abc import Callable

import numpy as np
from pydantic import BaseModel, Field

from narrativeflow.engine.agents import AgentPopulation, ArchetypeConfig, M
from narrativeflow.engine.graph import GraphData, Topology, TopologyParams, generate_graph
from narrativeflow.engine.metrics import TickMetrics, compute_tick_metrics
from narrativeflow.engine.narratives import NarrativeSeed, NarrativeTracker
from narrativeflow.engine.propagation import PropagationConfig, resolve_transitions


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""

    seed_text: str
    population_size: int = Field(default=500, ge=10, le=10000)
    topology: Topology = Topology.BARABASI_ALBERT
    topology_params: TopologyParams = Field(default_factory=TopologyParams)
    archetype_count: int = Field(default=15, ge=5, le=30)
    max_ticks: int = Field(default=100, ge=10, le=500)
    tick_speed: float = Field(default=5.0, ge=0.1, le=100.0)
    seed: int | None = None  # RNG seed for reproducibility


class SimulationResult(BaseModel):
    """Summary of a completed simulation."""

    total_ticks: int
    final_state_counts: dict[str, int]
    peak_velocity: float
    total_transitions: dict[str, int]


class SimulationEngine:
    """Runs the SMIR simulation headlessly."""

    def __init__(
        self,
        config: SimulationConfig,
        propagation_config: PropagationConfig | None = None,
    ) -> None:
        self.config = config
        self.prop_config = propagation_config or PropagationConfig()
        self.rng = np.random.default_rng(config.seed)

        self.agents: AgentPopulation | None = None
        self.graph_data: GraphData | None = None
        self.tracker = NarrativeTracker()
        self.metrics_history: list[TickMetrics] = []
        self.current_tick = 0
        self._total_transitions: dict[str, int] = {
            "S_to_M": 0, "S_to_I": 0, "M_to_I": 0, "to_R": 0,
        }

    def initialize(
        self,
        archetypes: list[ArchetypeConfig],
        seed_narrative: NarrativeSeed | None = None,
    ) -> None:
        """Set up the simulation: generate graph, create agents, seed narrative.

        Args:
            archetypes: Behavioral archetype configurations.
            seed_narrative: The initial narrative. If None, a default is created from config.
        """
        # Generate social network
        self.graph_data = generate_graph(
            self.config.topology,
            self.config.population_size,
            self.config.topology_params,
            seed=self.config.seed,
        )

        # Create agent population from archetypes + graph metrics
        self.agents = AgentPopulation.from_archetypes(
            archetypes=archetypes,
            n=self.config.population_size,
            influence_scores=self.graph_data.influence_scores,
            community_ids=self.graph_data.community_ids,
            rng=self.rng,
        )

        # Initialize seed narrative
        if seed_narrative is None:
            seed_narrative = NarrativeSeed(content=self.config.seed_text)
        narrative = self.tracker.add_seed(seed_narrative, simulation_id="")

        # Seed a few initial misinformed agents (top influencers)
        n_initial = max(1, self.config.population_size // 100)  # ~1% initial seed
        top_influence = np.argsort(self.agents.influence_score)[-n_initial:]
        self.agents.states[top_influence] = M
        for idx in top_influence:
            self.agents.narrative_ids[idx] = narrative.id

        # Record initial metrics
        self.tracker.update_spread_counts(self.agents.narrative_ids)
        initial_metrics = compute_tick_metrics(self.agents, 0, self.tracker)
        self.metrics_history.append(initial_metrics)

    def tick(self) -> TickMetrics:
        """Execute one simulation tick. Returns the metrics for this tick."""
        if self.agents is None or self.graph_data is None:
            raise RuntimeError("Simulation not initialized. Call initialize() first.")

        self.current_tick += 1

        # Get seed narrative info for propagation
        seed_id = self.tracker.seed_id or ""
        seed_narrative = self.tracker.narratives.get(seed_id)
        virality = seed_narrative.virality_modifier if seed_narrative else 1.0
        emotional_charge = seed_narrative.emotional_charge if seed_narrative else 0.5

        # Resolve all transitions for this tick
        transition_counts = resolve_transitions(
            agents=self.agents,
            adjacency=self.graph_data.adjacency,
            config=self.prop_config,
            virality=virality,
            emotional_charge=emotional_charge,
            tick=self.current_tick,
            rng=self.rng,
            seed_narrative_id=seed_id,
        )

        # Accumulate transition counts
        for key, val in transition_counts.items():
            self._total_transitions[key] += val

        # Update narrative spread counts
        self.tracker.update_spread_counts(self.agents.narrative_ids)

        # Compute metrics
        prev_metrics = self.metrics_history[-1] if self.metrics_history else None
        metrics = compute_tick_metrics(
            self.agents, self.current_tick, self.tracker, prev_metrics, transition_counts,
        )
        self.metrics_history.append(metrics)

        return metrics

    def run(
        self,
        on_tick: Callable[[TickMetrics], None] | None = None,
    ) -> SimulationResult:
        """Run the simulation for max_ticks or until convergence.

        Args:
            on_tick: Optional callback invoked after each tick with metrics.

        Returns:
            SimulationResult with final state and statistics.
        """
        if self.agents is None:
            raise RuntimeError("Simulation not initialized. Call initialize() first.")

        for _ in range(self.config.max_ticks):
            metrics = self.tick()

            if on_tick is not None:
                on_tick(metrics)

            # Check convergence: no S agents left, or no M/I activity
            counts = metrics.state_counts
            if counts["S"] == 0:
                break
            if counts["M"] == 0 and counts["I"] == 0:
                break

        return SimulationResult(
            total_ticks=self.current_tick,
            final_state_counts=self.agents.get_state_counts(),
            peak_velocity=self.metrics_history[-1].peak_velocity if self.metrics_history else 0.0,
            total_transitions=self._total_transitions,
        )
