"""Agent population managed as numpy arrays for vectorized computation."""

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field

# SMIR states (I is standard epidemiological notation)
S, M, I, R = 0, 1, 2, 3  # noqa: E741
STATE_LABELS = {S: "Susceptible", M: "Misinformed", I: "Informed", R: "Resistant"}


class ArchetypeConfig(BaseModel):
    """Archetype parameters used to initialize agent traits."""

    id: int = 0
    name: str = "Default"
    susceptibility: float = Field(default=0.5, ge=0.0, le=1.0)
    sharing_tendency: float = Field(default=0.5, ge=0.0, le=1.0)
    trust_mainstream_media: float = Field(default=0.5, ge=0.0, le=1.0)
    trust_social_peers: float = Field(default=0.5, ge=0.0, le=1.0)
    emotional_reactivity: float = Field(default=0.5, ge=0.0, le=1.0)
    correction_receptiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    mutation_style: str = "exaggeration"
    population_percentage: float = Field(default=100.0, ge=0.0, le=100.0)


@dataclass
class AgentPopulation:
    """Vectorized agent state stored as numpy arrays.

    All arrays have shape (n,) where n is population size.
    """

    n: int

    # Stable parameters (set at init)
    susceptibility: NDArray[np.float32] = field(init=False)
    trust_threshold: NDArray[np.float32] = field(init=False)
    activity_rate: NDArray[np.float32] = field(init=False)
    influence_score: NDArray[np.float32] = field(init=False)
    open_mindedness: NDArray[np.float32] = field(init=False)
    emotional_reactivity: NDArray[np.float32] = field(init=False)
    archetype_id: NDArray[np.int32] = field(init=False)
    community_id: NDArray[np.int32] = field(init=False)

    # Dynamic state (changes per tick)
    states: NDArray[np.int8] = field(init=False)
    confidence: NDArray[np.float32] = field(init=False)
    ticks_in_state: NDArray[np.int32] = field(init=False)
    exposure_count: NDArray[np.int32] = field(init=False)
    last_active_tick: NDArray[np.int32] = field(init=False)

    # Narrative tracking (per agent)
    narrative_ids: list[str | None] = field(init=False)

    def __post_init__(self) -> None:
        self.susceptibility = np.zeros(self.n, dtype=np.float32)
        self.trust_threshold = np.zeros(self.n, dtype=np.float32)
        self.activity_rate = np.full(self.n, 0.5, dtype=np.float32)
        self.influence_score = np.zeros(self.n, dtype=np.float32)
        self.open_mindedness = np.zeros(self.n, dtype=np.float32)
        self.emotional_reactivity = np.zeros(self.n, dtype=np.float32)
        self.archetype_id = np.zeros(self.n, dtype=np.int32)
        self.community_id = np.zeros(self.n, dtype=np.int32)

        self.states = np.zeros(self.n, dtype=np.int8)  # all start Susceptible
        self.confidence = np.zeros(self.n, dtype=np.float32)
        self.ticks_in_state = np.zeros(self.n, dtype=np.int32)
        self.exposure_count = np.zeros(self.n, dtype=np.int32)
        self.last_active_tick = np.full(self.n, -1, dtype=np.int32)
        self.narrative_ids = [None] * self.n

    @classmethod
    def from_archetypes(
        cls,
        archetypes: list[ArchetypeConfig],
        n: int,
        influence_scores: NDArray[np.float32],
        community_ids: NDArray[np.int32],
        rng: np.random.Generator | None = None,
    ) -> "AgentPopulation":
        """Create a population with traits distributed by archetype percentages.

        Args:
            archetypes: List of archetype configurations.
            n: Total population size.
            influence_scores: Per-node influence from graph centrality.
            community_ids: Per-node community assignment.
            rng: Random number generator for reproducibility.
        """
        if rng is None:
            rng = np.random.default_rng()

        pop = cls(n)
        pop.influence_score = influence_scores.astype(np.float32)
        pop.community_id = community_ids.astype(np.int32)

        # Assign archetypes to agents based on population percentages
        assignments = _assign_archetypes(archetypes, n, rng)

        # Vectorized assignment from archetype configs
        for arch in archetypes:
            mask = np.array([assignments[i] == arch.id for i in range(n)])
            count = int(mask.sum())
            if count == 0:
                continue

            pop.archetype_id[mask] = arch.id
            # Add per-agent variation (±10%) around archetype baseline via beta distribution
            pop.susceptibility[mask] = _varied(arch.susceptibility, count, rng)
            pop.trust_threshold[mask] = _varied(arch.trust_mainstream_media, count, rng)
            pop.activity_rate[mask] = _varied(arch.sharing_tendency, count, rng)
            pop.open_mindedness[mask] = _varied(arch.correction_receptiveness, count, rng)
            pop.emotional_reactivity[mask] = _varied(arch.emotional_reactivity, count, rng)

        return pop

    def get_state_counts(self) -> dict[str, int]:
        """Return count of agents in each SMIR state."""
        unique, counts = np.unique(self.states, return_counts=True)
        result = {"S": 0, "M": 0, "I": 0, "R": 0}
        label_map = {S: "S", M: "M", I: "I", R: "R"}
        for state, count in zip(unique, counts, strict=False):
            result[label_map[int(state)]] = int(count)
        return result

    def get_by_state(self, state: int) -> NDArray[np.bool_]:
        """Return boolean mask of agents in the given state."""
        result: NDArray[np.bool_] = self.states == state
        return result

    def increment_ticks_in_state(self) -> None:
        """Increment ticks_in_state for all non-Susceptible agents."""
        non_s = self.states != S
        self.ticks_in_state[non_s] += 1


def _assign_archetypes(
    archetypes: list[ArchetypeConfig], n: int, rng: np.random.Generator
) -> NDArray[np.int32]:
    """Assign archetype IDs to n agents based on population percentages."""
    assignments = np.zeros(n, dtype=np.int32)
    total_pct = sum(a.population_percentage for a in archetypes)
    if total_pct == 0:
        return assignments

    idx = 0
    for arch in archetypes:
        count = int(round(n * arch.population_percentage / total_pct))
        count = min(count, n - idx)  # don't overflow
        assignments[idx : idx + count] = arch.id
        idx += count

    # Fill remaining due to rounding
    if idx < n:
        assignments[idx:] = archetypes[-1].id

    # Shuffle so archetypes aren't spatially clustered
    rng.shuffle(assignments)
    return assignments


def _varied(baseline: float, count: int, rng: np.random.Generator) -> NDArray[np.float32]:
    """Generate per-agent values with ±10% variation around baseline using beta distribution."""
    if baseline <= 0.01:
        return np.full(count, 0.01, dtype=np.float32)
    if baseline >= 0.99:
        return np.full(count, 0.99, dtype=np.float32)

    # Beta distribution centered on baseline with concentration ~50 (tight spread)
    alpha = baseline * 50
    beta = (1 - baseline) * 50
    values = rng.beta(alpha, beta, count).astype(np.float32)
    return np.clip(values, 0.0, 1.0)
