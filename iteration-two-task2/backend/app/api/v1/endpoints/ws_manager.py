from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

from fastapi import WebSocket

# Per-session WebSocket connection manager
_connections: dict[str, list[WebSocket]] = {}
_lock = threading.Lock()


async def connect(session_id: str, ws: WebSocket) -> None:
    await ws.accept()
    with _lock:
        _connections.setdefault(session_id, []).append(ws)


def disconnect(session_id: str, ws: WebSocket) -> None:
    with _lock:
        conns = _connections.get(session_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            _connections.pop(session_id, None)


async def broadcast(session_id: str, event: str, data: dict[str, Any]) -> None:
    """Broadcast a message to all WebSocket clients for a given session."""
    with _lock:
        conns = list(_connections.get(session_id, []))
    if not conns:
        return
    message = json.dumps({"event": event, "data": data}, default=str)
    stale: list[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_text(message)
        except Exception:
            stale.append(ws)
    # Clean up stale connections
    if stale:
        with _lock:
            for ws in stale:
                conns = _connections.get(session_id, [])
                if ws in conns:
                    conns.remove(ws)


def broadcast_sync(session_id: str, event: str, data: dict[str, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast(session_id, event, data))
        return
    except RuntimeError:
        pass
    asyncio.run(broadcast(session_id, event, data))
