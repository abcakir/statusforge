import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.redis import get_pubsub_redis
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _redis_forward(pubsub, broadcast_fn):
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                await broadcast_fn(json.loads(message["data"]))
            except Exception as e:
                logger.error("WS forward error: %s", e)


@router.websocket("/ws")
async def ws_global(ws: WebSocket):
    await manager.connect_global(ws)
    pubsub = get_pubsub_redis().pubsub()
    await pubsub.subscribe("ws:global")
    task = asyncio.create_task(_redis_forward(pubsub, manager.broadcast_global))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_global(ws)
    finally:
        task.cancel()
        await pubsub.unsubscribe("ws:global")


@router.websocket("/ws/services/{service_id}")
async def ws_service(ws: WebSocket, service_id: str):
    await manager.connect_service(ws, service_id)
    channel = f"ws:service:{service_id}"
    pubsub = get_pubsub_redis().pubsub()
    await pubsub.subscribe(channel)
    task = asyncio.create_task(
        _redis_forward(pubsub, lambda msg: manager.broadcast_service(service_id, msg))
    )
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_service(ws, service_id)
    finally:
        task.cancel()
        await pubsub.unsubscribe(channel)
