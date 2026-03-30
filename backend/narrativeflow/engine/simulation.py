"""Main simulation engine — tick loop orchestrator."""

from collections.abc import Callable
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from narrativeflow.engine.agents import AgentPopulation, ArchetypeConfig, M
from narrativeflow.engine.graph import GraphData, Topology, TopologyParams, generate_graph
from narrativeflow.engine.metrics import TickMetrics, compute_tick_metrics
from narrativeflow.engine.narratives import (
    MutationType,
    NarrativeSeed,
    NarrativeTracker,
)
from narrativeflow.engine.propagation import (
    PropagationConfig,
    TransitionResult,
    resolve_transitions,
)

# Mutation callback type: (archetype_name, archetype_desc, mutation_style, narrative_content)
# -> (mutated_content, mutation_type_str) or None
MutationCallback = Callable[..., Any]


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""

    seed_text: str
    population_size: int = Field(default=500, ge=10, le=10000)
    topology: Topology = Topology.BARABASI_ALBERT
    topology_params: TopologyParams = Field(default_factory=TopologyParams)
    archetype_count: int = Field(default=15, ge=5, le=30)
    max_ticks: int = Field(default=100, ge=10, le=500)
    tick_speed: float = Field(default=5.0, ge=0.1, le=100.0)
    seed: int | None = None


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
        archetypes: list[ArchetypeConfig] | None = None,
    ) -> None:
        self.config = config
        self.prop_config = propagation_config or PropagationConfig()
        self.rng = np.random.default_rng(config.seed)
        self.archetypes = archetypes or []

        self.agents: AgentPopulation | None = None
        self.graph_data: GraphData | None = None
        self.tracker = NarrativeTracker()
        self.metrics_history: list[TickMetrics] = []
        self.current_tick = 0
        self._total_transitions: dict[str, int] = {
            "S_to_M": 0,
            "S_to_I": 0,
            "M_to_I": 0,
            "to_R": 0,
        }
        self._last_transition_result: TransitionResult | None = None

    def initialize(
        self,
        archetypes: list[ArchetypeConfig],
        seed_narrative: NarrativeSeed | None = None,
    ) -> None:
        """Set up the simulation: generate graph, create agents, seed narrative."""
        self.archetypes = archetypes

        # Generate social network
        self.graph_data = generate_graph(
            self.config.topology,
            self.config.population_size,
            self.config.topology_params,
            seed=self.config.seed,
        )

        # Create agent population with betweenness for network amplification
        self.agents = AgentPopulation.from_archetypes(
            archetypes=archetypes,
            n=self.config.population_size,
            influence_scores=self.graph_data.influence_scores,
            community_ids=self.graph_data.community_ids,
            betweenness=self.graph_data.betweenness,
            rng=self.rng,
        )

        # Initialize seed narrative
        if seed_narrative is None:
            seed_narrative = NarrativeSeed(content=self.config.seed_text)
        narrative = self.tracker.add_seed(seed_narrative, simulation_id="")

        # Seed initial misinformed agents (top influencers, ~1%)
        n_initial = max(1, self.config.population_size // 100)
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
            raise RuntimeError(
                "Simulation not initialized. Call initialize() first."
            )

        self.current_tick += 1

        # Get the dominant narrative's virality and emotional charge
        # (per-agent narrative tracking uses the dominant for simplicity)
        dominant = self.tracker.get_dominant()
        seed_narrative = self.tracker.narratives.get(
            self.tracker.seed_id or ""
        )
        active_narrative = dominant or seed_narrative
        virality = active_narrative.virality_modifier if active_narrative else 1.0
        emotional_charge = (
            active_narrative.emotional_charge if active_narrative else 0.5
        )
        seed_id = self.tracker.seed_id or ""

        # Resolve all transitions for this tick
        transition_result = resolve_transitions(
            agents=self.agents,
            adjacency=self.graph_data.adjacency,
            config=self.prop_config,
            virality=virality,
            emotional_charge=emotional_charge,
            tick=self.current_tick,
            rng=self.rng,
            seed_narrative_id=seed_id,
        )
        self._last_transition_result = transition_result

        # Accumulate transition counts
        for key, val in transition_result.counts.items():
            self._total_transitions[key] += val

        # Update narrative spread counts
        self.tracker.update_spread_counts(self.agents.narrative_ids)

        # Compute metrics
        prev_metrics = (
            self.metrics_history[-1] if self.metrics_history else None
        )
        metrics = compute_tick_metrics(
            self.agents,
            self.current_tick,
            self.tracker,
            prev_metrics,
            transition_result.counts,
        )
        self.metrics_history.append(metrics)

        return metrics

    def apply_mutations(
        self,
        mutations: list[
            tuple[ArchetypeConfig, str, str]
        ],  # (archetype, content, mutation_type)
    ) -> None:
        """Apply narrative mutations generated externally (e.g., by LLM).

        Each mutation creates a new narrative and updates agents of that
        archetype to hold the mutated version.
        """
        if self.agents is None:
            return

        for arch, content, mutation_type_str in mutations:
            # Find the narrative this archetype's agents are currently holding
            arch_mask = self.agents.archetype_id == arch.id
            m_arch_mask = arch_mask & (self.agents.states == M)
            if not np.any(m_arch_mask):
                continue

            # Find the current narrative of these agents
            sample_idx = np.where(m_arch_mask)[0][0]
            current_nid = self.agents.narrative_ids[sample_idx]
            if current_nid is None:
                continue

            # Create mutation
            try:
                mt = MutationType(mutation_type_str)
            except ValueError:
                mt = MutationType.EXAGGERATION

            new_narrative = self.tracker.add_mutation(
                parent_id=current_nid,
                content=content,
                mutation_type=mt,
                origin_tick=self.current_tick,
                origin_archetype_id=arch.id,
            )

            # Update agents of this archetype to hold the new narrative
            for idx in np.where(m_arch_mask)[0]:
                self.agents.narrative_ids[idx] = new_narrative.id

    def should_mutate(self) -> bool:
        """Check if this tick should trigger narrative mutation."""
        return (
            self.current_tick > 0
            and self.current_tick % self.prop_config.mutation_interval == 0
        )

    def get_mutation_candidates(
        self,
    ) -> list[tuple[ArchetypeConfig, str]]:
        """Return (archetype, current_narrative_content) pairs for mutation.

        Only includes archetypes that have agents currently in M state.
        """
        if self.agents is None:
            return []

        candidates: list[tuple[ArchetypeConfig, str]] = []
        for arch in self.archetypes:
            arch_mask = self.agents.archetype_id == arch.id
            m_arch_mask = arch_mask & (self.agents.states == M)
            if not np.any(m_arch_mask):
                continue

            sample_idx = np.where(m_arch_mask)[0][0]
            nid = self.agents.narrative_ids[sample_idx]
            if nid and nid in self.tracker.narratives:
                content = self.tracker.narratives[nid].content
                candidates.append((arch, content))

        return candidates

    def get_changed_indices(self) -> list[int]:
        """Return agent indices that changed state in the last tick."""
        if self._last_transition_result is None:
            return []
        return self._last_transition_result.changed_indices

    def run(
        self,
        on_tick: Callable[[TickMetrics], None] | None = None,
    ) -> SimulationResult:
        """Run the simulation for max_ticks or until convergence.

        Note: This sync method does NOT invoke LLM mutations.
        For LLM-integrated mutation, use tick() + should_mutate() +
        get_mutation_candidates() + apply_mutations() in an async loop.
        """
        if self.agents is None:
            raise RuntimeError(
                "Simulation not initialized. Call initialize() first."
            )

        for _ in range(self.config.max_ticks):
            metrics = self.tick()

            if on_tick is not None:
                on_tick(metrics)

            counts = metrics.state_counts
            if counts["S"] == 0:
                break
            if counts["M"] == 0 and counts["I"] == 0:
                break

        return SimulationResult(
            total_ticks=self.current_tick,
            final_state_counts=self.agents.get_state_counts(),
            peak_velocity=(
                self.metrics_history[-1].peak_velocity
                if self.metrics_history
                else 0.0
            ),
            total_transitions=self._total_transitions,
        )
