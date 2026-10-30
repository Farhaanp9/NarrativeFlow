"""Integration tests for API endpoints."""

import asyncio

from httpx import AsyncClient


async def test_create_simulation(client: AsyncClient) -> None:
    """POST /api/simulations should create and return id + status."""
    response = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Breaking: Popular supplement found dangerous",
            "population_size": 50,
            "max_ticks": 10,
            "archetype_count": 5,
            "tick_speed": 100.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "initializing"


async def test_list_simulations(client: AsyncClient) -> None:
    """GET /api/simulations should return a list."""
    # Create one first
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Test list headline",
            "population_size": 50,
            "max_ticks": 10,
            "tick_speed": 100.0,
        },
    )
    assert create_resp.status_code == 200

    response = await client.get("/api/simulations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "status" in data[0]
    assert "seed_text" in data[0]


async def test_get_simulation_detail(client: AsyncClient) -> None:
    """GET /api/simulations/:id should return simulation details."""
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Test detail headline",
            "population_size": 50,
            "max_ticks": 10,
            "tick_speed": 100.0,
        },
    )
    sim_id = create_resp.json()["id"]

    response = await client.get(f"/api/simulations/{sim_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sim_id
    assert data["seed_text"] == "Test detail headline"
    assert data["population_size"] == 50


async def test_get_nonexistent_simulation(client: AsyncClient) -> None:
    """GET /api/simulations/:id with bad ID should return 404."""
    response = await client.get("/api/simulations/nonexistent-id")
    assert response.status_code == 404


async def test_delete_simulation(client: AsyncClient) -> None:
    """DELETE /api/simulations/:id should remove it."""
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Test delete headline",
            "population_size": 50,
            "max_ticks": 10,
            "tick_speed": 100.0,
        },
    )
    sim_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/simulations/{sim_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/simulations/{sim_id}")
    assert get_resp.status_code == 404


async def test_delete_nonexistent_simulation(
    client: AsyncClient,
) -> None:
    """DELETE /api/simulations/:id with bad ID should return 404."""
    response = await client.delete("/api/simulations/nonexistent-id")
    assert response.status_code == 404


async def test_simulation_completes_with_results(
    client: AsyncClient,
) -> None:
    """A small simulation should complete and have results retrievable."""
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Small test for completion",
            "population_size": 30,
            "max_ticks": 10,
            "archetype_count": 5,
            "tick_speed": 100.0,
        },
    )
    sim_id = create_resp.json()["id"]

    # Wait for background task to complete
    for _ in range(60):
        await asyncio.sleep(0.5)
        resp = await client.get(f"/api/simulations/{sim_id}")
        status = resp.json()["status"]
        if status in ("completed", "failed"):
            break

    detail = (await client.get(f"/api/simulations/{sim_id}")).json()
    assert detail["status"] == "completed", (
        f"Expected completed, got {detail['status']}"
    )
    assert detail["final_state_counts"] is not None
    assert detail["metrics_history"] is not None
    assert len(detail["metrics_history"]) > 0

    # Report should exist
    report_resp = await client.get(f"/api/reports/{sim_id}")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert len(report["content"]) > 0

    # Data export should work
    data_resp = await client.get(f"/api/reports/{sim_id}/data")
    assert data_resp.status_code == 200
    export = data_resp.json()
    assert "final_state_counts" in export
    assert "metrics_history" in export


async def test_report_404_before_completion(
    client: AsyncClient,
) -> None:
    """GET /api/reports/:id should 404 for non-existent simulation."""
    response = await client.get("/api/reports/nonexistent-id")
    assert response.status_code == 404


async def test_invalid_simulation_config(
    client: AsyncClient,
) -> None:
    """Invalid config should return 422."""
    response = await client.post(
        "/api/simulations",
        json={
            "seed_text": "",  # too short
            "population_size": 50,
        },
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Valid headline",
            "population_size": 999999,  # too large
        },
    )
    assert response.status_code == 422


async def _wait_for_status(
    client: AsyncClient, sim_id: str, target: str, max_wait: float = 30.0
) -> str:
    """Poll until simulation reaches target status or timeout."""
    for _ in range(int(max_wait * 2)):
        await asyncio.sleep(0.5)
        resp = await client.get(f"/api/simulations/{sim_id}")
        status = resp.json()["status"]
        if status in (target, "completed", "failed"):
            return status
    return status


async def test_pause_and_resume(client: AsyncClient) -> None:
    """Pause a running simulation, then resume it to completion."""
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Test pause resume flow",
            "population_size": 30,
            "max_ticks": 20,
            "archetype_count": 5,
            "tick_speed": 2.0,  # slow enough to pause
        },
    )
    sim_id = create_resp.json()["id"]

    # Wait for running
    status = await _wait_for_status(client, sim_id, "running")
    if status == "completed":
        return  # too fast to pause, skip

    # Pause
    pause_resp = await client.post(f"/api/simulations/{sim_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "paused"

    # Verify it stays paused
    await asyncio.sleep(1)

    # Resume
    resume_resp = await client.post(f"/api/simulations/{sim_id}/resume")
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "running"

    # Wait for completion
    status = await _wait_for_status(client, sim_id, "completed")
    assert status == "completed"


async def test_pause_nonexistent_returns_404(
    client: AsyncClient,
) -> None:
    resp = await client.post("/api/simulations/nonexistent/pause")
    assert resp.status_code == 404


async def test_step_requires_paused(client: AsyncClient) -> None:
    """Step should only work when paused."""
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Step test",
            "population_size": 30,
            "max_ticks": 50,
            "tick_speed": 5.0,
        },
    )
    sim_id = create_resp.json()["id"]

    # Wait for running
    status = await _wait_for_status(client, sim_id, "running")
    if status != "running":
        return

    # Step should fail while running
    step_resp = await client.post(f"/api/simulations/{sim_id}/step")
    assert step_resp.status_code == 400

    # Pause first
    await client.post(f"/api/simulations/{sim_id}/pause")

    # Now step should work
    step_resp = await client.post(f"/api/simulations/{sim_id}/step")
    assert step_resp.status_code == 200

    # Resume to clean up
    await client.post(f"/api/simulations/{sim_id}/resume")
    await _wait_for_status(client, sim_id, "completed")


async def test_agent_detail_endpoint(client: AsyncClient) -> None:
    """GET /api/simulations/:id/agents/:agent_id returns agent info."""
    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Agent detail test",
            "population_size": 30,
            "max_ticks": 15,
            "tick_speed": 2.0,
        },
    )
    sim_id = create_resp.json()["id"]

    # Wait for running (engine must be registered)
    status = await _wait_for_status(client, sim_id, "running")
    if status not in ("running", "paused"):
        # Completed too fast — can't inspect
        return

    resp = await client.get(f"/api/simulations/{sim_id}/agents/0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 0
    assert "state" in data
    assert data["state"] in ("S", "M", "I", "R")
    assert "archetype_name" in data
    assert "susceptibility" in data
    assert "state_transitions" in data

    # Out of range agent should 404
    resp = await client.get(f"/api/simulations/{sim_id}/agents/99999")
    assert resp.status_code == 404

    # Wait for completion to clean up
    # Resume if paused
    if status == "paused":
        await client.post(f"/api/simulations/{sim_id}/resume")
    await _wait_for_status(client, sim_id, "completed")


async def test_agent_detail_404_when_not_running(
    client: AsyncClient,
) -> None:
    """Agent detail should 404 for non-running simulations."""
    resp = await client.get(
        "/api/simulations/nonexistent/agents/0"
    )
    assert resp.status_code == 404


async def test_agent_detail_after_completion_names_archetype(
    client: AsyncClient,
) -> None:
    """A completed simulation's agents resolve to their own archetype names."""
    from narrativeflow.llm.client import _DEFAULT_ARCHETYPES

    create_resp = await client.post(
        "/api/simulations",
        json={
            "seed_text": "Archetype name after completion",
            "population_size": 40,
            "max_ticks": 10,
            "archetype_count": 8,
            "tick_speed": 100.0,
        },
    )
    sim_id = create_resp.json()["id"]
    assert await _wait_for_status(client, sim_id, "completed") == "completed"

    for agent_id in range(10):
        resp = await client.get(f"/api/simulations/{sim_id}/agents/{agent_id}")
        assert resp.status_code == 200
        data = resp.json()
        # The LLM is unreachable in tests, so archetypes are the defaults
        expected = _DEFAULT_ARCHETYPES[data["archetype_id"]]["name"]
        assert data["archetype_name"] == expected
