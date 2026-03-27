"""Tests for the health endpoint."""

from httpx import AsyncClient

from narrativeflow import __version__


async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == __version__
