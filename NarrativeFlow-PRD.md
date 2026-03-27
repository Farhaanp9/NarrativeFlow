# NarrativeFlow — Product Requirements Document (PRD)

**Version:** 1.0
**Author:** Farhaan Pishori
**Date:** March 26, 2026
**Status:** Draft
**Classification:** Internal / Portfolio

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision & Goals](#3-product-vision--goals)
4. [Target Users & Personas](#4-target-users--personas)
5. [Core Features](#5-core-features)
6. [User Flows](#6-user-flows)
7. [System Architecture](#7-system-architecture)
8. [Data Models](#8-data-models)
9. [API Specification](#9-api-specification)
10. [The SMIR Propagation Model](#10-the-smir-propagation-model)
11. [LLM Integration Strategy](#11-llm-integration-strategy)
12. [Frontend Specification](#12-frontend-specification)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Competitive Landscape](#14-competitive-landscape)
15. [Monetization Strategy](#15-monetization-strategy)
16. [Phased Roadmap](#16-phased-roadmap)
17. [Validation & Benchmarking](#17-validation--benchmarking)
18. [Risks & Mitigations](#18-risks--mitigations)
19. [Success Metrics](#19-success-metrics)
20. [Appendix](#20-appendix)

---

## 1. Executive Summary

**NarrativeFlow** is a multi-agent simulation engine that models how information — and misinformation — spreads through social networks. It orchestrates thousands of AI-driven agents, each with unique personalities, trust thresholds, political leanings, and media consumption habits, to simulate the lifecycle of narratives across digital populations.

Users seed the system with a real-world event (a breaking news story, a policy announcement, a market rumor), and NarrativeFlow generates a simulated social network where autonomous agents share, distort, debunk, or amplify narratives. The system identifies which network structures are most vulnerable to false narratives, where optimal intervention points exist, and how quickly corrections can overtake misinformation under different conditions.

**What makes NarrativeFlow different:** Unlike existing tools (Blackbird.AI, Cyabra, Logically) that *detect* misinformation reactively after it's already spreading, NarrativeFlow is a **predictive war-gaming sandbox** — letting organizations stress-test information ecosystems *before* real damage occurs. It also uniquely tracks **narrative mutation** — how stories evolve and distort as they propagate through different population segments.

**Target market:** The counter-misinformation solutions market is projected at $17.29B by 2026 (11.62% CAGR). Gartner has named disinformation security a Top 10 Strategic Technology Trend, predicting 50% of enterprises will adopt solutions by 2028 (up from <5% today).

---

## 2. Problem Statement

### 2.1 The Misinformation Crisis

Misinformation is the defining information challenge of our era. The MIT Media Lab's landmark 2018 study — the largest-ever longitudinal analysis of false news spread — found:

- **Falsehoods are 70% more likely to be retweeted** than the truth
- **False news reaches 1,500 people ~6x faster** than true stories
- **False stories hit cascade depth of 10 about 20x faster** than factual ones
- **Humans, not bots, are the primary spreaders** — false news speeds through networks due to human retweeting behavior, not automated amplification
- **Novelty drives sharing** — false news succeeds because it is perceived as more novel, triggering fear, disgust, and surprise

These dynamics have had real consequences:
- **2024 US Election:** False claims about noncitizen voting, ballot destruction (attributed to Russian operations by the FBI), and the Springfield, Ohio pet-eating hoax all went viral before fact-checks could catch up. One Michigan voter fraud post received 30M+ views.
- **Health misinformation:** A January 2025 video claiming mRNA vaccines "cause serious harm" was viewed by 2.5M people. The poster was subsequently appointed to a CDC advisory panel.
- **AI-generated disinfo:** Chinese-backed influence campaigns used deepfake videos throughout 2024 to spread divisive messaging about US politics.

### 2.2 The Gap in Existing Tools

The current misinformation defense ecosystem is fundamentally **reactive**:

| Current Approach | What It Does | What It Misses |
|-----------------|-------------|---------------|
| **Detection platforms** (Blackbird.AI, Cyabra) | Monitor live social media, identify ongoing narrative attacks | Cannot predict what *would* happen. No simulation capability. |
| **Fact-checking** (Logically, human fact-checkers) | Verify claims after they spread | Too slow — by the time fact-checks publish, false narratives have already cascaded through millions |
| **Content moderation** (ActiveFence, platform tools) | Remove violating content | Whack-a-mole approach — doesn't address the structural vulnerability of the network |
| **Academic research** (MOSAIC, papers) | Study dynamics in controlled settings | Not productizable. MOSAIC found LLM agents *don't behave like humans* with misinformation due to safety training — agents refuse to share false content |

**No existing tool answers the fundamental question: "If this story breaks tomorrow, how will it spread, mutate, and what can we do to stop it?"**

### 2.3 The Behavioral Science Foundation

NarrativeFlow's design is grounded in peer-reviewed behavioral research:

- **Habitual sharing > intentional sharing:** A 2025 USC study found that users' social media habits doubled and tripled the amount of fake news shared — habits were more influential than political beliefs or lack of critical reasoning
- **Inattention, not malice:** There is a large disconnect between what people believe and what they share — driven primarily by inattention rather than purposeful misinformation spreading
- **Emotional triggers matter:** False stories trigger fear, disgust, and surprise. True stories trigger anticipation, sadness, joy, and trust. Emotional valence is the primary vector of misinformation construction
- **Network structure is destiny:** 0.25% of X users were responsible for 73-78% of all low-credibility content (2024 study) — network topology concentrates and amplifies misinformation through hub nodes
- **Platform design drives behavior:** Incentivizing accuracy over popularity doubled the amount of accurate news shared — suggesting structural interventions can be more effective than individual fact-checking

---

## 3. Product Vision & Goals

### 3.1 Vision Statement

*"Predict how misinformation spreads before it happens — so organizations can prepare, intervene, and protect their communities."*

### 3.2 Product Goals

| # | Goal | Measurable Outcome |
|---|------|-------------------|
| G1 | Enable predictive simulation of narrative spread | User can seed a scenario and see simulated spread within 5 minutes |
| G2 | Model narrative mutation realistically | System tracks how stories evolve through 3+ generations of mutation |
| G3 | Identify network vulnerabilities | System outputs vulnerability scores per community/node cluster |
| G4 | Test intervention strategies | User can inject corrections/flags mid-simulation and compare outcomes |
| G5 | Generate actionable reports | System produces a structured report with recommendations after each run |
| G6 | Run at zero cost for individuals | Phase 1 runs entirely on local LLM (Ollama) with no API spend |

### 3.3 Design Principles

1. **Predictive over reactive** — simulate the future, don't monitor the present
2. **Scientifically grounded** — every behavioral parameter maps to published research
3. **Accessible over academic** — web UI anyone can use, not a Python notebook for researchers
4. **Transparent simulation** — users can inspect any agent, any tick, any decision
5. **Cost-efficient by architecture** — LLM calls are minimized through the archetype pattern (20-50 calls per run, not thousands)

---

## 4. Target Users & Personas

### 4.1 Primary Personas

**Persona 1: The Communications Director**
- **Name:** Sarah, 38, Head of Communications at a Fortune 500 company
- **Pain point:** A controversial product launch is coming. She needs to understand how potential misinformation about the product could spread and prepare counter-messaging
- **NarrativeFlow use:** Seeds a simulation with "Company X's new product causes health issue Y" and tests different response strategies — early correction vs. influencer partnership vs. platform flagging
- **Success metric:** Has a tested playbook ready before launch day

**Persona 2: The Policy Researcher**
- **Name:** Marcus, 31, Researcher at a think tank focused on information integrity
- **Pain point:** Needs to understand how different network structures (echo chambers vs. bridged communities) affect misinformation resilience for a policy paper
- **NarrativeFlow use:** Runs 50+ simulations with varying network topologies and susceptibility distributions to generate statistical insights
- **Success metric:** Publishable data on network vulnerability patterns

**Persona 3: The Election Security Analyst**
- **Name:** Priya, 42, Working with an election commission
- **Pain point:** Needs to war-game potential disinformation campaigns before a national election and prepare rapid-response protocols
- **NarrativeFlow use:** Seeds simulations with known disinformation playbooks (voter fraud claims, candidate deepfakes) and identifies the intervention timing that minimizes spread
- **Success metric:** Identifies that corrections need to deploy within 2 hours of initial spread to be effective in the simulated population

**Persona 4: The Portfolio Developer (Farhaan)**
- **Name:** Farhaan, building an impressive technical portfolio project
- **Pain point:** Needs a project that demonstrates systems design, ML/AI, graph theory, applied math, and full-stack development — all in one
- **NarrativeFlow use:** Builds the system, demos it live, writes about the technical decisions
- **Success metric:** Project that impresses at interviews and has genuine commercial potential

### 4.2 Secondary Personas

- **Journalist** — wants to understand how a story they're about to publish might be distorted
- **Brand Safety Manager** — needs to simulate how a brand crisis narrative could escalate
- **Educator** — uses NarrativeFlow as a teaching tool for media literacy courses
- **NGO / Public Health Communicator** — simulates health misinformation spread to optimize messaging strategy

---

## 5. Core Features

### 5.1 Feature Priority Matrix

| Priority | Feature | Description |
|----------|---------|-------------|
| **P0 — MVP** | Scenario Seeding | Input a headline, article, or event description to initialize simulation |
| **P0 — MVP** | Agent Archetype Generation | LLM generates 10-30 behavioral archetypes from seed event |
| **P0 — MVP** | Social Graph Generation | Generate configurable social network topologies (Barabási-Albert, Watts-Strogatz, Stochastic Block Model) |
| **P0 — MVP** | SMIR Propagation Engine | Tick-based simulation with Susceptible → Misinformed → Informed → Resistant states |
| **P0 — MVP** | Real-Time Visualization | WebGL network graph with live node coloring by belief state |
| **P0 — MVP** | Spread Timeline | Line chart showing S/M/I/R population counts over time |
| **P0 — MVP** | Simulation Controls | Play, pause, step, speed adjustment |
| **P0 — MVP** | Report Generation | LLM-generated summary report after simulation completes |
| **P1 — Enhanced** | Narrative Mutation Tracking | Track how stories distort as they propagate; visualize mutation tree |
| **P1 — Enhanced** | Intervention Testing | Inject corrections, flags, or influencer debunks mid-simulation |
| **P1 — Enhanced** | Agent Inspector | Click any node to see agent profile, belief history, exposure timeline |
| **P1 — Enhanced** | Vulnerability Scoring | Per-community vulnerability scores based on topology + archetype distribution |
| **P1 — Enhanced** | Multi-Platform Simulation | Simulate cross-platform dynamics (Twitter-like + Reddit-like) |
| **P2 — Advanced** | Comparison Mode | Run same scenario with different parameters side-by-side |
| **P2 — Advanced** | Historical Replay | Seed with a real past event, compare simulation output to what actually happened |
| **P2 — Advanced** | API Access | RESTful API for programmatic simulation runs |
| **P2 — Advanced** | Custom Agent Profiles | Upload custom demographic/behavioral data to create agent populations |
| **P2 — Advanced** | Export & Sharing | PDF reports, JSON data export, shareable simulation links |
| **P3 — Future** | Real-Time Data Ingestion | Seed from live news feeds (RSS, newsAPI) |
| **P3 — Future** | Collaborative Simulations | Multiple users observe/control same simulation |
| **P3 — Future** | Enterprise SSO & Audit Logs | For enterprise customers |

### 5.2 Detailed Feature Specifications

#### F1: Scenario Seeding (P0)

**Input options:**
- Free-text headline (e.g., "New study links popular sweetener to cancer risk")
- Paste article URL or body text
- Select from curated scenario templates (election disinfo, health misinfo, financial rumor, brand crisis)

**Processing pipeline:**
1. LLM extracts: primary claim, secondary claims, entities mentioned, emotional tone, topic category
2. System generates: narrative seed object with virality estimate, emotional charge score, novelty score
3. User confirms/adjusts extracted parameters before simulation begins

**Configuration panel:**
- Population size: 100 / 500 / 1,000 / 5,000 / 10,000 (slider)
- Network topology: Barabási-Albert / Watts-Strogatz / Stochastic Block Model (dropdown + brief explanation)
- Platform archetype: Twitter-like (broadcast) / Facebook-like (friend clusters) / Reddit-like (community-based)
- Simulation duration: 50 / 100 / 200 / 500 ticks (slider)
- Archetype count: 10 / 15 / 20 / 30 (slider)

#### F2: Agent Archetype Generation (P0)

**LLM prompt strategy:**
Given the seed event, the LLM generates N archetype profiles, each containing:
- Persona name and description
- Susceptibility score (0-1)
- Sharing tendency (0-1)
- Trust in mainstream media (0-1)
- Trust in social media peers (0-1)
- Emotional reactivity (0-1)
- Correction receptiveness (0-1)
- Typical mutation style (enum: "emotional_amplification", "conspiracy_framing", "decontextualization", "fabrication", "exaggeration", "political_reframing")
- Population percentage (how much of the simulation this archetype represents)

**Behavioral calibration:**
Agent parameters are NOT raw LLM outputs used directly for behavior. Instead, they seed the mathematical SMIR model parameters. This avoids the MOSAIC problem where LLM agents refuse to share misinformation due to safety training. The LLM describes *how a human with these traits would behave* — then math drives the actual simulation.

#### F3: Social Graph Generation (P0)

**Three topology options:**

| Topology | Model | Properties | Best For |
|----------|-------|-----------|----------|
| Scale-Free | Barabási-Albert | Power-law degree distribution, few hubs with many connections | Twitter/X — influencer-driven networks |
| Small-World | Watts-Strogatz | High clustering, short path lengths | Facebook — friend-of-friend communities |
| Modular | Stochastic Block Model | Distinct communities with tunable cross-group connectivity | Polarized populations, echo chamber studies |

**Graph parameters exposed to user:**
- Node count (population size)
- Average connections per node
- Community count (for SBM)
- Cross-community connectivity (for SBM) — "how siloed are the echo chambers?"

**Post-generation analysis (computed once, used throughout simulation):**
- Betweenness centrality per node → identifies bridge nodes / super-spreaders
- Clustering coefficient per node → identifies echo chamber membership
- Community detection → identifies distinct population clusters
- Degree distribution → identifies influencer nodes

#### F4: SMIR Propagation Engine (P0)

See [Section 10](#10-the-smir-propagation-model) for full mathematical specification.

**Core loop:**
```
for each tick:
    1. Activate agents (based on activity_rate probability)
    2. For each active agent:
       a. Retrieve posts from neighbors (weighted by connection strength)
       b. Apply recommendation algorithm filter (simulated feed)
       c. For each visible post:
          - Compute state transition probability using SMIR model
          - Roll stochastic dice against probability
          - If transition: update state, propagate narrative to neighbors
    3. Every N ticks: query LLM archetypes for narrative mutation
    4. Compute per-tick metrics
    5. Broadcast tick state to connected WebSocket clients
    6. Check termination conditions (convergence, max ticks)
```

**Vectorized execution:** Agent state transitions are computed using numpy vectorized operations across the entire population per tick — not individual Python loops. This enables 10,000 agents at ~50-100 ticks/second.

#### F5: Real-Time Network Visualization (P0)

**Technology:** Sigma.js (WebGL renderer) + Graphology (in-memory graph data structure)

**Visual encoding:**
- Node color: Green (Susceptible), Red (Misinformed), Blue (Informed), Gray (Resistant)
- Node size: Proportional to influence score (degree centrality)
- Edge opacity: Proportional to interaction recency (recently-active edges glow)
- Layout: Force-directed (ForceAtlas2) pre-computed at simulation start, positions stable throughout

**Interactions:**
- Zoom/pan the graph
- Click node → opens Agent Inspector panel
- Hover node → tooltip with agent archetype, current state, exposure count
- Highlight community clusters
- Toggle heatmap overlay (spread intensity)

#### F6: Report Generation (P0)

**Generated at simulation end by LLM (1-3 calls):**

Report sections:
1. **Executive Summary** — What happened in plain language
2. **Spread Dynamics** — How fast the narrative spread, peak velocity, cascade depth
3. **Narrative Evolution** — How the story mutated (P1: with mutation tree visual)
4. **Vulnerability Analysis** — Which communities were most susceptible and why
5. **Key Agents** — Which nodes had disproportionate influence on spread
6. **Intervention Windows** — When corrections would have been most effective (P1: with counterfactual data)
7. **Recommendations** — Actionable suggestions based on simulation findings

**Export formats:** Markdown (default), PDF (via html-to-pdf), JSON (raw simulation data)

---

## 6. User Flows

### 6.1 Primary Flow: Run a Simulation

```
Landing Page
    │
    ▼
[Seed Input Form]
    │  User enters headline or pastes article
    │  Selects configuration (population, topology, duration)
    ▼
[Processing Screen]  (3-15 seconds)
    │  "Extracting narrative claims..."
    │  "Generating agent archetypes..."
    │  "Building social network..."
    ▼
[Simulation View]
    │  Live network graph (nodes changing color)
    │  Spread timeline chart (S/M/I/R curves)
    │  Tick counter + play/pause/speed controls
    │  [Optional: Click node → Agent Inspector]
    │  [Optional: P1 — Inject intervention]
    ▼
[Simulation Complete]
    │  "Generating report..."
    ▼
[Report View]
    │  Full report with visualizations
    │  Export buttons (PDF, JSON, share link)
    │  "Run Again with Different Parameters" button
```

### 6.2 Secondary Flow: Compare Scenarios (P2)

```
[Simulation Complete] → [Compare Mode]
    │  "Run same scenario with different parameters"
    │  Adjust: topology / population / archetype mix
    ▼
[Split-Screen View]
    │  Left: Original simulation results
    │  Right: New simulation running live
    ▼
[Comparison Report]
    │  Side-by-side metrics
    │  "Narrative spread 40% faster in echo-chamber topology"
```

### 6.3 Secondary Flow: Intervention Testing (P1)

```
[Simulation Running] → [Pause at tick N]
    │  Click "Inject Intervention"
    ▼
[Intervention Panel]
    │  Type: Correction / Platform Flag / Influencer Debunk / Source Removal
    │  Target: All agents / Specific community / Specific nodes
    │  Strength: Low / Medium / High
    ▼
[Resume Simulation]
    │  Watch how intervention changes spread dynamics
    ▼
[Report includes intervention analysis]
    │  "Correction at tick 30 reduced misinformed population by 23%"
```

---

## 7. System Architecture

### 7.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js 15)                       │
│   React 19 + TypeScript + Tailwind CSS + shadcn/ui               │
│   Sigma.js (WebGL graph) + Recharts (charts) + Zustand (state)  │
└───────────────────────────┬─────────────────────────────────────┘
                            │  WebSocket (live ticks)
                            │  REST (CRUD, config, reports)
┌───────────────────────────▼─────────────────────────────────────┐
│                      API LAYER (FastAPI)                          │
│   Python 3.12+ / Uvicorn / async handlers                        │
│   Pydantic v2 request/response validation                        │
│   WebSocket broadcast manager                                    │
│   Simulation lifecycle orchestrator                              │
└────┬──────────┬──────────┬──────────┬───────────────────────────┘
     │          │          │          │
┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼──────────┐
│Simulation│ │  LLM   │ │ Graph │ │    Storage   │
│ Engine  │ │Service │ │Engine │ │              │
│(Python) │ │(Ollama)│ │(igraph)│ │SQLite+Redis │
│numpy    │ │OpenAI  │ │       │ │              │
│scipy    │ │compat  │ │       │ │              │
└─────────┘ └────────┘ └───────┘ └──────────────┘
```

### 7.2 Technology Stack (Justified)

#### Backend

| Technology | Version | Purpose | Why This Choice |
|-----------|---------|---------|----------------|
| **Python** | 3.12+ | Primary language | Dominant ML/simulation ecosystem, async support, best graph/math libraries |
| **FastAPI** | ≥0.115 | HTTP + WebSocket API | 3-4x faster than Flask (22k vs 6k RPS), native async, auto OpenAPI docs, Pydantic integration |
| **Uvicorn** | ≥0.34 | ASGI server | Production-grade, HTTP/2 support, works with FastAPI |
| **Pydantic** | ≥2.10 | Data validation | Rust core (5-50x faster than v1), validates agent configs, LLM outputs, API schemas |
| **python-igraph** | ≥0.11 | Graph engine | C core, 8-10x faster than NetworkX for centrality/community detection, scale-free generation |
| **numpy** | ≥2.1 | Vectorized simulation math | Tick computations across 10k agents in one vectorized operation |
| **scipy** | ≥1.14 | Statistical distributions | Beta distributions for trust, power-law for influence, configurable agent traits |
| **openai** (Python SDK) | ≥1.60 | LLM client | Works with both Ollama (local, free) AND cloud APIs (Claude, GPT) via base_url swap |
| **aiosqlite** | ≥0.20 | Async SQLite | Persistent storage for sim history, results, archetypes. Zero-config, WAL mode for concurrent reads |
| **redis-py** | ≥5.2 | Real-time state + pub/sub | Sub-ms tick reads, pub/sub for WebSocket broadcast. Phase 2+ (SQLite alone for Phase 1) |
| **structlog** | ≥24.4 | Structured logging | JSON logs, simulation traceability |
| **typer** | ≥0.15 | CLI interface | Run simulations from terminal without frontend |
| **uv** | latest | Package manager | 10-100x faster than pip, lockfile support |
| **ruff** | ≥0.8 | Linter + formatter | Replaces black + isort + flake8 in one tool |
| **mypy** | ≥1.13 | Type checking | Catches bugs before runtime in simulation logic |
| **pytest** | ≥8.3 | Testing | With pytest-asyncio for async engine tests |

#### Frontend

| Technology | Version | Purpose | Why This Choice |
|-----------|---------|---------|----------------|
| **Next.js** | 15 | React framework | SSR for landing page SEO, file-based routing, API routes if needed |
| **React** | 19 | UI library | Industry standard, massive ecosystem |
| **TypeScript** | ≥5.7 | Type safety | Catches frontend bugs, better DX |
| **Tailwind CSS** | ≥4.0 | Styling | Utility-first, fast iteration, consistent design |
| **shadcn/ui** | latest | UI components | Tailwind-based, copy-paste, professional appearance with zero design effort |
| **Sigma.js** | ≥3.0 | Network graph visualization | WebGL-rendered, handles 50k+ nodes smoothly, 10x faster than D3 for graphs |
| **Graphology** | ≥0.25 | Graph data structure | In-memory graph that feeds Sigma.js renderer |
| **Recharts** | ≥2.15 | Charts (S/M/I/R curves, metrics) | React-native, composable, good for dashboards |
| **Zustand** | ≥5.0 | State management | Lightweight, no boilerplate, perfect for simulation state |
| **react-use-websocket** | ≥4.11 | WebSocket hook | Clean API for consuming live simulation updates |

#### Infrastructure

| Technology | Purpose | Why |
|-----------|---------|-----|
| **Ollama** | Local LLM inference server | Free, OpenAI-compatible API, runs Llama 3.1 8B on consumer hardware |
| **Llama 3.1 8B** | Default local model | Best quality-to-size ratio for archetype generation |
| **Docker + Docker Compose** | Containerization | Dev/prod parity, one-command setup |
| **GitHub Actions** | CI/CD | Lint, type-check, test on every PR |
| **Pre-commit** | Git hooks | Enforce code quality before commits |

### 7.3 Project File Structure

```
narrativeflow/
├── README.md
├── NarrativeFlow-PRD.md                # This document
├── docker-compose.yml                   # Full stack orchestration
├── .github/
│   └── workflows/
│       └── ci.yml                       # Lint + type-check + test
│
├── backend/
│   ├── pyproject.toml                   # Python dependencies (uv)
│   ├── Dockerfile
│   ├── narrativeflow/
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic Settings (env vars)
│   │   ├── cli.py                       # Typer CLI entry point
│   │   │
│   │   ├── engine/                      # Core simulation engine
│   │   │   ├── __init__.py
│   │   │   ├── simulation.py            # Main tick loop orchestrator
│   │   │   ├── propagation.py           # SMIR model (numpy vectorized)
│   │   │   ├── graph.py                 # igraph network generation + analysis
│   │   │   ├── agents.py                # Agent dataclass + state management
│   │   │   ├── archetypes.py            # LLM archetype generation + caching
│   │   │   ├── narratives.py            # Narrative objects, mutation tracking, lineage
│   │   │   ├── interventions.py         # Correction/flag injection logic
│   │   │   └── metrics.py               # Per-tick analytics computation
│   │   │
│   │   ├── llm/                         # LLM integration layer
│   │   │   ├── __init__.py
│   │   │   ├── client.py                # Unified async client (Ollama / cloud)
│   │   │   ├── prompts.py               # All prompt templates
│   │   │   └── parser.py                # Pydantic models for structured LLM output
│   │   │
│   │   ├── api/                         # FastAPI application
│   │   │   ├── __init__.py
│   │   │   ├── main.py                  # App factory, middleware, lifespan
│   │   │   ├── deps.py                  # Dependency injection (DB, Redis, LLM)
│   │   │   ├── models.py                # Pydantic request/response schemas
│   │   │   └── routes/
│   │   │       ├── simulations.py       # POST /simulations, GET /simulations/:id
│   │   │       ├── reports.py           # GET /reports/:id
│   │   │       └── ws.py               # WS /ws/simulations/:id
│   │   │
│   │   └── storage/                     # Data persistence
│   │       ├── __init__.py
│   │       ├── database.py              # SQLite schema, migrations, queries
│   │       └── cache.py                 # Redis state management (Phase 2+)
│   │
│   └── tests/
│       ├── conftest.py                  # Shared fixtures
│       ├── test_propagation.py          # SMIR model unit tests
│       ├── test_agents.py               # Agent behavior tests
│       ├── test_graph.py                # Graph generation tests
│       ├── test_archetypes.py           # Archetype generation tests
│       ├── test_simulation.py           # Integration tests (full tick loop)
│       └── test_api.py                  # API endpoint tests
│
├── frontend/
│   ├── package.json
│   ├── Dockerfile
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   │
│   ├── app/
│   │   ├── layout.tsx                   # Root layout (dark theme, fonts)
│   │   ├── page.tsx                     # Landing page + seed input
│   │   ├── simulation/
│   │   │   └── [id]/
│   │   │       └── page.tsx             # Live simulation view
│   │   └── reports/
│   │       └── [id]/
│   │           └── page.tsx             # Post-simulation report
│   │
│   ├── components/
│   │   ├── seed-input/
│   │   │   ├── SeedForm.tsx             # Headline/article input form
│   │   │   ├── ConfigPanel.tsx          # Population, topology, duration config
│   │   │   └── TemplateSelector.tsx     # Pre-built scenario templates
│   │   ├── simulation/
│   │   │   ├── NetworkGraph.tsx         # Sigma.js WebGL graph
│   │   │   ├── SpreadTimeline.tsx       # Recharts S/M/I/R line chart
│   │   │   ├── NarrativeMutationTree.tsx # Tree viz of story evolution (P1)
│   │   │   ├── TickControls.tsx         # Play/pause/speed/step
│   │   │   ├── AgentInspector.tsx       # Selected node detail panel
│   │   │   ├── MetricsBar.tsx           # Live metrics (spread rate, peak velocity)
│   │   │   └── InterventionPanel.tsx    # Inject corrections (P1)
│   │   ├── report/
│   │   │   ├── ReportView.tsx           # Full rendered report
│   │   │   ├── VulnerabilityScorecard.tsx
│   │   │   ├── InterventionAnalysis.tsx
│   │   │   └── ExportButton.tsx
│   │   └── ui/                          # shadcn/ui components
│   │
│   ├── lib/
│   │   ├── api.ts                       # REST client
│   │   ├── ws.ts                        # WebSocket connection manager
│   │   └── types.ts                     # Shared TypeScript types
│   │
│   └── stores/
│       └── simulationStore.ts           # Zustand store
│
└── docs/
    ├── SMIR-model.md                    # Mathematical specification
    ├── archetype-prompts.md             # LLM prompt templates
    └── validation-methodology.md        # How we validate accuracy
```

---

## 8. Data Models

### 8.1 Core Entities

#### Simulation

```
Simulation
├── id: UUID
├── status: enum (configuring, initializing, running, paused, completed, failed)
├── created_at: datetime
├── completed_at: datetime | null
├── config: SimulationConfig
│   ├── seed_text: string
│   ├── population_size: int (100-10000)
│   ├── topology: enum (barabasi_albert, watts_strogatz, stochastic_block_model)
│   ├── topology_params: dict (model-specific parameters)
│   ├── platform_archetype: enum (twitter, facebook, reddit)
│   ├── archetype_count: int (10-30)
│   ├── max_ticks: int (50-500)
│   └── tick_speed: float (ticks per second for visualization)
├── seed_narrative: NarrativeSeed
├── archetypes: list[Archetype]
├── current_tick: int
├── metrics_history: list[TickMetrics]
└── report: Report | null
```

#### Agent

```
Agent
├── id: int
├── archetype_id: int
├── graph_node_id: int
│
├── Parameters (set at init, stable):
│   ├── susceptibility: float [0, 1]
│   ├── trust_threshold: float [0, 1]
│   ├── activity_rate: float [0, 1]
│   ├── influence_score: float [0, 1]        # derived from graph centrality
│   ├── open_mindedness: float [0, 1]
│   ├── emotional_reactivity: float [0, 1]
│   └── community_id: int                     # from community detection
│
├── State (changes per tick):
│   ├── belief_state: enum (S, M, I, R)
│   ├── belief_confidence: float [0, 1]
│   ├── exposure_count: int
│   ├── ticks_in_current_state: int
│   ├── narrative_version_id: str | null      # which mutation they hold
│   └── last_active_tick: int
│
└── History (append-only):
    └── state_transitions: list[{tick, from_state, to_state, trigger_agent_id, narrative_id}]
```

#### Archetype

```
Archetype
├── id: int
├── simulation_id: UUID
├── name: string                              # "Skeptical Tech Worker"
├── description: string
├── susceptibility_baseline: float
├── sharing_tendency: float
├── trust_mainstream_media: float
├── trust_social_peers: float
├── emotional_reactivity: float
├── correction_receptiveness: float
├── mutation_style: enum
├── population_percentage: float
└── generated_by: string                      # LLM model used
```

#### Narrative

```
Narrative
├── id: string (UUID)
├── simulation_id: UUID
├── parent_id: string | null                  # null for seed narrative
├── content: string                           # The claim text
├── mutation_type: enum (seed, exaggeration, conspiracy_framing,
│                        decontextualization, fabrication,
│                        emotional_amplification, political_reframing)
├── emotional_charge: float [0, 1]
├── virality_modifier: float                  # multiplier vs parent
├── complexity: float [0, 1]
├── origin_tick: int
├── origin_archetype_id: int
├── spread_count: int                         # agents currently holding this version
└── lineage: list[string]                     # chain of IDs back to seed
```

#### TickMetrics

```
TickMetrics
├── tick: int
├── state_counts: {S: int, M: int, I: int, R: int}
├── spread_rate: float                        # new M+I this tick / total S last tick
├── peak_velocity: float                      # max spread_rate seen so far
├── active_narratives: int                    # distinct narrative versions in circulation
├── dominant_narrative_id: string
├── cascade_depth: int                        # longest chain of spread
├── community_breakdown: list[{community_id, S, M, I, R}]
├── top_spreaders: list[{agent_id, shares_this_tick}]
└── intervention_active: bool
```

### 8.2 SQLite Schema

```sql
CREATE TABLE simulations (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'configuring',
    config JSON NOT NULL,
    seed_narrative JSON,
    current_tick INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE archetypes (
    id INTEGER PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    name TEXT NOT NULL,
    profile JSON NOT NULL,          -- full archetype parameters
    population_pct REAL NOT NULL
);

CREATE TABLE narratives (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    parent_id TEXT REFERENCES narratives(id),
    content TEXT NOT NULL,
    mutation_type TEXT NOT NULL,
    emotional_charge REAL,
    virality_modifier REAL,
    origin_tick INTEGER,
    origin_archetype_id INTEGER,
    spread_count INTEGER DEFAULT 0,
    lineage JSON                    -- array of ancestor IDs
);

CREATE TABLE tick_metrics (
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    tick INTEGER NOT NULL,
    metrics JSON NOT NULL,           -- full TickMetrics object
    PRIMARY KEY (simulation_id, tick)
);

CREATE TABLE reports (
    simulation_id TEXT PRIMARY KEY REFERENCES simulations(id),
    content TEXT NOT NULL,           -- markdown report
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON                    -- structured report data for export
);

-- Agent state is held in memory during simulation (numpy arrays)
-- and only persisted to SQLite as a snapshot on completion
CREATE TABLE agent_snapshots (
    simulation_id TEXT NOT NULL REFERENCES simulations(id),
    agent_data BLOB NOT NULL,        -- compressed numpy array of final agent states
    PRIMARY KEY (simulation_id)
);
```

---

## 9. API Specification

### 9.1 REST Endpoints

#### Simulations

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|-------------|----------|
| `POST` | `/api/simulations` | Create + start simulation | `SimulationConfig` | `{id, status}` |
| `GET` | `/api/simulations` | List all simulations | — | `list[SimulationSummary]` |
| `GET` | `/api/simulations/:id` | Get simulation detail | — | `SimulationDetail` |
| `POST` | `/api/simulations/:id/pause` | Pause running simulation | — | `{status}` |
| `POST` | `/api/simulations/:id/resume` | Resume paused simulation | — | `{status}` |
| `POST` | `/api/simulations/:id/step` | Advance one tick | — | `TickMetrics` |
| `DELETE` | `/api/simulations/:id` | Delete simulation + data | — | `204` |

#### Interventions (P1)

| Method | Path | Description | Request Body |
|--------|------|-------------|-------------|
| `POST` | `/api/simulations/:id/interventions` | Inject intervention | `{type, target, strength}` |

#### Reports

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `GET` | `/api/reports/:sim_id` | Get generated report | `Report` |
| `GET` | `/api/reports/:sim_id/export?format=pdf` | Export report | binary PDF |
| `GET` | `/api/reports/:sim_id/data` | Export raw simulation data | JSON |

#### Agents (Inspector)

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `GET` | `/api/simulations/:id/agents/:agent_id` | Get agent detail | `AgentDetail` |
| `GET` | `/api/simulations/:id/graph` | Get graph structure | `{nodes, edges}` |

### 9.2 WebSocket

| Path | Direction | Payload |
|------|-----------|---------|
| `WS /ws/simulations/:id` | Server → Client | Per-tick: `TickUpdate {tick, state_counts, hot_nodes[], spread_rate, new_mutations[], dominant_narrative}` |
| | Client → Server | `{action: "set_speed", value: 2.0}` |
| | Client → Server | `{action: "pause"}` / `{action: "resume"}` |

---

## 10. The SMIR Propagation Model

### 10.1 Overview

NarrativeFlow uses a novel **SMIR (Susceptible → Misinformed → Informed → Resistant)** model, extending classical epidemiological SIR for information dynamics. Unlike standard SIR, SMIR has two competing "infection" pathways (misinformation and truth) and a hardening mechanic.

### 10.2 State Definitions

| State | Symbol | Description |
|-------|--------|-------------|
| **Susceptible** | S | Agent has not been exposed to the narrative. Default starting state. |
| **Misinformed** | M | Agent has been exposed to and currently believes a false version of the narrative. |
| **Informed** | I | Agent has been exposed to and currently believes the true/corrected version. |
| **Resistant** | R | Agent has been exposed long enough that their belief has hardened. They will not change state again. Terminal state. |

### 10.3 Transition Equations

All transitions are computed per-tick as probabilities, then resolved stochastically.

**S → M (Susceptible becomes Misinformed):**
```
P(S→M) = 1 - ∏(1 - β_M × s_i × v_n × e_n × w_ij)
          for each misinformed neighbor j

Where:
  β_M  = base misinformation transmission rate (global parameter)
  s_i  = agent i's susceptibility (from archetype, 0-1)
  v_n  = narrative n's virality modifier (0-2)
  e_n  = narrative n's emotional charge (0-1)
  w_ij = edge weight between agents i and j (connection strength)
```

**S → I (Susceptible becomes Informed):**
```
P(S→I) = 1 - ∏(1 - β_I × t_i × c_n × cr_j × w_ij)
          for each informed neighbor j

Where:
  β_I  = base truth transmission rate (global, typically < β_M per MIT finding)
  t_i  = agent i's trust in source (mainstream media trust or peer trust, depending on j)
  c_n  = correction strength (how compelling the true version is)
  cr_j = credibility of neighbor j (derived from influence_score)
  w_ij = edge weight
```

**M → I (Misinformed becomes Informed — correction succeeds):**
```
P(M→I) = 1 - ∏(1 - γ × o_i × cr_j × (1 - conf_i) × w_ij)
          for each informed neighbor j

Where:
  γ    = correction effectiveness rate (global)
  o_i  = agent i's open-mindedness
  cr_j = corrector's credibility
  conf_i = agent i's belief confidence (grows over time in M state)
  w_ij = edge weight

Note: As conf_i approaches 1 (belief hardens), correction becomes nearly impossible.
```

**M → R and I → R (Belief hardening):**
```
P(X→R) = σ(ticks_in_state - hardening_threshold)

Where:
  σ    = sigmoid function (smooth transition)
  hardening_threshold = ticks after which belief starts to solidify (archetype-dependent)
```

### 10.4 Key Model Properties

1. **Asymmetric transmission:** β_M > β_I by default (calibrated to MIT's "70% more likely to share" finding). Misinformation spreads faster than truth.

2. **Novelty decay:** Narrative virality decreases over time as it becomes "old news": `v_n(t) = v_n(0) × decay^t`

3. **Confidence accumulation:** The longer an agent holds a belief, the harder it is to change: `conf_i(t) = 1 - e^(-λ × ticks_in_state)`

4. **Emotional contagion:** High emotional charge narratives increase susceptibility in nearby agents temporarily: emotional exposure raises `s_i` for the next K ticks.

5. **Network amplification:** Agents with high betweenness centrality have amplified spread (they bridge communities). Hub nodes (high degree) create cascade events.

### 10.5 Narrative Mutation Rules

Every `mutation_interval` ticks (default: 20), for each active archetype that holds misinformation:

1. Query LLM: "Given archetype [X] received narrative [N], how would they retell it?"
2. LLM returns: mutated content + mutation type
3. New Narrative object created with parent reference
4. Agents of that archetype who share in subsequent ticks spread the mutated version
5. Mutation tree grows organically

**Mutation types and their effects:**
| Type | Effect on virality | Effect on emotional charge |
|------|-------------------|--------------------------|
| Exaggeration | +20% | +10% |
| Conspiracy framing | +40% | +30% |
| Decontextualization | +10% | -5% |
| Fabrication | +50% | +40% |
| Emotional amplification | +15% | +50% |
| Political reframing | +30% | +20% |

### 10.6 Vectorized Implementation

Agent states are stored as numpy arrays for vectorized computation:

```python
# Agent state arrays (N = population size)
states       = np.zeros(N, dtype=np.int8)    # 0=S, 1=M, 2=I, 3=R
suscept      = np.random.beta(a, b, N)        # from archetype distributions
confidence   = np.zeros(N, dtype=np.float32)
ticks_in_st  = np.zeros(N, dtype=np.int32)

# Adjacency as sparse matrix for efficient neighbor lookups
adj_matrix   = sparse.csr_matrix(igraph_to_scipy(graph))

# Per-tick transition: vectorized across all agents simultaneously
# No Python for-loops over individual agents
```

---

## 11. LLM Integration Strategy

### 11.1 Design Philosophy

**The LLM is a creative consultant, not the simulation engine.** It generates behavioral profiles and narrative mutations. The actual simulation runs on math (numpy/scipy). This is critical for:
- **Cost:** 20-50 LLM calls per run vs. thousands
- **Speed:** Math runs at 50-100 ticks/second; LLM calls would bottleneck
- **Reproducibility:** Math is deterministic given seed; LLM output varies
- **Avoiding the MOSAIC problem:** LLM agents refuse to share misinformation due to safety training. Our approach asks the LLM to *describe* human behavior, not *perform* it.

### 11.2 LLM Call Inventory

| Call | Phase | Count | Input | Output | Model |
|------|-------|-------|-------|--------|-------|
| Narrative extraction | Init | 1-3 | Seed text | Claims, entities, tone, category | Llama 3.1 8B |
| Archetype generation | Init | 10-30 | Seed + topic + requested archetype count | ArchetypeProfile (Pydantic) | Llama 3.1 8B |
| Narrative mutation | Every N ticks | 5-15 total | Archetype profile + current narrative | Mutated narrative + mutation type | Llama 3.1 8B |
| Report synthesis | End | 1-3 | Full simulation metrics + key events | Markdown report | Llama 3.1 8B (or Claude for higher quality) |
| **Total per run** | | **~20-50** | | | |

### 11.3 Prompt Architecture

All prompts use structured output (JSON mode) with Pydantic validation:

```
System: You are a behavioral scientist specializing in information ecosystems.
        You analyze how different population segments react to and share narratives.
        Respond ONLY in the specified JSON format.

User:   Given the following news event:
        "{seed_text}"

        Generate {count} distinct behavioral archetypes representing how different
        segments of the population would react to and share this information.

        For each archetype, provide:
        {ArchetypeProfile.model_json_schema()}

        Ensure archetypes cover the full spectrum: true believers, skeptics,
        active debunkers, passive consumers, and amplifiers.
        Population percentages must sum to 100.
```

### 11.4 LLM Client Architecture

```python
# Single client interface that works with any OpenAI-compatible backend
class LLMClient:
    """Unified async LLM client. Swap backends via base_url."""

    def __init__(self, config: LLMConfig):
        self.client = AsyncOpenAI(
            base_url=config.base_url,      # "http://localhost:11434/v1" for Ollama
            api_key=config.api_key,         # "ollama" for local, real key for cloud
        )
        self.model = config.model           # "llama3.1:8b" for Ollama

    async def generate_archetypes(self, seed: NarrativeSeed, count: int) -> list[ArchetypeProfile]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[...],
            response_format={"type": "json_object"},
        )
        return [ArchetypeProfile.model_validate_json(r) for r in parse_response(response)]
```

### 11.5 Cost Projections

| Configuration | LLM Calls/Run | Cost/Run | Monthly (10 runs/day) |
|--------------|---------------|----------|----------------------|
| **Ollama local (Llama 3.1 8B)** | ~40 | $0.00 | $0.00 |
| **Ollama + Claude Haiku reports** | ~37 local + 3 cloud | ~$0.05 | ~$15 |
| **Full Claude Sonnet** | ~40 cloud | ~$1.50 | ~$450 |
| **Full GPT-4o-mini** | ~40 cloud | ~$0.40 | ~$120 |

---

## 12. Frontend Specification

### 12.1 Pages

#### Landing Page (`/`)
- Hero section explaining NarrativeFlow in one sentence
- Seed input form (prominent, center-stage)
- Configuration panel (collapsible, sensible defaults)
- 3 scenario template cards (quick-start)
- Recent simulations list (if returning user)

#### Simulation View (`/simulation/:id`)
- **Left panel (60%):** Sigma.js network graph, full-screen capable
- **Right panel (40%):**
  - Spread Timeline chart (S/M/I/R curves)
  - Live metrics bar (spread rate, active narratives, cascade depth)
  - Tick controls (play/pause/step/speed slider)
  - Agent Inspector (appears when node clicked)
  - Intervention Panel (P1, collapsible)
- **Bottom bar:** Narrative mutation tree (P1, horizontal scrollable)

#### Report View (`/reports/:id`)
- Rendered markdown report
- Embedded charts (regenerated from stored data)
- Vulnerability scorecard (visual)
- Export buttons (PDF, JSON, copy link)
- "Run Again" button with pre-filled config

### 12.2 Design System

- **Theme:** Dark mode default (data-heavy interfaces read better dark)
- **Color palette:**
  - Susceptible: `#4ADE80` (green)
  - Misinformed: `#EF4444` (red)
  - Informed: `#3B82F6` (blue)
  - Resistant: `#6B7280` (gray)
  - Background: `#0F172A` (slate-900)
  - Surface: `#1E293B` (slate-800)
  - Text: `#F1F5F9` (slate-100)
- **Typography:** Inter (UI), JetBrains Mono (metrics/data)
- **Components:** shadcn/ui with Tailwind, consistent border radius and spacing

### 12.3 Real-Time Data Flow

```
[FastAPI Server]
    │
    │  Simulation engine produces TickUpdate every tick
    │
    ▼
[WebSocket Manager]
    │
    │  Broadcasts to all connected clients for this simulation
    │
    ▼
[React WebSocket Hook]
    │
    │  Updates Zustand store
    │
    ▼
[Zustand Store]
    │
    ├──▶ Sigma.js: Re-colors changed nodes (only hot_nodes, not full redraw)
    ├──▶ Recharts: Appends new data point to S/M/I/R time series
    ├──▶ MetricsBar: Updates spread rate, narrative count
    └──▶ AgentInspector: Updates if selected agent changed state
```

**Performance target:** Smooth 60fps visualization at 10 ticks/second with 5,000 nodes.

---

## 13. Non-Functional Requirements

### 13.1 Performance

| Metric | Target | How |
|--------|--------|-----|
| Simulation init time | <15s for 5,000 agents | Archetype generation parallelized, graph generation is <1s |
| Tick computation time | <20ms for 10,000 agents | Numpy vectorized operations, sparse adjacency matrix |
| Ticks per second (headless) | 50-100 | No visualization overhead |
| Ticks per second (with viz) | 1-10 (user-configurable) | Throttled by tick_speed setting |
| Frontend frame rate | 60fps | WebGL (Sigma.js), incremental node updates |
| WebSocket latency | <50ms | FastAPI async, local network |
| LLM call latency (local) | <5s per call | Ollama with Llama 3.1 8B on M-series Mac or decent GPU |
| Total simulation time (1000 agents, 100 ticks) | <2 minutes | Including archetype gen + simulation + report |

### 13.2 Scalability

| Tier | Agents | Infrastructure | Notes |
|------|--------|---------------|-------|
| Phase 1 | 100-1,000 | Single machine (laptop) | SQLite, Ollama, in-process simulation |
| Phase 2 | 1,000-10,000 | Single server + Redis | Redis for state, potentially separate Ollama server |
| Phase 3 | 10,000-100,000 | Multi-process (Ray) | Distribute tick computation across cores |
| Phase 4 | 100,000-1,000,000 | Cluster (Ray on cloud) | Horizontal scaling, dedicated LLM inference |

### 13.3 Reliability

- Simulation state checkpointed to SQLite every 10 ticks (configurable)
- On crash, simulation can resume from last checkpoint
- LLM call failures: retry 3x with exponential backoff, then fall back to rule-based archetype/mutation
- WebSocket disconnection: client auto-reconnects and receives state catch-up

### 13.4 Security

- No user authentication in Phase 1 (single-user local)
- Phase 2+: API key authentication for API access
- Input sanitization on seed text (prevent prompt injection in LLM calls)
- No external data sent unless user opts into cloud LLM
- SQLite database not exposed externally

### 13.5 Testing

| Type | Tool | Coverage Target |
|------|------|----------------|
| Unit tests | pytest | Propagation model, agent behavior, graph generation — 90%+ |
| Integration tests | pytest | Full tick loop, API endpoints — key paths covered |
| Type checking | mypy (strict mode) | 100% of source code |
| Linting | ruff | Zero warnings on CI |
| Frontend | Vitest + React Testing Library | Component rendering, store updates |

---

## 14. Competitive Landscape

### 14.1 Competitive Matrix

| | **NarrativeFlow** | **Blackbird.AI** | **Cyabra** | **MiroFish** | **OASIS** | **MOSAIC** | **Conducttr** |
|---|---|---|---|---|---|---|---|
| **Type** | Predictive simulator | Reactive monitor | Reactive monitor | General prediction engine | Research framework | Research framework | Training platform |
| **Approach** | Simulate future scenarios | Watch live social media | Watch live social media | Simulate any scenario | Simulate social dynamics | Study moderation | Crisis exercises |
| **Misinfo-specific** | Yes (purpose-built) | Yes (detection) | Yes (detection) | No (generic) | No (generic) | Partially | Partially |
| **Narrative mutation tracking** | Yes | No | No | No | No | No | No |
| **Intervention testing** | Yes | No | No | No | No | Yes (moderation only) | Yes (human exercises) |
| **Predictive** | Yes | No (monitoring only) | No | Yes (generic) | No | No | No |
| **Scale** | 100-100k+ agents | N/A (real data) | N/A | Up to 1M | Up to 1M | Small (<1000) | Small (training) |
| **Cost** | Free (local) to $/run | Enterprise $$$ | Enterprise $$$ | Free (open source) | Free (open source) | Free (research) | Enterprise $$$ |
| **Audience** | Researchers, brands, govs, devs | Enterprise security teams | Enterprise | Developers/researchers | Researchers | Researchers | Defense/corporate |
| **Behavioral realism** | Hybrid archetype + math (avoids MOSAIC problem) | Real data | Real data | Pure LLM | LLM + rules | Pure LLM (flawed) | Human players |

### 14.2 Competitive Advantages

1. **Only predictive misinfo-specific simulator** — Blackbird.AI announced simulation as future roadmap; NarrativeFlow ships it first
2. **Narrative mutation tracking** — unique feature, no competitor has it
3. **Solves the MOSAIC problem** — hybrid archetype approach avoids LLM safety training artifacts
4. **Free-to-run** — runs on local LLM, unlike enterprise-priced competitors
5. **Accessible** — web UI vs. Python notebooks (OASIS, MOSAIC)

### 14.3 Risks from Competitors

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Blackbird.AI ships simulation features | Medium | Medium | They're enterprise-only ($$$). NarrativeFlow targets broader audience at $0 |
| MiroFish adds misinfo specialization | Low-Medium | Medium | MiroFish is Chinese-language-first and general-purpose. Misinfo requires domain expertise |
| OASIS adds misinfo module | Low | Low | Academic project, not productized. No web UI |
| New startup enters space | Medium | Medium | First-mover advantage + open-source community |

---

## 15. Monetization Strategy

### 15.1 Business Model: Open-Core

Core simulation engine is free and open-source. Premium features and services are paid.

### 15.2 Revenue Streams

| Stream | Target Customer | Pricing Model | Phase |
|--------|----------------|--------------|-------|
| **Free tier** | Individuals, researchers, students | Free forever (local LLM, basic features) | Phase 1 |
| **Pro tier** | Professionals, small orgs | $29-99/month — cloud LLM, more agents, API access, saved history | Phase 3 |
| **Enterprise tier** | Brands, governments, platforms | Custom pricing — SSO, custom agent profiles, priority support, SLA | Phase 4 |
| **API access** | Developers, platforms | Pay-per-simulation ($1-5/run) or monthly subscription | Phase 3 |
| **Reports & consulting** | Political orgs, NGOs | Custom simulation reports ($500-5,000 per engagement) | Phase 4 |
| **Data licensing** | Academic institutions | Synthetic social network datasets, annual license | Phase 4 |

### 15.3 Pricing Justification

- Blackbird.AI charges enterprise rates (est. $50k-200k+/year)
- Conducttr licenses start at thousands per year
- NarrativeFlow at $29-99/month fills the gap between free academic tools and unaffordable enterprise platforms

---

## 16. Phased Roadmap

### Phase 1: Foundation MVP (Weeks 1-4)

**Goal:** Working end-to-end simulation with visualization. Locally runnable, impressive demo.

| Week | Deliverable |
|------|------------|
| **Week 1** | Project scaffolding: FastAPI backend + Next.js frontend + Docker Compose. SMIR propagation model (numpy). Graph generation (igraph). Agent data structures. Unit tests for propagation math. |
| **Week 2** | LLM integration: Ollama client, archetype generation prompts, Pydantic parsers. CLI runner: run simulation from terminal with text output. SQLite storage for simulation history. |
| **Week 3** | API layer: simulation CRUD endpoints, WebSocket broadcast. Frontend: seed input form, config panel, basic network graph (Sigma.js), spread timeline (Recharts), tick controls. |
| **Week 4** | Report generation (LLM synthesis). Polish: loading states, error handling, dark theme. Docker Compose one-command setup. README with demo GIF. |

**Phase 1 deliverables:**
- [x] Run a simulation from headline input
- [x] Watch network graph update in real-time
- [x] See S/M/I/R spread curves
- [x] Get a generated report
- [x] Entire stack runs locally for $0
- [x] `docker compose up` and it works

### Phase 2: Differentiation (Weeks 5-8)

**Goal:** Features that no competitor has. This is what makes NarrativeFlow unique.

| Week | Deliverable |
|------|------------|
| **Week 5** | Narrative mutation engine: LLM-driven story evolution, mutation tree data model, lineage tracking. |
| **Week 6** | Narrative Mutation Tree visualization (frontend). Agent Inspector panel (click node → see profile, history, belief changes). |
| **Week 7** | Intervention system: inject corrections mid-simulation, flag content, simulate influencer debunks. Intervention Panel UI. |
| **Week 8** | Vulnerability scoring per community. Enhanced report with mutation analysis + intervention recommendations. Redis integration for improved real-time performance. |

**Phase 2 deliverables:**
- [x] Watch how narratives mutate as they spread
- [x] Inspect any agent's journey
- [x] Test intervention strategies mid-simulation
- [x] Community vulnerability scores
- [x] Comprehensive reports with actionable insights

### Phase 3: Scale & Polish (Weeks 9-12)

**Goal:** Production-grade quality, API access, cloud option.

| Week | Deliverable |
|------|------------|
| **Week 9** | Comparison mode: run same scenario with different configs side-by-side. Pre-built scenario templates (election, health, brand crisis). |
| **Week 10** | API documentation (auto-generated from FastAPI). Cloud LLM option (Claude Haiku/Sonnet). Scale to 10,000+ agents. |
| **Week 11** | PDF export. JSON data export. Shareable simulation links. Landing page polish. |
| **Week 12** | Performance optimization. Comprehensive test suite. CI/CD pipeline. Blog post / case study writeup. |

### Phase 4: Monetization (Weeks 13+)

**Goal:** Turn it into a product with paying users.

- User authentication (Supabase Auth or Clerk)
- Hosted version (Vercel + Railway/Fly.io)
- Pro tier features (cloud LLM, more agents, history)
- API metering and billing
- Enterprise features (SSO, custom profiles)
- Historical replay: seed with past events, compare to reality

---

## 17. Validation & Benchmarking

### 17.1 How We Know the Simulation Is Realistic

Validation is the hardest part of any simulation. NarrativeFlow uses a multi-level approach:

#### Level 1: Parameter Calibration (Before Simulation)

Agent parameters are calibrated against published behavioral research:
- β_M / β_I ratio calibrated to MIT's "70% more likely to retweet" finding
- Susceptibility distributions informed by 2025 USC habitual sharing research
- Emotional reactivity weights from MIT Media Lab emotion analysis
- Network topology parameters from empirical social network studies

#### Level 2: Pattern Validation (After Simulation)

Compare simulation outputs to known real-world patterns:
- **Spread curve shape:** Does misinformation follow the characteristic S-curve with faster initial growth than truth? (Per MIT study)
- **Super-spreader concentration:** Does 0.25% of agents drive 73-78% of misinformation spread? (Per 2024 X study)
- **Cascade depth:** Do false narratives reach deeper cascade depths than true ones?
- **Correction effectiveness:** Do corrections show diminishing returns over time? (Per "continued influence effect" research)

#### Level 3: Historical Replay (Phase 4)

Seed with documented real-world events where outcomes are known:
- Springfield, Ohio pet-eating hoax (September 2024) — known spread pattern
- Michigan voter fraud claim (October 2024) — 30M+ views, known timeline
- mRNA vaccine misinfo (January 2025) — 2.5M views, known trajectory

Compare simulation output to actual documented spread. Use KS test to measure distributional similarity between simulated and real spread curves.

#### Level 4: Sensitivity Analysis

Run same scenario 100 times with identical parameters. Measure:
- Mean and variance of final M/I/R distributions
- Consistency of vulnerability rankings across runs
- Stability of intervention effectiveness estimates

Report confidence intervals, not point estimates.

### 17.2 Metrics for Validation

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Spread asymmetry ratio | M spreads faster than I (matching MIT data) | M/I speed ratio: 1.5-2.5x |
| Super-spreader concentration | % of misinfo from top 1% of agents | 60-80% |
| Cascade depth ratio | M cascade depth vs I cascade depth | M 5-20x deeper |
| Correction decay curve | Correction effectiveness vs time | Monotonically decreasing |
| Cross-run consistency | Variance in outcomes across identical runs | CV < 0.3 for key metrics |

---

## 18. Risks & Mitigations

### 18.1 Technical Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|-----------|
| **LLM agent behavior doesn't match real humans** | High | Medium | Hybrid archetype + math model. LLM describes behavior; math executes it. Avoids MOSAIC's failure mode. |
| **Local LLM quality insufficient** | Medium | Medium | Llama 3.1 8B is strong for structured output. Fallback: Mistral 7B, or cloud API for critical calls only. |
| **Sigma.js performance degrades at 10k+ nodes** | Medium | Low | WebGL handles 50k+. Fallback: cluster visualization (render communities as super-nodes). |
| **Simulation takes too long** | Medium | Low | Numpy vectorization handles 10k agents at 50+ ticks/sec. Bottleneck is LLM calls, which are batched and infrequent. |
| **SMIR model oversimplifies real dynamics** | High | Medium | Transparent about limitations. Position as "scenario exploration" not prophecy. Publish sensitivity analyses. |

### 18.2 Product Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|-----------|
| **Dual-use concern (could be used TO spread misinfo)** | High | Medium | Clear terms of use. Don't expose raw mutation prompts. Focus marketing on defense/protection use case. |
| **Hard to validate predictions** | High | High | Never claim predictions. Frame as "scenario exploration" and "stress testing." Show confidence intervals. |
| **Market too niche for resume impact** | Low | Low | Universal topic. Everyone understands misinformation. Technical depth speaks for itself. |
| **Competitor ships similar product** | Medium | Medium | Open-source builds community moat. Misinfo specialization is the differentiator. |

### 18.3 Ethical Considerations

NarrativeFlow must be built responsibly:

1. **No operational misinfo generation:** The system models how misinfo *would* spread. It should never generate actually harmful false content. LLM prompts are designed for behavioral analysis, not content creation.
2. **Dual-use safeguards:** Mutation prompts produce analytical descriptions, not weaponizable playbooks. Rate-limited to prevent bulk content generation.
3. **Transparency:** All simulation parameters, model assumptions, and limitations are documented and inspectable. No black-box predictions.
4. **Responsible disclosure:** If the system reveals a genuinely novel vulnerability in a real platform's design, responsible disclosure to the platform before publication.

---

## 19. Success Metrics

### 19.1 Portfolio/Resume Success

| Metric | Target | Measurement |
|--------|--------|-------------|
| Working demo | End-to-end simulation runs in <5 min | Manual test |
| GitHub stars | 100+ within 3 months of public release | GitHub |
| Interview talking points | Covers 5+ technical domains in one project | Conversation quality |
| Technical blog post | Published, 1000+ reads | Blog analytics |

### 19.2 Product Success (if commercialized)

| Metric | Target (6 months) | Target (12 months) |
|--------|-------------------|-------------------|
| Monthly active users | 500 | 5,000 |
| Simulations run | 5,000 | 50,000 |
| API customers | 10 | 100 |
| MRR (Monthly Recurring Revenue) | $1,000 | $10,000 |
| Academic citations | 2 | 10 |

### 19.3 Simulation Quality

| Metric | Target |
|--------|--------|
| Spread asymmetry matches MIT data | Within 20% of documented ratios |
| Users rate reports as "useful" | 70%+ (survey) |
| Historical replay accuracy | Spread curve correlation > 0.6 with real data |

---

## 20. Appendix

### 20.1 Key Research References

1. Vosoughi, Roy, Aral. "The Spread of True and False News Online." *Science*, 2018. — Foundational study on misinformation spread speed
2. Park et al. "Generative Agents: Interactive Simulacra of Human Behavior." *UIST*, 2023. — Stanford's generative agent architecture
3. Chopra et al. "On the Limits of Agency in Agent-Based Models." *AAMAS*, 2025. — MIT's LLM archetype methodology for million-agent scale
4. OASIS: Open Agent Social Interaction Simulations. CAMEL-AI, 2024. — Framework for 1M agent social simulation
5. MOSAIC: Modeling Social AI for Content Dissemination. *EMNLP*, 2025. — LLM agent misinfo limitations
6. Epidemic modeling for misinformation spread. *Nature Scientific Reports*, 2024. — SIR model for misinfo
7. USC Study on habitual sharing, 2025. — Habits drive misinfo sharing more than beliefs
8. APA Report: How and Why Misinformation Spreads. 2024.

### 20.2 Key URLs

- MiroFish: https://github.com/666ghj/MiroFish
- OASIS: https://github.com/camel-ai/oasis
- AgentTorch: https://agenttorch.github.io/AgentTorch/
- Blackbird.AI: https://blackbird.ai
- Sigma.js: https://www.sigmajs.org/
- Ollama: https://ollama.ai

### 20.3 Glossary

| Term | Definition |
|------|-----------|
| **Agent** | A simulated individual in the social network with behavioral parameters and evolving state |
| **Archetype** | An LLM-generated behavioral profile representing a demographic/personality cluster |
| **Cascade depth** | The longest chain of agent-to-agent narrative spread |
| **SMIR** | Susceptible-Misinformed-Informed-Resistant — the propagation model |
| **Narrative mutation** | How a story changes as it passes through agents with different mutation styles |
| **Tick** | One discrete time step in the simulation |
| **Vulnerability score** | A metric indicating how susceptible a community/cluster is to misinformation |
| **Intervention** | A deliberate action injected into the simulation (correction, flag, debunk) |
| **Hardening** | The process by which an agent's belief becomes resistant to change over time |

---

*End of PRD — NarrativeFlow v1.0*
