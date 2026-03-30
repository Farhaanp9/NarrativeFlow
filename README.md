# NarrativeFlow

**A predictive simulation engine for modeling how misinformation spreads through social networks.**

NarrativeFlow orchestrates thousands of AI-driven agents — each with unique personalities, trust thresholds, and media consumption habits — to simulate the lifecycle of narratives across digital populations. Seed the system with a real-world scenario, and watch how stories spread, mutate, and cascade through a simulated social network in real time.

No existing tool answers the fundamental question: *"If this story breaks tomorrow, how will it spread, mutate, and what can we do to stop it?"* NarrativeFlow does.

---

## Why This Matters

Misinformation is the defining information challenge of our era. MIT Media Lab's landmark study found that falsehoods are **70% more likely to be shared** than the truth, reach people **6x faster**, and hit cascade depth **20x quicker**. The 2024 US election saw a single voter fraud claim reach 30M+ views before any fact-check could respond.

The current defense ecosystem is fundamentally **reactive** — platforms like Blackbird.AI and Cyabra detect misinformation *after* it's already spreading, fact-checkers publish corrections *after* millions have been exposed, and content moderation plays whack-a-mole *after* the damage is done.

NarrativeFlow flips this paradigm. It's a **predictive war-gaming sandbox** that lets organizations stress-test information ecosystems *before* real damage occurs. Communications teams can simulate how a crisis narrative might spread. Election security analysts can war-game disinformation campaigns. Researchers can study how network structure affects vulnerability to false narratives.

## How It Works

A user enters a headline or claim — say, *"New study links popular sweetener to cancer risk"* — and configures a simulated population. NarrativeFlow then:

1. **Generates behavioral archetypes** via LLM — skeptics, amplifiers, conspiracy theorists, passive consumers, active debunkers — each with calibrated psychological profiles
2. **Builds a social network** using one of three topology models (scale-free, small-world, or modular communities) that mirror real platform dynamics
3. **Runs a tick-based simulation** where agents share, distort, debunk, or ignore the narrative based on their traits and network position
4. **Mutates narratives** as they propagate — stories evolve through exaggeration, conspiracy framing, political reframing, and decontextualization as they pass through different population segments
5. **Produces an analytical report** identifying vulnerability hotspots, optimal intervention windows, and which network structures proved most resilient

The entire simulation runs in a browser with a real-time WebGL network visualization showing misinformation (red) spreading through susceptible agents (green), corrections (blue) fighting back, and beliefs hardening into resistant states (gray).

## The Science: SMIR Propagation Model

NarrativeFlow introduces a novel **SMIR** (Susceptible, Misinformed, Informed, Resistant) propagation model, extending classical epidemiological SIR for information dynamics. Unlike standard SIR, SMIR has two competing "infection" pathways — misinformation and truth — and a belief-hardening mechanic.

**State transitions:**

- **S to M** (Susceptible becomes Misinformed) — Driven by exposure to misinformed neighbors, weighted by susceptibility, narrative virality, emotional charge, and connection strength. Calibrated so misinformation transmits faster than truth, matching the MIT finding.
- **S to I** (Susceptible becomes Informed) — Truth spreads through informed neighbors, weighted by trust in source and credibility of the corrector.
- **M to I** (Correction succeeds) — An informed neighbor can correct a misinformed agent, but effectiveness decreases as belief confidence grows over time. The longer someone holds a false belief, the harder it is to correct.
- **M/I to R** (Belief hardens) — After enough time in any belief state, agents become Resistant — their view is locked in and they stop changing. This models the well-documented "continued influence effect."

**Key dynamics the model captures:**

- **Asymmetric transmission** — Misinformation spreads inherently faster than corrections
- **Novelty decay** — Narrative virality decreases over time as stories become "old news"
- **Confidence accumulation** — The longer an agent holds a belief, the more resistant they become to changing it
- **Emotional contagion** — High emotional charge narratives temporarily boost susceptibility in nearby agents
- **Network amplification** — Bridge nodes with high betweenness centrality amplify spread across communities
- **Narrative mutation** — Stories evolve as they pass through agents with different mutation styles (exaggeration, conspiracy framing, fabrication, political reframing)

All transitions are computed as vectorized numpy operations across the entire population per tick, enabling 10,000+ agents at 50-100 ticks/second.

## What Makes This Different

| | NarrativeFlow | Detection Platforms (Blackbird.AI, Cyabra) | Academic Frameworks (OASIS, MOSAIC) |
|---|---|---|---|
| **Approach** | Simulate future scenarios | Monitor live social media | Study dynamics in notebooks |
| **Predictive** | Yes | No (reactive only) | No |
| **Narrative mutation** | Tracks how stories evolve | No | No |
| **Intervention testing** | Inject corrections mid-simulation | No | Limited |
| **Accessible** | Web UI anyone can use | Enterprise-only ($$$) | Python notebooks for researchers |
| **Cost** | Free (runs on local LLM) | Enterprise pricing | Free but not productized |
| **Behavioral realism** | Hybrid archetype + math (avoids MOSAIC problem) | Real data | Pure LLM (flawed — agents refuse to share misinfo due to safety training) |

## Architecture

The system is designed as three decoupled layers:

**Simulation Engine** (Python) — The mathematical core. Agent state is stored as numpy arrays for vectorized computation. Social networks are generated with python-igraph supporting three topology models: Barabasi-Albert (scale-free, mimics Twitter/X), Watts-Strogatz (small-world, mimics Facebook), and Stochastic Block Model (modular communities, mimics echo chambers). The engine runs headlessly at 50-100 ticks/second and exposes a clean tick-by-tick API.

**API Layer** (FastAPI) — REST endpoints for simulation lifecycle management (create, pause, resume, step, inspect agents) plus WebSocket broadcasting of per-tick state updates. The LLM integration uses a unified client that works with Ollama locally (free) or any OpenAI-compatible cloud API. When no LLM is available, the system falls back to built-in behavioral archetypes.

**Visualization** (Next.js + Sigma.js) — A real-time WebGL network graph where nodes change color as beliefs propagate, paired with Recharts timelines showing S/M/I/R population curves. Users can pause the simulation, inspect individual agents, adjust speed, and step through ticks one at a time.

```
Frontend (Next.js)              API (FastAPI)                 LLM (Ollama)
Sigma.js WebGL graph    <--->   SMIR Engine (numpy)           Archetype generation
Recharts timelines      WS      python-igraph (graphs)        Narrative mutation
Zustand state           REST    aiosqlite (persistence)       Report synthesis
shadcn/ui controls              Pydantic (validation)
```

## Behavioral Science Foundation

Every parameter in the simulation maps to published research:

- **Transmission asymmetry** calibrated to MIT's "70% more likely to retweet" finding (Vosoughi, Roy, Aral, *Science* 2018)
- **Susceptibility distributions** informed by USC's habitual sharing research — habits drive misinformation sharing more than beliefs or critical reasoning (2025)
- **Emotional reactivity weights** from MIT Media Lab emotion analysis — false news triggers fear, disgust, and surprise while true news triggers anticipation and trust
- **Network topology parameters** from empirical social network studies — 0.25% of X users drove 73-78% of all low-credibility content (2024)
- **Archetype generation** uses the hybrid approach from MIT's LLM archetype methodology (Chopra et al., *AAMAS* 2025), solving the MOSAIC problem where pure LLM agents refuse to share misinformation due to safety training

## Research References

1. Vosoughi, Roy, Aral. "The Spread of True and False News Online." *Science*, 2018
2. Chopra et al. "On the Limits of Agency in Agent-Based Models." *AAMAS*, 2025
3. OASIS: Open Agent Social Interaction Simulations. CAMEL-AI, 2024
4. MOSAIC: Modeling Social AI for Content Dissemination. *EMNLP*, 2025
5. Epidemic modeling for misinformation spread. *Nature Scientific Reports*, 2024
6. USC Study on habitual sharing, 2025

---

See [NarrativeFlow-PRD.md](NarrativeFlow-PRD.md) for the full technical specification including data models, API contracts, and validation methodology.
