"""
Real-Time WebSocket Router and Connection Manager.

Manages persistent client WebSocket connections for real-time broadcasts of
crowd density updates, transit bulletins, match scores, and safety incident approvals.
"""
import json
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Connection manager for tracking and broadcasting to active WebSocket clients."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept an incoming WebSocket connection and add to active list.

        Args:
            websocket: Incoming WebSocket client instance.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket client from active connections.

        Args:
            websocket: Client WebSocket instance to remove.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send a message to a specific single WebSocket client.

        Args:
            message: Message payload string.
            websocket: Target client WebSocket instance.
        """
        await websocket.send_text(message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a JSON payload to all connected WebSocket clients.

        Prunes dead or failed client connections automatically during iteration.

        Args:
            message: Dictionary payload to JSON-serialize and send.
        """
        payload = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/updates")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint handling client connection lifecycle and real-time push feeds.

    Args:
        websocket: Client WebSocket connection.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"status": "received", "data": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
