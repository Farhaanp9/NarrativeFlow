"""Simulation CRUD endpoints."""

import asyncio
import json
import uuid
from datetime import UTC, datetime

import aiosqlite
import structlog
from fastapi import APIRouter, Depends, HTTPException

from narrativeflow.api.deps import get_db, get_llm_client
from narrativeflow.api.models import (
    AgentDetailResponse,
    SimulationCreateRequest,
    SimulationDetail,
    SimulationStatusResponse,
    SimulationSummary,
)
from narrativeflow.api.routes.ws import ws_manager
from narrativeflow.engine.agents import AgentPopulation, ArchetypeConfig
from narrativeflow.engine.simulation import SimulationConfig, SimulationEngine
from narrativeflow.llm.client import LLMClient

logger = structlog.get_logger()

router = APIRouter(prefix="/api/simulations", tags=["simulations"])

# In-memory registry of running engines for agent inspection
_running_engines: dict[str, SimulationEngine] = {}

# Strong references to simulation tasks; asyncio keeps only weak ones
_simulation_tasks: set[asyncio.Task[None]] = set()


@router.post("", response_model=SimulationStatusResponse)
async def create_simulation(
    req: SimulationCreateRequest,
    db: aiosqlite.Connection = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> SimulationStatusResponse:
    """Create and start a new simulation."""
    sim_id = str(uuid.uuid4())
    config_dict = req.model_dump(mode="json")

    await db.execute(
        "INSERT INTO simulations (id, status, config, current_tick) "
        "VALUES (?, ?, ?, 0)",
        (sim_id, "initializing", json.dumps(config_dict)),
    )
    await db.commit()

    task = asyncio.create_task(_run_simulation(sim_id, req, llm))
    _simulation_tasks.add(task)
    task.add_done_callback(_simulation_tasks.discard)

    return SimulationStatusResponse(id=sim_id, status="initializing")


async def _run_simulation(
    sim_id: str,
    req: SimulationCreateRequest,
    llm: LLMClient,
) -> None:
    """Run the full simulation lifecycle in background."""
    from narrativeflow.config import get_settings

    settings = get_settings()
    control = ws_manager.get_control(sim_id)
    control.set_speed(req.tick_speed)

    try:
        # 1. Generate archetypes via LLM
        logger.info("sim_generating_archetypes", sim_id=sim_id)
        archetype_profiles = await llm.generate_archetypes(
            req.seed_text, req.archetype_count
        )

        archetypes = [
            ArchetypeConfig(
                id=i,
                name=p.name,
                susceptibility=p.susceptibility,
                sharing_tendency=p.sharing_tendency,
                trust_mainstream_media=p.trust_mainstream_media,
                trust_social_peers=p.trust_social_peers,
                emotional_reactivity=p.emotional_reactivity,
                correction_receptiveness=p.correction_receptiveness,
                mutation_style=p.mutation_style.value,
                population_percentage=p.population_percentage,
            )
            for i, p in enumerate(archetype_profiles)
        ]

        # Store archetypes in DB
        db = await aiosqlite.connect(settings.db_path)
        try:
            for arch in archetype_profiles:
                await db.execute(
                    "INSERT INTO archetypes "
                    "(simulation_id, name, profile, population_pct) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        sim_id,
                        arch.name,
                        arch.model_dump_json(),
                        arch.population_percentage,
                    ),
                )
            await db.commit()
        finally:
            await db.close()

        # 2. Initialize engine
        logger.info("sim_starting", sim_id=sim_id)
        sim_config = SimulationConfig(
            seed_text=req.seed_text,
            population_size=req.population_size,
            topology=req.topology,
            topology_params=req.topology_params,
            archetype_count=req.archetype_count,
            max_ticks=req.max_ticks,
            tick_speed=req.tick_speed,
        )
        engine = SimulationEngine(sim_config)

        narrative_seed_output = await llm.extract_narrative(req.seed_text)
        from narrativeflow.engine.narratives import NarrativeSeed

        seed_narrative = NarrativeSeed(
            content=narrative_seed_output.primary_claim,
            claims=[
                narrative_seed_output.primary_claim,
                *narrative_seed_output.secondary_claims,
            ],
            entities=narrative_seed_output.entities,
            tone=narrative_seed_output.tone,
            category=narrative_seed_output.category,
            virality_estimate=narrative_seed_output.virality_estimate,
            emotional_charge=narrative_seed_output.emotional_charge,
            novelty_score=narrative_seed_output.novelty_score,
        )

        engine.initialize(archetypes, seed_narrative)

        # Register engine for agent inspection
        _running_engines[sim_id] = engine

        # Store graph data for frontend
        if engine.graph_data is not None:
            graph_json = json.dumps({
                "nodes": [
                    {
                        "id": i,
                        "community": int(
                            engine.graph_data.community_ids[i]
                        ),
                        "influence": float(
                            engine.graph_data.influence_scores[i]
                        ),
                        "degree": int(engine.graph_data.degree[i]),
                    }
                    for i in range(engine.graph_data.n_nodes)
                ],
                "edges": [
                    {"source": int(s), "target": int(t)}
                    for s, t in engine.graph_data.edge_list
                ],
            })
            db_g = await aiosqlite.connect(settings.db_path)
            try:
                await db_g.execute(
                    "UPDATE simulations SET seed_narrative = ? "
                    "WHERE id = ?",
                    (graph_json, sim_id),
                )
                await db_g.commit()
            finally:
                await db_g.close()

        # Mark running only once the engine and graph exist, so clients
        # that see "running" can inspect agents and load the graph.
        db_r = await aiosqlite.connect(settings.db_path)
        try:
            await db_r.execute(
                "UPDATE simulations SET status = ? WHERE id = ?",
                ("running", sim_id),
            )
            await db_r.commit()
        finally:
            await db_r.close()

        # 3. Run tick loop with pause/resume support
        state_map = {0: "S", 1: "M", 2: "I", 3: "R"}

        async def on_tick_async(
            tick: int, metrics_dict: dict[str, object]
        ) -> None:
            await ws_manager.broadcast(sim_id, metrics_dict)
            if tick % 10 == 0:
                db2 = await aiosqlite.connect(settings.db_path)
                try:
                    await db2.execute(
                        "UPDATE simulations SET current_tick = ? "
                        "WHERE id = ?",
                        (tick, sim_id),
                    )
                    await db2.commit()
                finally:
                    await db2.close()

        for _ in range(sim_config.max_ticks):
            # Wait if paused (blocks until resumed/stepped)
            await control.wait_if_paused()

            metrics = engine.tick()

            # Build node states for changed nodes
            node_states: dict[str, str] = {}
            changed = engine.get_changed_indices()
            if engine.agents is not None:
                if metrics.tick == 1:
                    for i in range(engine.agents.n):
                        node_states[str(i)] = state_map.get(
                            int(engine.agents.states[i]), "S"
                        )
                else:
                    for i in changed:
                        node_states[str(i)] = state_map.get(
                            int(engine.agents.states[i]), "S"
                        )

            metrics_dict: dict[str, object] = {
                "tick": metrics.tick,
                "state_counts": metrics.state_counts,
                "spread_rate": metrics.spread_rate,
                "peak_velocity": metrics.peak_velocity,
                "active_narratives": metrics.active_narratives,
                "dominant_narrative_id": metrics.dominant_narrative_id,
                "node_states": node_states,
                "hot_nodes": changed[:20],
            }

            await on_tick_async(metrics.tick, metrics_dict)

            # Store tick metrics
            tick_record: dict[str, object] = {
                "tick": metrics.tick,
                "state_counts": metrics.state_counts,
                "spread_rate": metrics.spread_rate,
                "peak_velocity": metrics.peak_velocity,
                "active_narratives": metrics.active_narratives,
                "dominant_narrative_id": metrics.dominant_narrative_id,
            }
            db3 = await aiosqlite.connect(settings.db_path)
            try:
                await db3.execute(
                    "INSERT INTO tick_metrics "
                    "(simulation_id, tick, metrics) VALUES (?, ?, ?)",
                    (sim_id, metrics.tick, json.dumps(tick_record)),
                )
                await db3.commit()
            finally:
                await db3.close()

            # Narrative mutation
            if engine.should_mutate():
                candidates = engine.get_mutation_candidates()
                mutations: list[tuple[ArchetypeConfig, str, str]] = []
                new_mutations_info: list[dict[str, str]] = []
                for m_arch, narrative_content in candidates:
                    try:
                        mutated = await llm.mutate_narrative(
                            archetype_name=m_arch.name,
                            archetype_description=m_arch.name,
                            mutation_style=m_arch.mutation_style,
                            narrative_content=narrative_content,
                        )
                        mutations.append((
                            m_arch,
                            mutated.content,
                            mutated.mutation_type.value,
                        ))
                        new_mutations_info.append({
                            "archetype": m_arch.name,
                            "type": mutated.mutation_type.value,
                            "content": mutated.content[:100],
                        })
                    except Exception:
                        logger.warning(
                            "mutation_failed",
                            archetype=m_arch.name,
                        )
                if mutations:
                    engine.apply_mutations(mutations)
                    # Broadcast mutation event
                    await ws_manager.broadcast(sim_id, {
                        "type": "mutations",
                        "tick": metrics.tick,
                        "new_mutations": new_mutations_info,
                    })

            # Check convergence
            if metrics.state_counts["S"] == 0:
                break
            if (
                metrics.state_counts["M"] == 0
                and metrics.state_counts["I"] == 0
            ):
                break

            tick_delay = 1.0 / control.speed
            await asyncio.sleep(tick_delay)

        # 4. Generate report
        logger.info("sim_generating_report", sim_id=sim_id)
        final_counts = (
            engine.agents.get_state_counts() if engine.agents else {}
        )
        peak_vel = (
            engine.metrics_history[-1].peak_velocity
            if engine.metrics_history
            else 0.0
        )

        report_md = await llm.generate_report(
            seed_text=req.seed_text,
            population_size=req.population_size,
            topology=req.topology.value,
            total_ticks=engine.current_tick,
            final_counts=final_counts,
            peak_velocity=peak_vel,
            total_transitions=engine._total_transitions,
        )

        # 5. Save final state
        now = datetime.now(UTC).isoformat()
        db4 = await aiosqlite.connect(settings.db_path)
        try:
            if engine.agents is not None:
                await db4.execute(
                    "INSERT OR REPLACE INTO agent_snapshots "
                    "(simulation_id, agent_data) VALUES (?, ?)",
                    (sim_id, engine.agents.to_bytes()),
                )
            await db4.execute(
                "UPDATE simulations SET status = ?, current_tick = ?, "
                "completed_at = ? WHERE id = ?",
                ("completed", engine.current_tick, now, sim_id),
            )
            await db4.execute(
                "INSERT OR REPLACE INTO reports "
                "(simulation_id, content, raw_data) VALUES (?, ?, ?)",
                (
                    sim_id,
                    report_md,
                    json.dumps({
                        "final_state_counts": final_counts,
                        "total_transitions": engine._total_transitions,
                        "peak_velocity": peak_vel,
                        "total_ticks": engine.current_tick,
                    }),
                ),
            )
            await db4.commit()
        finally:
            await db4.close()

        # Build full node states for reconnecting clients
        all_node_states: dict[str, str] = {}
        if engine.agents is not None:
            for i in range(engine.agents.n):
                all_node_states[str(i)] = state_map.get(
                    int(engine.agents.states[i]), "S"
                )

        await ws_manager.broadcast(sim_id, {
            "type": "completed",
            "tick": engine.current_tick,
            "final_state_counts": final_counts,
            "node_states": all_node_states,
        })

        logger.info(
            "sim_completed",
            sim_id=sim_id,
            ticks=engine.current_tick,
            final_counts=final_counts,
        )

    except Exception:
        logger.exception("sim_failed", sim_id=sim_id)
        db5 = await aiosqlite.connect(settings.db_path)
        try:
            await db5.execute(
                "UPDATE simulations SET status = ? WHERE id = ?",
                ("failed", sim_id),
            )
            await db5.commit()
        finally:
            await db5.close()
    finally:
        _running_engines.pop(sim_id, None)
        ws_manager.cleanup(sim_id)


# --- Pause / Resume / Step endpoints ---


@router.post("/{sim_id}/pause", response_model=SimulationStatusResponse)
async def pause_simulation(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> SimulationStatusResponse:
    """Pause a running simulation."""
    cursor = await db.execute(
        "SELECT status FROM simulations WHERE id = ?", (sim_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if row[0] != "running":
        raise HTTPException(
            status_code=400, detail=f"Cannot pause: status is {row[0]}"
        )

    control = ws_manager.get_control(sim_id)
    control.pause()

    await db.execute(
        "UPDATE simulations SET status = ? WHERE id = ?",
        ("paused", sim_id),
    )
    await db.commit()

    return SimulationStatusResponse(id=sim_id, status="paused")


@router.post("/{sim_id}/resume", response_model=SimulationStatusResponse)
async def resume_simulation(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> SimulationStatusResponse:
    """Resume a paused simulation."""
    cursor = await db.execute(
        "SELECT status FROM simulations WHERE id = ?", (sim_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if row[0] != "paused":
        raise HTTPException(
            status_code=400, detail=f"Cannot resume: status is {row[0]}"
        )

    control = ws_manager.get_control(sim_id)
    control.resume()

    await db.execute(
        "UPDATE simulations SET status = ? WHERE id = ?",
        ("running", sim_id),
    )
    await db.commit()

    return SimulationStatusResponse(id=sim_id, status="running")


@router.post("/{sim_id}/step", response_model=SimulationStatusResponse)
async def step_simulation(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> SimulationStatusResponse:
    """Advance a paused simulation by one tick."""
    cursor = await db.execute(
        "SELECT status FROM simulations WHERE id = ?", (sim_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if row[0] != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Can only step when paused: status is {row[0]}",
        )

    control = ws_manager.get_control(sim_id)
    control.step()

    return SimulationStatusResponse(id=sim_id, status="paused")


# --- Agent detail endpoint ---


@router.get(
    "/{sim_id}/agents/{agent_id}",
    response_model=AgentDetailResponse,
)
async def get_agent_detail(
    sim_id: str,
    agent_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> AgentDetailResponse:
    """Get detailed info for a specific agent."""
    engine = _running_engines.get(sim_id)
    agents = engine.agents if engine is not None else None

    # Fall back to stored snapshot
    if agents is None:
        cursor = await db.execute(
            "SELECT agent_data FROM agent_snapshots WHERE simulation_id = ?",
            (sim_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Simulation not running and no snapshot available",
            )
        agents = AgentPopulation.from_bytes(row[0])

    if agent_id < 0 or agent_id >= agents.n:
        raise HTTPException(
            status_code=404, detail="Agent not found"
        )

    state_map = {0: "S", 1: "M", 2: "I", 3: "R"}

    # Find archetype name
    arch_id = int(agents.archetype_id[agent_id])
    arch_name = "Unknown"
    if engine is not None:
        for arch in engine.archetypes:
            if arch.id == arch_id:
                arch_name = arch.name
                break
    else:
        cursor = await db.execute(
            "SELECT name FROM archetypes WHERE simulation_id = ? AND id = ?",
            (sim_id, arch_id),
        )
        row = await cursor.fetchone()
        if row is not None:
            arch_name = row[0]

    return AgentDetailResponse(
        id=agent_id,
        archetype_id=arch_id,
        archetype_name=arch_name,
        state=state_map.get(int(agents.states[agent_id]), "S"),
        susceptibility=float(agents.susceptibility[agent_id]),
        trust_threshold=float(agents.trust_threshold[agent_id]),
        influence_score=float(agents.influence_score[agent_id]),
        open_mindedness=float(agents.open_mindedness[agent_id]),
        emotional_reactivity=float(
            agents.emotional_reactivity[agent_id]
        ),
        community_id=int(agents.community_id[agent_id]),
        exposure_count=int(agents.exposure_count[agent_id]),
        ticks_in_state=int(agents.ticks_in_state[agent_id]),
        confidence=float(agents.confidence[agent_id]),
        narrative_id=agents.narrative_ids[agent_id],
        state_transitions=[
            {"tick": t, "from": state_map.get(f, "?"), "to": state_map.get(to, "?")}
            for t, f, to in agents.state_transitions[agent_id]
        ],
    )


# --- CRUD endpoints ---


@router.get("", response_model=list[SimulationSummary])
async def list_simulations(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[SimulationSummary]:
    """List all simulations, most recent first."""
    cursor = await db.execute(
        "SELECT id, status, config, current_tick, created_at "
        "FROM simulations ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    results = []
    for row in rows:
        config = json.loads(row[2])
        results.append(
            SimulationSummary(
                id=row[0],
                status=row[1],
                seed_text=config.get("seed_text", ""),
                population_size=config.get("population_size", 0),
                topology=config.get("topology", ""),
                current_tick=row[3],
                created_at=row[4],
            )
        )
    return results


@router.get("/{sim_id}", response_model=SimulationDetail)
async def get_simulation(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> SimulationDetail:
    """Get detailed simulation info including metrics."""
    cursor = await db.execute(
        "SELECT id, status, config, current_tick, created_at, "
        "completed_at FROM simulations WHERE id = ?",
        (sim_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    config = json.loads(row[2])

    final_counts = None
    peak_velocity = None
    total_transitions = None
    metrics_history = None

    if row[1] == "completed":
        report_cursor = await db.execute(
            "SELECT raw_data FROM reports WHERE simulation_id = ?",
            (sim_id,),
        )
        report_row = await report_cursor.fetchone()
        if report_row and report_row[0]:
            raw = json.loads(report_row[0])
            final_counts = raw.get("final_state_counts")
            peak_velocity = raw.get("peak_velocity")
            total_transitions = raw.get("total_transitions")

        metrics_cursor = await db.execute(
            "SELECT metrics FROM tick_metrics "
            "WHERE simulation_id = ? ORDER BY tick",
            (sim_id,),
        )
        metrics_rows = await metrics_cursor.fetchall()
        metrics_history = [json.loads(m[0]) for m in metrics_rows]

    return SimulationDetail(
        id=row[0],
        status=row[1],
        seed_text=config.get("seed_text", ""),
        population_size=config.get("population_size", 0),
        topology=config.get("topology", ""),
        max_ticks=config.get("max_ticks", 100),
        current_tick=row[3],
        created_at=row[4],
        completed_at=row[5],
        final_state_counts=final_counts,
        peak_velocity=peak_velocity,
        total_transitions=total_transitions,
        metrics_history=metrics_history,
    )


@router.delete("/{sim_id}", status_code=204)
async def delete_simulation(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> None:
    """Delete a simulation and all associated data."""
    cursor = await db.execute(
        "SELECT id FROM simulations WHERE id = ?", (sim_id,)
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    await db.execute("DELETE FROM simulations WHERE id = ?", (sim_id,))
    await db.commit()


@router.get("/{sim_id}/graph")
async def get_graph(
    sim_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, object]:
    """Get the graph structure for visualization."""
    cursor = await db.execute(
        "SELECT seed_narrative, status FROM simulations WHERE id = ?",
        (sim_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if row[0] is None:
        raise HTTPException(
            status_code=404, detail="Graph data not yet available"
        )
    graph_data = json.loads(row[0])

    # Include final node states for completed simulations
    if row[1] == "completed":
        snap_cursor = await db.execute(
            "SELECT agent_data FROM agent_snapshots "
            "WHERE simulation_id = ?",
            (sim_id,),
        )
        snap_row = await snap_cursor.fetchone()
        if snap_row is not None:
            agents = AgentPopulation.from_bytes(snap_row[0])
            state_map = {0: "S", 1: "M", 2: "I", 3: "R"}
            graph_data["node_states"] = {
                str(i): state_map.get(int(agents.states[i]), "S")
                for i in range(agents.n)
            }

    return graph_data  # type: ignore[no-any-return]
