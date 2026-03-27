"""Per-tick analytics computation."""

import numpy as np
from pydantic import BaseModel

from narrativeflow.engine.agents import AgentPopulation
from narrativeflow.engine.narratives import NarrativeTracker


class CommunityBreakdown(BaseModel):
    """SMIR state counts for a single community."""

    community_id: int
    S: int = 0
    M: int = 0
    I: int = 0  # noqa: E741
    R: int = 0


class TickMetrics(BaseModel):
    """Metrics computed at each simulation tick."""

    tick: int
    state_counts: dict[str, int]
    spread_rate: float = 0.0
    peak_velocity: float = 0.0
    active_narratives: int = 0
    dominant_narrative_id: str | None = None
    cascade_depth: int = 0
    community_breakdown: list[CommunityBreakdown] = []
    top_spreaders: list[dict[str, float]] = []
    intervention_active: bool = False


def compute_tick_metrics(
    agents: AgentPopulation,
    tick: int,
    tracker: NarrativeTracker,
    prev_metrics: TickMetrics | None = None,
    transition_counts: dict[str, int] | None = None,
) -> TickMetrics:
    """Compute all metrics for the current tick.

    Args:
        agents: Current agent population state.
        tick: Current tick number.
        tracker: Narrative tracker with active narratives.
        prev_metrics: Metrics from previous tick (for peak velocity).
        transition_counts: Dict of transitions this tick.
    """
    state_counts = agents.get_state_counts()

    # Spread rate: new M agents this tick / total S last tick
    spread_rate = 0.0
    if transition_counts:
        new_misinformed = transition_counts.get("S_to_M", 0)
        prev_s = (prev_metrics.state_counts["S"] if prev_metrics else agents.n)
        if prev_s > 0:
            spread_rate = new_misinformed / prev_s

    # Peak velocity
    peak_velocity = spread_rate
    if prev_metrics and prev_metrics.peak_velocity > peak_velocity:
        peak_velocity = prev_metrics.peak_velocity

    # Narrative info
    active_narratives = tracker.get_active_count()
    dominant = tracker.get_dominant()
    dominant_id = dominant.id if dominant else None

    # Cascade depth: max lineage length
    cascade_depth = 0
    for n in tracker.narratives.values():
        if len(n.lineage) > cascade_depth:
            cascade_depth = len(n.lineage)

    # Community breakdown
    community_breakdown = _compute_community_breakdown(agents)

    # Top spreaders: agents in M state with highest influence
    top_spreaders = _compute_top_spreaders(agents, limit=5)

    return TickMetrics(
        tick=tick,
        state_counts=state_counts,
        spread_rate=round(spread_rate, 6),
        peak_velocity=round(peak_velocity, 6),
        active_narratives=active_narratives,
        dominant_narrative_id=dominant_id,
        cascade_depth=cascade_depth,
        community_breakdown=community_breakdown,
        top_spreaders=top_spreaders,
    )


def _compute_community_breakdown(agents: AgentPopulation) -> list[CommunityBreakdown]:
    """Compute SMIR state counts per community."""
    communities = np.unique(agents.community_id)
    breakdowns = []
    for cid in communities:
        mask = agents.community_id == cid
        states = agents.states[mask]
        breakdowns.append(
            CommunityBreakdown(
                community_id=int(cid),
                S=int((states == 0).sum()),
                M=int((states == 1).sum()),
                I=int((states == 2).sum()),
                R=int((states == 3).sum()),
            )
        )
    return breakdowns


def _compute_top_spreaders(agents: AgentPopulation, limit: int = 5) -> list[dict[str, float]]:
    """Find agents in M state with highest influence scores."""
    m_mask = agents.states == 1
    if not np.any(m_mask):
        return []

    m_indices = np.where(m_mask)[0]
    m_influence = agents.influence_score[m_mask]

    # Top N by influence
    n_top = min(limit, len(m_indices))
    top_idx = np.argsort(m_influence)[-n_top:][::-1]

    return [
        {"agent_id": int(m_indices[i]), "influence": float(m_influence[i])}
        for i in top_idx
    ]
