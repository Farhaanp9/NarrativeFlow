"""Vectorized SMIR state transition equations.

Implements the propagation model from PRD Section 10.3:
- S → M: misinformation transmission
- S → I: truth transmission
- M → I: correction
- M → R, I → R: belief hardening

PRD 10.4 enhancements:
- Emotional contagion: high emotional charge temporarily boosts susceptibility
- Network amplification: betweenness centrality amplifies spread for bridge nodes
"""

import numpy as np
from numpy.typing import NDArray
from scipy import sparse

from narrativeflow.engine.agents import AgentPopulation, I, M, R, S

# Emotional exposure decay rate per tick
EMOTIONAL_DECAY = 0.8


class PropagationConfig:
    """Global parameters for SMIR propagation model."""

    def __init__(
        self,
        beta_m: float = 0.15,
        beta_i: float = 0.08,
        gamma: float = 0.10,
        hardening_threshold: int = 30,
        hardening_steepness: float = 0.2,
        confidence_lambda: float = 0.05,
        novelty_decay: float = 0.995,
        mutation_interval: int = 20,
    ) -> None:
        self.beta_m = beta_m
        self.beta_i = beta_i
        self.gamma = gamma
        self.hardening_threshold = hardening_threshold
        self.hardening_steepness = hardening_steepness
        self.confidence_lambda = confidence_lambda
        self.novelty_decay = novelty_decay
        self.mutation_interval = mutation_interval


def compute_s_to_m(
    agents: AgentPopulation,
    adjacency: sparse.csr_matrix,
    config: PropagationConfig,
    virality: float,
    emotional_charge: float,
    tick: int,
) -> NDArray[np.float32]:
    """Compute P(S→M) for all susceptible agents.

    P(S→M) = 1 - ∏(1 - β_M × s_i × v_n × e_n × w_ij) for each M neighbor j

    Includes:
    - Novelty decay on virality
    - Emotional contagion: susceptibility boosted by emotional_exposure
    - Network amplification: M neighbors weighted by (1 + betweenness)
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    s_mask = agents.get_by_state(S)

    if not np.any(s_mask):
        return probs

    m_mask = agents.get_by_state(M)
    if not np.any(m_mask):
        return probs

    # Novelty decay
    effective_virality = virality * (config.novelty_decay ** tick)

    # Network amplification: weight M neighbors by (1 + betweenness)
    m_weighted = m_mask.astype(np.float32) * (1.0 + agents.betweenness)
    m_neighbor_weight = np.asarray(adjacency.dot(m_weighted)).flatten()

    # Emotional contagion: boost susceptibility by emotional_exposure
    effective_susceptibility = agents.susceptibility * (1.0 + agents.emotional_exposure)
    effective_susceptibility = np.clip(effective_susceptibility, 0.0, 1.0)

    # Per-agent base probability
    base_p = (
        config.beta_m * effective_susceptibility * effective_virality * emotional_charge
    )
    base_p = np.clip(base_p, 0.0, 0.99)

    # P(S→M) = 1 - (1 - base_p)^(weighted_m_neighbors)
    survival = np.power(1.0 - base_p, m_neighbor_weight)
    probs = 1.0 - survival

    probs[~s_mask] = 0.0
    result: NDArray[np.float32] = probs.astype(np.float32)
    return result


def compute_s_to_i(
    agents: AgentPopulation,
    adjacency: sparse.csr_matrix,
    config: PropagationConfig,
    correction_strength: float = 0.5,
) -> NDArray[np.float32]:
    """Compute P(S→I) for all susceptible agents.

    P(S→I) = 1 - ∏(1 - β_I × t_i × c_n × cr_j × w_ij) for each I neighbor j
    Includes network amplification via influence + betweenness.
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    s_mask = agents.get_by_state(S)
    i_mask = agents.get_by_state(I)

    if not np.any(s_mask) or not np.any(i_mask):
        return probs

    # Weighted I neighbors: influence + betweenness amplification
    i_weight = i_mask.astype(np.float32) * (
        agents.influence_score + agents.betweenness
    )
    i_neighbor_weight = np.asarray(adjacency.dot(i_weight)).flatten()

    base_p = config.beta_i * agents.trust_threshold * correction_strength
    base_p = np.clip(base_p, 0.0, 0.99)

    i_neighbor_count = np.asarray(
        adjacency.dot(i_mask.astype(np.float32))
    ).flatten()
    survival = np.power(
        1.0 - base_p, i_neighbor_count * (1.0 + i_neighbor_weight)
    )
    probs = 1.0 - survival

    probs[~s_mask] = 0.0
    result: NDArray[np.float32] = probs.astype(np.float32)
    return result


def compute_m_to_i(
    agents: AgentPopulation,
    adjacency: sparse.csr_matrix,
    config: PropagationConfig,
) -> NDArray[np.float32]:
    """Compute P(M→I) for all misinformed agents.

    P(M→I) = 1 - ∏(1 - γ × o_i × cr_j × (1 - conf_i) × w_ij) for each I neighbor j
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    m_mask = agents.get_by_state(M)
    i_mask = agents.get_by_state(I)

    if not np.any(m_mask) or not np.any(i_mask):
        return probs

    confidence = compute_confidence(
        agents.ticks_in_state, config.confidence_lambda
    )

    i_neighbor_count = np.asarray(
        adjacency.dot(i_mask.astype(np.float32))
    ).flatten()

    base_p = config.gamma * agents.open_mindedness * (1.0 - confidence)
    base_p = np.clip(base_p, 0.0, 0.99)

    survival = np.power(1.0 - base_p, i_neighbor_count)
    probs = 1.0 - survival

    probs[~m_mask] = 0.0
    result: NDArray[np.float32] = probs.astype(np.float32)
    return result


def compute_hardening(
    agents: AgentPopulation,
    config: PropagationConfig,
) -> NDArray[np.float32]:
    """Compute P(X→R) for M and I agents (belief hardening).

    P(X→R) = σ(ticks_in_state - hardening_threshold)
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    mi_mask = (agents.states == M) | (agents.states == I)

    if not np.any(mi_mask):
        return probs

    x = agents.ticks_in_state.astype(np.float32) - config.hardening_threshold
    probs = 1.0 / (1.0 + np.exp(-config.hardening_steepness * x))

    probs[~mi_mask] = 0.0
    result: NDArray[np.float32] = probs.astype(np.float32)
    return result


def compute_confidence(
    ticks_in_state: NDArray[np.int32],
    lambda_: float,
) -> NDArray[np.float32]:
    """Confidence accumulation: conf(t) = 1 - e^(-λ*t)."""
    result: NDArray[np.float32] = (
        1.0 - np.exp(-lambda_ * ticks_in_state.astype(np.float32))
    ).astype(np.float32)
    return result


class TransitionResult:
    """Result of one tick of SMIR transitions."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {
            "S_to_M": 0,
            "S_to_I": 0,
            "M_to_I": 0,
            "to_R": 0,
        }
        self.changed_indices: list[int] = []


def resolve_transitions(
    agents: AgentPopulation,
    adjacency: sparse.csr_matrix,
    config: PropagationConfig,
    virality: float,
    emotional_charge: float,
    tick: int,
    rng: np.random.Generator,
    seed_narrative_id: str,
    correction_strength: float = 0.5,
) -> TransitionResult:
    """Execute one tick of SMIR transitions for the entire population.

    Returns TransitionResult with counts and list of changed agent indices.
    """
    n = agents.n
    result = TransitionResult()

    # Determine which agents are active this tick
    active = rng.random(n) < agents.activity_rate

    # 1. Compute all transition probabilities
    p_s_to_m = compute_s_to_m(
        agents, adjacency, config, virality, emotional_charge, tick
    )
    p_s_to_i = compute_s_to_i(agents, adjacency, config, correction_strength)
    p_m_to_i = compute_m_to_i(agents, adjacency, config)
    p_hardening = compute_hardening(agents, config)

    # Only active agents can transition
    p_s_to_m *= active
    p_s_to_i *= active
    p_m_to_i *= active
    p_hardening *= active

    # 2. Stochastic resolution
    rolls = rng.random(n).astype(np.float32)

    s_to_m = (agents.states == S) & (rolls < p_s_to_m)
    s_to_i = (agents.states == S) & ~s_to_m & (rolls < p_s_to_i)
    m_to_i = (agents.states == M) & (rolls < p_m_to_i)
    hardening_rolls = rng.random(n).astype(np.float32)
    to_r = (
        ((agents.states == M) | (agents.states == I))
        & ~m_to_i
        & (hardening_rolls < p_hardening)
    )

    # 3. Apply transitions and record history
    if np.any(s_to_m):
        agents.record_transitions(s_to_m, tick, S, M)
        agents.states[s_to_m] = M
        agents.ticks_in_state[s_to_m] = 0
        agents.confidence[s_to_m] = 0.0
        agents.exposure_count[s_to_m] += 1
        for idx in np.where(s_to_m)[0]:
            agents.narrative_ids[idx] = seed_narrative_id
            result.changed_indices.append(int(idx))
        result.counts["S_to_M"] = int(s_to_m.sum())

    if np.any(s_to_i):
        agents.record_transitions(s_to_i, tick, S, I)
        agents.states[s_to_i] = I
        agents.ticks_in_state[s_to_i] = 0
        agents.confidence[s_to_i] = 0.0
        agents.exposure_count[s_to_i] += 1
        for idx in np.where(s_to_i)[0]:
            result.changed_indices.append(int(idx))
        result.counts["S_to_I"] = int(s_to_i.sum())

    if np.any(m_to_i):
        agents.record_transitions(m_to_i, tick, M, I)
        agents.states[m_to_i] = I
        agents.ticks_in_state[m_to_i] = 0
        agents.confidence[m_to_i] = 0.0
        for idx in np.where(m_to_i)[0]:
            result.changed_indices.append(int(idx))
        result.counts["M_to_I"] = int(m_to_i.sum())

    if np.any(to_r):
        # Record with correct from_state per agent
        m_to_r = to_r & (agents.states == M)
        i_to_r = to_r & (agents.states == I)
        if np.any(m_to_r):
            agents.record_transitions(m_to_r, tick, M, R)
        if np.any(i_to_r):
            agents.record_transitions(i_to_r, tick, I, R)
        agents.states[to_r] = R
        agents.ticks_in_state[to_r] = 0
        for idx in np.where(to_r)[0]:
            result.changed_indices.append(int(idx))
        result.counts["to_R"] = int(to_r.sum())

    # 4. Emotional contagion: boost neighbors of newly-M agents
    if np.any(s_to_m):
        new_m_vec = s_to_m.astype(np.float32) * emotional_charge
        exposure_boost = np.asarray(adjacency.dot(new_m_vec)).flatten()
        agents.emotional_exposure += (
            exposure_boost * agents.emotional_reactivity
        ).astype(np.float32)
        agents.emotional_exposure = np.clip(
            agents.emotional_exposure, 0.0, 1.0
        )

    # 5. Decay emotional exposure
    agents.emotional_exposure *= EMOTIONAL_DECAY

    # 6. Increment ticks in state and update active tick
    agents.increment_ticks_in_state()
    agents.last_active_tick[active] = tick

    return result
