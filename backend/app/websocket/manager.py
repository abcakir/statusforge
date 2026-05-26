import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._global: list[WebSocket] = []
        self._service: dict[str, list[WebSocket]] = {}

    async def connect_global(self, ws: WebSocket) -> None:
        await ws.accept()
        self._global.append(ws)

    async def connect_service(self, ws: WebSocket, service_id: str) -> None:
        await ws.accept()
        self._service.setdefault(service_id, []).append(ws)

    def disconnect_global(self, ws: WebSocket) -> None:
        if ws in self._global:
            self._global.remove(ws)

    def disconnect_service(self, ws: WebSocket, service_id: str) -> None:
        conns = self._service.get(service_id, [])
        if ws in conns:
            conns.remove(ws)

    async def _send_all(self, connections: list[WebSocket], data: str) -> list[WebSocket]:
        dead = []
        for ws in list(connections):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        return dead

    async def broadcast_global(self, message: dict) -> None:
        data = json.dumps(message)
        dead = await self._send_all(self._global, data)
        for ws in dead:
            self.disconnect_global(ws)

    async def broadcast_service(self, service_id: str, message: dict) -> None:
        data = json.dumps(message)
        dead = await self._send_all(self._service.get(service_id, []), data)
        for ws in dead:
            self.disconnect_service(ws, service_id)


manager = ConnectionManager()
