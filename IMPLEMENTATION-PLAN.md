# NarrativeFlow — Phase 1 Implementation Plan

## Context

NarrativeFlow is a multi-agent simulation engine that models misinformation spread through social networks. The PRD (`NarrativeFlow-PRD.md`) defines a complete architecture: FastAPI backend with numpy-vectorized SMIR propagation, python-igraph graph generation, Ollama-powered LLM integration, and a Next.js 15 frontend with Sigma.js network visualization. This plan covers Phase 1 (MVP) — a working end-to-end simulation with real-time visualization, runnable locally for $0.

Each sub-phase produces a working, testable increment. No sub-phase depends on unverified work from a prior one.

---

## Sub-phase 1A: Project Scaffolding & Core Infrastructure

**Scope:** Python project setup, FastAPI skeleton, SQLite init, Docker Compose, config management.

**Files to create (~12 files):**

| File | Description |
|------|-------------|
| `backend/pyproject.toml` | Python deps (fastapi, uvicorn, pydantic, numpy, scipy, python-igraph, openai, aiosqlite, structlog, typer, ruff, mypy, pytest, pytest-asyncio) managed by uv |
| `backend/Dockerfile` | Python 3.12 slim image, uv install, uvicorn entrypoint |
| `backend/narrativeflow/__init__.py` | Package init with version |
| `backend/narrativeflow/config.py` | Pydantic Settings: DB path, Ollama URL, LLM model, log level, CORS origins |
| `backend/narrativeflow/api/__init__.py` | Empty init |
| `backend/narrativeflow/api/main.py` | FastAPI app factory with lifespan (DB init), CORS middleware, health endpoint (`GET /api/health`) |
| `backend/narrativeflow/storage/__init__.py` | Empty init |
| `backend/narrativeflow/storage/database.py` | SQLite schema creation (all 6 tables from PRD Section 8.2), async connection helper, WAL mode |
| `backend/narrativeflow/engine/__init__.py` | Empty init |
| `backend/narrativeflow/llm/__init__.py` | Empty init |
| `backend/tests/__init__.py` | Empty init |
| `backend/tests/conftest.py` | Shared fixtures: temp SQLite DB, test FastAPI client, settings override |
| `backend/tests/test_health.py` | Health endpoint returns 200 with version |
| `backend/tests/test_database.py` | Schema creates all tables, WAL mode enabled |
| `docker-compose.yml` | Services: backend (FastAPI on 8000), ollama (11434) |
| `backend/ruff.toml` | Ruff config (line length, select rules) |
| `backend/mypy.ini` | Mypy strict mode config |

**Verification:**
- `cd backend && uv sync` installs all deps
- `uv run pytest` — health and DB tests pass
- `uv run ruff check .` — zero warnings
- `uv run mypy narrativeflow/` — passes
- `docker compose up backend` starts, `curl localhost:8000/api/health` returns 200

---

## Sub-phase 1B: SMIR Propagation Engine

**Scope:** Agent data structures (numpy arrays), graph generation (igraph, 3 topologies), SMIR state transition equations (vectorized), tick loop, per-tick metrics.

**Dependencies:** 1A (project structure, config, DB)

**Files to create (~8 files):**

| File | Description |
|------|-------------|
| `backend/narrativeflow/engine/agents.py` | `AgentPopulation` class: numpy arrays for states, susceptibility, confidence, ticks_in_state, exposure_count, activity_rate, influence_score, open_mindedness, emotional_reactivity, community_id, archetype_id. Init from archetype list + graph centrality data. Methods: `get_by_state()`, `update_states()`, `increment_ticks()`. |
| `backend/narrativeflow/engine/graph.py` | `generate_graph(topology, n, params)` → igraph.Graph. Supports Barabasi-Albert, Watts-Strogatz, Stochastic Block Model. Post-generation: compute betweenness centrality, clustering coefficient, community detection (Louvain), degree distribution. Returns `GraphData` with adjacency sparse matrix + node metrics. |
| `backend/narrativeflow/engine/propagation.py` | Vectorized SMIR transitions per PRD Section 10.3. `compute_s_to_m()`, `compute_s_to_i()`, `compute_m_to_i()`, `compute_hardening()`. Each returns probability array across all agents. `resolve_transitions(probs, rng)` — stochastic resolution. Confidence accumulation: `conf(t) = 1 - e^(-λ*ticks)`. Novelty decay: `v(t) = v(0) * decay^t`. |
| `backend/narrativeflow/engine/metrics.py` | `compute_tick_metrics(agents, tick, narratives)` → `TickMetrics` Pydantic model. State counts, spread rate, peak velocity, active narratives, cascade depth, community breakdown, top spreaders. |
| `backend/narrativeflow/engine/narratives.py` | `NarrativeSeed` and `Narrative` Pydantic models. `NarrativeTracker` class to manage active narratives, compute spread counts, track lineage. Mutation type enum with virality/emotion modifiers per PRD Section 10.5 table. |
| `backend/narrativeflow/engine/simulation.py` | `SimulationEngine` class. `initialize(config, archetypes, graph_data)` sets up agent arrays + adjacency matrix. `tick()` runs one step: activate agents, compute transitions, resolve stochastically, update states, compute metrics. `run(max_ticks)` runs headless tick loop. No LLM calls yet (mutation deferred to 1C). |
| `backend/tests/test_propagation.py` | Unit tests: S→M probability correct for known inputs, S→I probability correct, M→I correction with confidence decay, hardening sigmoid shape, novelty decay over ticks. Edge cases: isolated node never transitions, fully connected node transitions fast. |
| `backend/tests/test_graph.py` | Unit tests: BA graph has power-law degree distribution (top 10% nodes have >50% edges), WS graph has high clustering coefficient (>0.3), SBM produces correct community count. Graph metrics computed correctly (centrality, communities). Adjacency sparse matrix shape matches node count. |
| `backend/tests/test_agents.py` | Unit tests: agent population initializes correct array shapes, state updates work, archetype assignment distributes agents by population_pct. |
| `backend/tests/test_simulation.py` | Integration test: 1000-agent BA graph, run 100 ticks headless with mock archetypes. Asserts: states change over time, metrics recorded per tick, runs in <5 seconds, final state has fewer S agents than initial. |

**Verification:**
- `uv run pytest tests/test_propagation.py` — all transition math tests pass
- `uv run pytest tests/test_graph.py` — all 3 topologies generate correctly
- `uv run pytest tests/test_agents.py` — agent arrays init correctly
- `uv run pytest tests/test_simulation.py` — 1000-agent sim completes 100 ticks in <5s
- `uv run mypy narrativeflow/engine/` — passes

---

## Sub-phase 1C: LLM Integration

**Scope:** Unified LLM client (Ollama + cloud fallback), prompt templates, Pydantic output parsers, archetype generation, narrative extraction.

**Dependencies:** 1B (engine data structures for ArchetypeProfile, NarrativeSeed)

**Files to create (~5 files):**

| File | Description |
|------|-------------|
| `backend/narrativeflow/llm/client.py` | `LLMClient` class wrapping `AsyncOpenAI`. Constructor takes `LLMConfig` (base_url, api_key, model). Methods: `generate_archetypes(seed_text, count)`, `extract_narrative(seed_text)`, `generate_report(metrics, config)`, `mutate_narrative(archetype, narrative)`. Retry with exponential backoff (3 attempts). Fallback: if LLM unavailable, return mock/rule-based responses. |
| `backend/narrativeflow/llm/prompts.py` | Prompt templates as string constants: `NARRATIVE_EXTRACTION_PROMPT`, `ARCHETYPE_GENERATION_PROMPT`, `REPORT_SYNTHESIS_PROMPT`, `NARRATIVE_MUTATION_PROMPT`. Uses `{placeholders}` for `.format()`. System prompts per PRD Section 11.3. |
| `backend/narrativeflow/llm/parser.py` | Pydantic models for structured LLM output: `NarrativeSeedOutput` (claims, entities, tone, category, virality_estimate, emotional_charge, novelty_score), `ArchetypeProfile` (all fields from PRD Section 5.2 F2), `MutatedNarrative` (content, mutation_type, emotional_charge_delta, virality_delta), `ReportOutput` (sections as markdown). Parsing functions that validate JSON responses against these models. |
| `backend/tests/test_llm_parser.py` | Unit tests: valid JSON parses to correct Pydantic models, invalid JSON raises validation error, archetype population_pct sums to ~100, all enum values accepted for mutation_style. |
| `backend/tests/test_archetypes.py` | Integration test (requires Ollama OR uses mock): generate archetypes for a sample headline, assert returns valid `ArchetypeProfile` objects with correct field ranges (0-1 for floats, valid enums). Mock fallback test: when LLM unavailable, returns reasonable default archetypes. |

**Verification:**
- `uv run pytest tests/test_llm_parser.py` — parser tests pass (no LLM needed)
- `uv run pytest tests/test_archetypes.py` — passes with mock fallback (CI-safe)
- With Ollama running: `uv run pytest tests/test_archetypes.py -m "not mock_only"` — real LLM returns valid archetypes
- `uv run mypy narrativeflow/llm/` — passes

---

## Sub-phase 1D: Simulation Orchestrator & API

**Scope:** Full simulation lifecycle (create → init → run → complete → report), REST API, WebSocket tick broadcast, CLI runner.

**Dependencies:** 1A (DB, FastAPI), 1B (engine), 1C (LLM client)

**Files to create (~8 files):**

| File | Description |
|------|-------------|
| `backend/narrativeflow/api/models.py` | Pydantic request/response schemas: `SimulationCreateRequest` (seed_text, population_size, topology, topology_params, archetype_count, max_ticks, tick_speed), `SimulationSummary`, `SimulationDetail`, `TickUpdate` (for WebSocket). |
| `backend/narrativeflow/api/deps.py` | Dependency injection: get_db(), get_llm_client(), get_settings(). |
| `backend/narrativeflow/api/routes/simulations.py` | `POST /api/simulations` — create sim, generate archetypes, build graph, run in background task. `GET /api/simulations` — list all. `GET /api/simulations/{id}` — detail with metrics. `POST /api/simulations/{id}/pause` and `/resume`. `DELETE /api/simulations/{id}`. |
| `backend/narrativeflow/api/routes/reports.py` | `GET /api/reports/{sim_id}` — get markdown report. `GET /api/reports/{sim_id}/data` — raw JSON export. |
| `backend/narrativeflow/api/routes/ws.py` | `WS /ws/simulations/{id}` — broadcasts `TickUpdate` per tick. Accepts client commands: set_speed, pause, resume. Uses `WebSocketManager` for connection tracking. |
| `backend/narrativeflow/api/routes/__init__.py` | Empty init |
| `backend/narrativeflow/cli.py` | Typer app. `simulate` command: takes seed_text, --agents, --ticks, --topology. Runs full lifecycle synchronously, prints tick progress and final metrics to stdout. `list` command: shows past simulations. |
| `backend/tests/test_api.py` | Integration tests with TestClient: POST creates simulation (returns id+status), GET list returns it, GET detail has metrics after completion, WebSocket receives tick updates, DELETE removes simulation. Uses mock LLM. |

**Update existing files:**
- `backend/narrativeflow/api/main.py` — register route routers, add WebSocket manager to app state
- `backend/narrativeflow/engine/simulation.py` — add orchestration: init archetypes via LLM, build graph, run tick loop with WebSocket broadcast callback, generate report on completion, persist to DB

**Verification:**
- CLI: `uv run python -m narrativeflow.cli simulate "New study links sweetener to cancer" --agents 500 --ticks 100` — runs to completion, prints metrics
- `uv run pytest tests/test_api.py` — all API tests pass with mock LLM
- Manual: `uv run uvicorn narrativeflow.api.main:app` then POST to `/api/simulations` — simulation runs and GET returns results
- WebSocket test: connect to `ws://localhost:8000/ws/simulations/{id}`, receive tick updates

---

## Sub-phase 1E: Frontend Foundation

**Scope:** Next.js 15 project, landing page with seed form + config, simulation page with Sigma.js graph + Recharts timeline + tick controls, WebSocket integration.

**Dependencies:** 1D (API + WebSocket endpoints)

**Files to create (~20 files):**

| File | Description |
|------|-------------|
| `frontend/package.json` | Next.js 15, React 19, TypeScript, Tailwind 4, sigma.js, graphology, recharts, zustand, react-use-websocket |
| `frontend/tsconfig.json` | TypeScript strict config |
| `frontend/next.config.ts` | Next.js config (API proxy to backend) |
| `frontend/tailwind.config.ts` | Dark theme colors from PRD Section 12.2, Inter + JetBrains Mono fonts |
| `frontend/Dockerfile` | Node 22 image, npm install, next build, next start |
| `frontend/app/layout.tsx` | Root layout: dark theme, Inter font, global styles |
| `frontend/app/page.tsx` | Landing page: hero text, SeedForm, ConfigPanel, recent simulations list |
| `frontend/app/simulation/[id]/page.tsx` | Simulation view: 60/40 split layout, NetworkGraph + sidebar (timeline, metrics, controls, inspector) |
| `frontend/app/reports/[id]/page.tsx` | Report view: rendered markdown, export buttons, "Run Again" button |
| `frontend/components/seed-input/SeedForm.tsx` | Headline/article textarea, submit button, loading state |
| `frontend/components/seed-input/ConfigPanel.tsx` | Population slider, topology dropdown, duration slider, archetype count slider. Collapsible with sensible defaults. |
| `frontend/components/simulation/NetworkGraph.tsx` | Sigma.js + Graphology. Renders nodes colored by SMIR state (green/red/blue/gray). Node size by influence. ForceAtlas2 layout computed once. Updates node colors on tick via WebSocket data. |
| `frontend/components/simulation/SpreadTimeline.tsx` | Recharts LineChart: 4 lines (S/M/I/R) over ticks. Appends new data point each tick. PRD color scheme. |
| `frontend/components/simulation/TickControls.tsx` | Play/pause button, speed slider (0.5x-10x), step button, tick counter display. Sends commands via WebSocket. |
| `frontend/components/simulation/MetricsBar.tsx` | Live readout: spread rate, active narratives, cascade depth, peak velocity. JetBrains Mono font. |
| `frontend/components/report/ReportView.tsx` | Renders markdown report with react-markdown. Sections styled with Tailwind. |
| `frontend/components/report/ExportButton.tsx` | JSON export (downloads raw data from API). |
| `frontend/lib/api.ts` | REST client: createSimulation(), getSimulation(), listSimulations(), getReport(). Fetch wrapper with error handling. |
| `frontend/lib/ws.ts` | WebSocket connection manager: connect to sim, receive TickUpdate, send commands. |
| `frontend/lib/types.ts` | TypeScript types mirroring backend Pydantic models: SimulationConfig, TickUpdate, AgentState, etc. |
| `frontend/stores/simulationStore.ts` | Zustand store: simulation state, tick history, current tick data, node states. Actions: appendTick, setSpeed, togglePause. |

**Verification:**
- `cd frontend && npm install && npm run build` — builds without errors
- `npm run dev` — starts on localhost:3000
- Landing page renders, form submits to backend API
- Simulation page: graph renders with correct node count, nodes change color as ticks progress
- Spread timeline updates in real-time with 4 colored lines
- Tick controls: play/pause works, speed slider adjusts tick rate

---

## Sub-phase 1F: Report Generation & Polish

**Scope:** LLM-generated report, report view page, JSON export, error handling, loading states, full Docker Compose, README.

**Dependencies:** 1E (frontend pages exist), 1D (report API exists)

**Files to create/modify (~8 files):**

| File | Description |
|------|-------------|
| `backend/narrativeflow/engine/report.py` | `generate_report(simulation, metrics_history, config)` — builds LLM prompt with simulation summary data, calls LLM for report synthesis, returns markdown. Sections per PRD: Executive Summary, Spread Dynamics, Vulnerability Analysis, Key Agents, Intervention Windows, Recommendations. |
| `backend/tests/test_report.py` | Test report generation with mock LLM returns valid markdown with expected sections. |
| `docker-compose.yml` | **Update:** Add frontend service (port 3000), ensure backend + frontend + ollama all orchestrated. Health checks. |
| `backend/Dockerfile` | **Update:** Finalize for production (multi-stage build if needed). |
| `frontend/Dockerfile` | **Update:** Finalize for production. |
| `README.md` | Project overview, architecture diagram (ASCII), quick start (`docker compose up`), manual setup instructions, screenshots/GIFs, tech stack, link to PRD. |
| `.github/workflows/ci.yml` | GitHub Actions: lint (ruff), type-check (mypy), test (pytest with mock LLM), frontend build check. |

**Polish updates across existing files:**
- Frontend: loading spinners during simulation init, error toasts on API failure, empty states
- Backend: structured error responses, proper HTTP status codes, request validation errors
- Both: consistent error handling patterns

**Verification:**
- End-to-end: enter headline → watch simulation → see report with all sections
- `docker compose up` brings up entire stack (backend:8000, frontend:3000, ollama:11434)
- `docker compose up` from a clean clone + `README` instructions work
- `uv run pytest` — full test suite passes
- GitHub Actions CI passes on push
- JSON export downloads valid data file

---

## Dependency Graph

```
1A (Scaffolding)
 └── 1B (SMIR Engine)
      └── 1C (LLM Integration)
           └── 1D (Orchestrator & API)
                └── 1E (Frontend)
                     └── 1F (Reports & Polish)
```

Each layer builds on the last. The engine is the foundation — it must be rock-solid before the API wraps it.

## File Count Summary

| Sub-phase | New Files | Modified Files | Total |
|-----------|-----------|---------------|-------|
| 1A | ~17 | 0 | ~17 |
| 1B | ~10 | 0 | ~10 |
| 1C | ~5 | 0 | ~5 |
| 1D | ~8 | 2 | ~10 |
| 1E | ~20 | 0 | ~20 |
| 1F | ~5 | ~6 | ~11 |
| **Total** | **~65** | **~8** | **~73** |

## Testing Strategy Notes

- All backend tests use mock LLM by default (CI-safe, no Ollama required)
- Tests marked `@pytest.mark.ollama` require running Ollama (for local integration testing)
- Frontend tests deferred to Phase 1F polish (Vitest + React Testing Library for key components)
- Type checking (mypy strict) runs on every sub-phase as part of verification
