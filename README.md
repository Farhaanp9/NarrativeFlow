# NarrativeFlow

Multi-agent simulation engine that models how misinformation spreads through social networks.

Seed a headline, watch it propagate through thousands of AI-driven agents with unique personalities and trust thresholds, and discover where interventions are most effective.

## Architecture

```
Frontend (Next.js 15)          Backend (FastAPI)           LLM (Ollama)
React 19 + Tailwind            Python 3.12 + numpy        Llama 3.1 8B
Sigma.js (WebGL graph)  <-->   SMIR propagation engine    Archetype generation
Recharts (timelines)           python-igraph (graphs)     Report synthesis
Zustand (state)                aiosqlite (storage)
WebSocket (live ticks)         WebSocket (broadcast)
```

## Quick Start

### Docker (recommended)

```bash
docker compose up
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/health
- Ollama: http://localhost:11434

### Manual Setup

**Backend:**

```bash
cd backend
uv sync
uv run uvicorn narrativeflow.api.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Ollama (optional, for LLM-generated archetypes):**

```bash
ollama pull llama3.1:8b
ollama serve
```

Without Ollama, the system uses built-in default archetypes and fallback reports.

### CLI

Run a simulation without the frontend:

```bash
cd backend
uv run python -m narrativeflow.cli simulate "New study links sweetener to cancer" --agents 500 --ticks 100
```

## Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI | REST API + WebSocket |
| numpy / scipy | Vectorized SMIR propagation |
| python-igraph | Graph generation (BA, WS, SBM) |
| Pydantic | Data validation |
| aiosqlite | Async SQLite storage |
| openai SDK | LLM client (Ollama-compatible) |

### Frontend
| Technology | Purpose |
|-----------|---------|
| Next.js 15 | React framework |
| Sigma.js + Graphology | WebGL network graph |
| Recharts | S/M/I/R spread timeline |
| Zustand | State management |
| shadcn/ui | UI components |

## The SMIR Model

NarrativeFlow uses a novel **SMIR** (Susceptible -> Misinformed -> Informed -> Resistant) propagation model:

- **S -> M**: Misinformation spreads faster than truth (calibrated to MIT's "70% more likely to share" finding)
- **S -> I**: Truth transmission via informed neighbors
- **M -> I**: Correction succeeds based on open-mindedness and source credibility
- **M/I -> R**: Belief hardening over time (sigmoid threshold)

All transitions are computed as vectorized numpy operations across the entire population per tick.

## Development

```bash
cd backend
uv run pytest           # Run tests (70+ tests)
uv run ruff check .     # Lint
uv run mypy narrativeflow/  # Type check
```

```bash
cd frontend
npm run build           # Build
npm run dev             # Dev server
```

## Project Structure

```
narrativeflow/
  backend/
    narrativeflow/
      api/           # FastAPI routes, WebSocket, models
      engine/        # SMIR simulation engine, agents, graph, metrics
      llm/           # LLM client, prompts, parsers
      storage/       # SQLite database
    tests/           # pytest test suite
  frontend/
    app/             # Next.js pages (landing, simulation, reports)
    components/      # React components (graph, timeline, controls)
    stores/          # Zustand state management
    lib/             # API client, types, WebSocket
```

See [NarrativeFlow-PRD.md](NarrativeFlow-PRD.md) for full technical specification.
