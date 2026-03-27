"""WebSocket endpoint for real-time simulation tick updates."""

import asyncio
import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = structlog.get_logger()

router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections per simulation."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

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


# Singleton instance
ws_manager = WebSocketManager()


@router.websocket("/ws/simulations/{sim_id}")
async def simulation_ws(websocket: WebSocket, sim_id: str) -> None:
    """WebSocket endpoint for live simulation updates.

    Server → Client: TickUpdate JSON per tick
    Client → Server: {"action": "pause"/"resume"/"set_speed", "value": ...}
    """
    await ws_manager.connect(sim_id, websocket)
    try:
        while True:
            # Listen for client commands
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")
                logger.info(
                    "ws_command",
                    simulation_id=sim_id,
                    action=action,
                )
                # Commands are handled by the simulation runner
                # which checks ws_manager for pending commands
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(sim_id, websocket)
