"""Vectorized SMIR state transition equations.

Implements the propagation model from PRD Section 10.3:
- S → M: misinformation transmission
- S → I: truth transmission
- M → I: correction
- M → R, I → R: belief hardening
"""

import numpy as np
from numpy.typing import NDArray
from scipy import sparse

from narrativeflow.engine.agents import AgentPopulation, I, M, R, S


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
    ) -> None:
        # Base misinformation transmission rate (β_M > β_I per MIT finding)
        self.beta_m = beta_m
        # Base truth transmission rate
        self.beta_i = beta_i
        # Correction effectiveness rate
        self.gamma = gamma
        # Ticks before belief starts to harden
        self.hardening_threshold = hardening_threshold
        # Sigmoid steepness for hardening
        self.hardening_steepness = hardening_steepness
        # Confidence accumulation rate: conf(t) = 1 - e^(-λ*t)
        self.confidence_lambda = confidence_lambda
        # Novelty decay per tick: v(t) = v(0) * decay^t
        self.novelty_decay = novelty_decay


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

    With novelty decay applied to virality.
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

    # For each S agent, compute product over M neighbors: ∏(1 - β_M * s_i * v * e * w_ij)
    # Using sparse matrix: sum of log(1 - p_ij) where p_ij = β_M * s_i * v * e * w_ij
    # But w_ij is binary (1 for connected), so we count M neighbors and use per-agent formula

    # Number of M neighbors per agent (via sparse matrix multiply)
    m_vec = m_mask.astype(np.float32)
    m_neighbor_count = np.asarray(adjacency.dot(m_vec)).flatten()

    # Per-agent base probability per M neighbor
    base_p = config.beta_m * agents.susceptibility * effective_virality * emotional_charge
    base_p = np.clip(base_p, 0.0, 0.99)

    # P(S→M) = 1 - (1 - base_p)^(num_m_neighbors)
    survival = np.power(1.0 - base_p, m_neighbor_count)
    probs = 1.0 - survival

    # Only applies to S agents
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
    Simplified: aggregate over I neighbor count with agent trust.
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    s_mask = agents.get_by_state(S)
    i_mask = agents.get_by_state(I)

    if not np.any(s_mask) or not np.any(i_mask):
        return probs

    # Weighted I neighbors: sum of influence scores of I neighbors
    i_influence = (i_mask.astype(np.float32) * agents.influence_score)
    i_neighbor_weight = np.asarray(adjacency.dot(i_influence)).flatten()

    # Per-agent probability
    base_p = config.beta_i * agents.trust_threshold * correction_strength
    base_p = np.clip(base_p, 0.0, 0.99)

    # Use weighted neighbor count as effective number of exposures
    i_neighbor_count = np.asarray(adjacency.dot(i_mask.astype(np.float32))).flatten()
    survival = np.power(1.0 - base_p, i_neighbor_count * (1.0 + i_neighbor_weight))
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

    Confidence grows over time, making correction harder.
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    m_mask = agents.get_by_state(M)
    i_mask = agents.get_by_state(I)

    if not np.any(m_mask) or not np.any(i_mask):
        return probs

    # Confidence accumulation: conf(t) = 1 - e^(-λ * ticks_in_state)
    confidence = compute_confidence(agents.ticks_in_state, config.confidence_lambda)

    # I neighbor count
    i_neighbor_count = np.asarray(
        adjacency.dot(i_mask.astype(np.float32))
    ).flatten()

    # Base correction probability per I neighbor
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
    where σ is sigmoid function.
    """
    n = agents.n
    probs = np.zeros(n, dtype=np.float32)
    mi_mask = (agents.states == M) | (agents.states == I)

    if not np.any(mi_mask):
        return probs

    x = (agents.ticks_in_state.astype(np.float32) - config.hardening_threshold)
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
) -> dict[str, int]:
    """Execute one tick of SMIR transitions for the entire population.

    Returns dict of transition counts: {"S_to_M": n, "S_to_I": n, "M_to_I": n, "to_R": n}
    """
    n = agents.n
    transition_counts = {"S_to_M": 0, "S_to_I": 0, "M_to_I": 0, "to_R": 0}

    # Determine which agents are active this tick
    active = rng.random(n) < agents.activity_rate

    # 1. Compute all transition probabilities
    p_s_to_m = compute_s_to_m(agents, adjacency, config, virality, emotional_charge, tick)
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

    # S → M (misinformation wins over truth if both trigger — misinfo is faster)
    s_to_m = (agents.states == S) & (rolls < p_s_to_m)
    # S → I (only if not already transitioning to M)
    s_to_i = (agents.states == S) & ~s_to_m & (rolls < p_s_to_i)
    # M → I (correction)
    m_to_i = (agents.states == M) & (rolls < p_m_to_i)
    # X → R (hardening) — separate roll to avoid interference
    hardening_rolls = rng.random(n).astype(np.float32)
    to_r = ((agents.states == M) | (agents.states == I)) & ~m_to_i & (hardening_rolls < p_hardening)

    # 3. Apply transitions
    # S → M
    if np.any(s_to_m):
        agents.states[s_to_m] = M
        agents.ticks_in_state[s_to_m] = 0
        agents.confidence[s_to_m] = 0.0
        agents.exposure_count[s_to_m] += 1
        for idx in np.where(s_to_m)[0]:
            agents.narrative_ids[idx] = seed_narrative_id
        transition_counts["S_to_M"] = int(s_to_m.sum())

    # S → I
    if np.any(s_to_i):
        agents.states[s_to_i] = I
        agents.ticks_in_state[s_to_i] = 0
        agents.confidence[s_to_i] = 0.0
        agents.exposure_count[s_to_i] += 1
        transition_counts["S_to_I"] = int(s_to_i.sum())

    # M → I
    if np.any(m_to_i):
        agents.states[m_to_i] = I
        agents.ticks_in_state[m_to_i] = 0
        agents.confidence[m_to_i] = 0.0
        transition_counts["M_to_I"] = int(m_to_i.sum())

    # X → R
    if np.any(to_r):
        agents.states[to_r] = R
        agents.ticks_in_state[to_r] = 0
        transition_counts["to_R"] = int(to_r.sum())

    # 4. Increment ticks in state and update active tick
    agents.increment_ticks_in_state()
    agents.last_active_tick[active] = tick

    return transition_counts
