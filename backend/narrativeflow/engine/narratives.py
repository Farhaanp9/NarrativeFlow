"""Narrative data models, mutation tracking, and lineage management."""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class MutationType(StrEnum):
    """Types of narrative mutation with their effects on virality and emotion."""

    SEED = "seed"
    EXAGGERATION = "exaggeration"
    CONSPIRACY_FRAMING = "conspiracy_framing"
    DECONTEXTUALIZATION = "decontextualization"
    FABRICATION = "fabrication"
    EMOTIONAL_AMPLIFICATION = "emotional_amplification"
    POLITICAL_REFRAMING = "political_reframing"


# PRD Section 10.5: mutation effects on virality and emotional charge
MUTATION_EFFECTS: dict[MutationType, tuple[float, float]] = {
    MutationType.SEED: (0.0, 0.0),
    MutationType.EXAGGERATION: (0.20, 0.10),
    MutationType.CONSPIRACY_FRAMING: (0.40, 0.30),
    MutationType.DECONTEXTUALIZATION: (0.10, -0.05),
    MutationType.FABRICATION: (0.50, 0.40),
    MutationType.EMOTIONAL_AMPLIFICATION: (0.15, 0.50),
    MutationType.POLITICAL_REFRAMING: (0.30, 0.20),
}


class NarrativeSeed(BaseModel):
    """The initial narrative extracted from user's seed text."""

    content: str
    claims: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    tone: str = "neutral"
    category: str = "general"
    virality_estimate: float = Field(default=1.0, ge=0.0, le=2.0)
    emotional_charge: float = Field(default=0.5, ge=0.0, le=1.0)
    novelty_score: float = Field(default=0.5, ge=0.0, le=1.0)


class Narrative(BaseModel):
    """A narrative instance — either the seed or a mutation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    simulation_id: str = ""
    parent_id: str | None = None
    content: str
    mutation_type: MutationType = MutationType.SEED
    emotional_charge: float = Field(default=0.5, ge=0.0, le=1.0)
    virality_modifier: float = Field(default=1.0, ge=0.0)
    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    origin_tick: int = 0
    origin_archetype_id: int | None = None
    spread_count: int = 0
    lineage: list[str] = Field(default_factory=list)


class NarrativeTracker:
    """Manages active narratives during a simulation."""

    def __init__(self) -> None:
        self.narratives: dict[str, Narrative] = {}
        self.seed_id: str | None = None

    def add_seed(self, seed: NarrativeSeed, simulation_id: str) -> Narrative:
        """Create the seed narrative and register it."""
        narrative = Narrative(
            simulation_id=simulation_id,
            content=seed.content,
            mutation_type=MutationType.SEED,
            emotional_charge=seed.emotional_charge,
            virality_modifier=seed.virality_estimate,
            origin_tick=0,
        )
        narrative.lineage = [narrative.id]
        self.narratives[narrative.id] = narrative
        self.seed_id = narrative.id
        return narrative

    def add_mutation(
        self,
        parent_id: str,
        content: str,
        mutation_type: MutationType,
        origin_tick: int,
        origin_archetype_id: int | None = None,
    ) -> Narrative:
        """Create a mutated narrative derived from a parent."""
        parent = self.narratives[parent_id]
        virality_delta, emotion_delta = MUTATION_EFFECTS[mutation_type]

        narrative = Narrative(
            simulation_id=parent.simulation_id,
            parent_id=parent_id,
            content=content,
            mutation_type=mutation_type,
            emotional_charge=min(1.0, max(0.0, parent.emotional_charge + emotion_delta)),
            virality_modifier=parent.virality_modifier * (1.0 + virality_delta),
            origin_tick=origin_tick,
            origin_archetype_id=origin_archetype_id,
            lineage=[*parent.lineage, ""],  # placeholder, set below
        )
        narrative.lineage[-1] = narrative.id
        self.narratives[narrative.id] = narrative
        return narrative

    def get_active_count(self) -> int:
        """Return number of narratives with nonzero spread."""
        return sum(1 for n in self.narratives.values() if n.spread_count > 0)

    def get_dominant(self) -> Narrative | None:
        """Return the narrative with the highest spread count."""
        if not self.narratives:
            return None
        return max(self.narratives.values(), key=lambda n: n.spread_count)

    def update_spread_counts(self, narrative_ids: list[str | None]) -> None:
        """Recompute spread counts from agent narrative assignments."""
        for n in self.narratives.values():
            n.spread_count = 0
        for nid in narrative_ids:
            if nid is not None and nid in self.narratives:
                self.narratives[nid].spread_count += 1
