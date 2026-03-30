"""Pydantic request/response schemas for the API."""


from pydantic import BaseModel, Field

from narrativeflow.engine.graph import Topology, TopologyParams


class SimulationCreateRequest(BaseModel):
    """Request body for creating a new simulation."""

    seed_text: str = Field(min_length=1, max_length=5000)
    population_size: int = Field(default=500, ge=10, le=10000)
    topology: Topology = Topology.BARABASI_ALBERT
    topology_params: TopologyParams = Field(default_factory=TopologyParams)
    archetype_count: int = Field(default=15, ge=5, le=30)
    max_ticks: int = Field(default=100, ge=10, le=500)
    tick_speed: float = Field(default=5.0, ge=0.1, le=100.0)


class SimulationSummary(BaseModel):
    """Brief simulation info for list views."""

    id: str
    status: str
    seed_text: str
    population_size: int
    topology: str
    current_tick: int
    created_at: str


class SimulationDetail(BaseModel):
    """Full simulation detail including metrics."""

    id: str
    status: str
    seed_text: str
    population_size: int
    topology: str
    max_ticks: int
    current_tick: int
    created_at: str
    completed_at: str | None = None
    final_state_counts: dict[str, int] | None = None
    peak_velocity: float | None = None
    total_transitions: dict[str, int] | None = None
    metrics_history: list[dict[str, object]] | None = None


class TickUpdate(BaseModel):
    """Per-tick update broadcast via WebSocket."""

    tick: int
    state_counts: dict[str, int]
    spread_rate: float
    peak_velocity: float
    active_narratives: int
    dominant_narrative_id: str | None = None
    hot_nodes: list[int] = Field(default_factory=list)


class SimulationStatusResponse(BaseModel):
    """Response for status-changing operations."""

    id: str
    status: str


class ReportResponse(BaseModel):
    """Response containing the simulation report."""

    simulation_id: str
    content: str
    generated_at: str


class ReportDataResponse(BaseModel):
    """Raw simulation data export."""

    simulation_id: str
    config: dict[str, object]
    final_state_counts: dict[str, int]
    total_transitions: dict[str, int]
    metrics_history: list[dict[str, object]]


class AgentDetailResponse(BaseModel):
    """Detailed info for a single agent."""

    id: int
    archetype_id: int
    archetype_name: str
    state: str
    susceptibility: float
    trust_threshold: float
    influence_score: float
    open_mindedness: float
    emotional_reactivity: float
    community_id: int
    exposure_count: int
    ticks_in_state: int
    confidence: float
    narrative_id: str | None = None
    state_transitions: list[dict[str, object]] = Field(
        default_factory=list
    )
