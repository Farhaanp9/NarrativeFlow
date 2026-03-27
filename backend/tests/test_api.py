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
