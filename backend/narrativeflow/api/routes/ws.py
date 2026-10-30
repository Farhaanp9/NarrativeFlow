"""WebSocket endpoint for real-time simulation tick updates."""

import asyncio
import json

import aiosqlite
import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from narrativeflow.config import get_settings

logger = structlog.get_logger()

router = APIRouter()


class SimulationControl:
    """Per-simulation pause/resume/speed control via asyncio primitives."""

    def __init__(self) -> None:
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # not paused initially
        self.speed: float = 5.0
        self.step_requested = False

    def pause(self) -> None:
        self.pause_event.clear()

    def resume(self) -> None:
        self.step_requested = False
        self.pause_event.set()

    def step(self) -> None:
        """Allow exactly one tick then re-pause."""
        self.step_requested = True
        self.pause_event.set()

    def set_speed(self, speed: float) -> None:
        self.speed = max(0.1, min(100.0, speed))

    async def wait_if_paused(self) -> None:
        """Block until unpaused. Call this each tick."""
        await self.pause_event.wait()
        if self.step_requested:
            self.step_requested = False
            self.pause_event.clear()

    @property
    def is_paused(self) -> bool:
        return not self.pause_event.is_set()


class WebSocketManager:
    """Manages WebSocket connections and simulation controls."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._controls: dict[str, SimulationControl] = {}
        self._lock = asyncio.Lock()

    def get_control(self, sim_id: str) -> SimulationControl:
        """Get or create the control for a simulation."""
        if sim_id not in self._controls:
            self._controls[sim_id] = SimulationControl()
        return self._controls[sim_id]

    async def connect(self, sim_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            if sim_id not in self._connections:
                self._connections[sim_id] = []
            self._connections[sim_id].append(ws)
        logger.info("ws_connected", simulation_id=sim_id)

    async def disconnect(self, sim_id: str, ws: WebSocket) -> None:
        async with self._lock:
            if sim_id in self._connections:
                self._connections[sim_id] = [
                    c for c in self._connections[sim_id] if c is not ws
                ]
                if not self._connections[sim_id]:
                    del self._connections[sim_id]
        logger.info("ws_disconnected", simulation_id=sim_id)

    async def broadcast(
        self, sim_id: str, data: dict[str, object]
    ) -> None:
        """Send data to all connected clients for a simulation."""
        async with self._lock:
            connections = list(self._connections.get(sim_id, []))

        dead: list[WebSocket] = []
        message = json.dumps(data)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            await self.disconnect(sim_id, ws)

    def get_connection_count(self, sim_id: str) -> int:
        return len(self._connections.get(sim_id, []))

    def cleanup(self, sim_id: str) -> None:
        """Remove control state for a completed simulation."""
        self._controls.pop(sim_id, None)


# Singleton instance
ws_manager = WebSocketManager()


async def _record_status(sim_id: str, status: str) -> None:
    """Store a pause or resume, as the REST endpoints do, so reloads see it."""
    db = await aiosqlite.connect(get_settings().db_path)
    try:
        await db.execute(
            "UPDATE simulations SET status = ? "
            "WHERE id = ? AND status IN ('running', 'paused')",
            (status, sim_id),
        )
        await db.commit()
    finally:
        await db.close()


@router.websocket("/ws/simulations/{sim_id}")
async def simulation_ws(websocket: WebSocket, sim_id: str) -> None:
    """WebSocket endpoint for live simulation updates.

    Server → Client: TickUpdate JSON per tick
    Client → Server: {"action": "pause"/"resume"/"set_speed"/"step", "value": ...}
    """
    await ws_manager.connect(sim_id, websocket)
    control = ws_manager.get_control(sim_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "pause":
                    control.pause()
                    await _record_status(sim_id, "paused")
                elif action == "resume":
                    control.resume()
                    await _record_status(sim_id, "running")
                elif action == "step":
                    control.step()
                elif action == "set_speed":
                    value = msg.get("value", 5.0)
                    control.set_speed(float(value))
                logger.info(
                    "ws_command",
                    simulation_id=sim_id,
                    action=action,
                )
            except (json.JSONDecodeError, ValueError):
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(sim_id, websocket)
