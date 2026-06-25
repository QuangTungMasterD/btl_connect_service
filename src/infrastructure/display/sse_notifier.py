import asyncio
import json
import logging
from typing import Set

import httpx
from src.core.interfaces import DisplayNotifier
from src.shared.config import Config

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[asyncio.Queue] = set()

    async def connect(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.active_connections.add(q)
        logger.info(f"SSE client connected. Total: {len(self.active_connections)}")
        return q

    def disconnect(self, q: asyncio.Queue):
        self.active_connections.discard(q)
        logger.info(f"SSE client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """broadcast nhận dict, EventSourceResponse sẽ tự động format đúng SSE"""
        for q in self.active_connections:
            await q.put(message)   # chỉ gửi dict, không format sẵn

manager = ConnectionManager()

class SseDisplayNotifier(DisplayNotifier):
    async def notify(self, user_id: str, message: str) -> None:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"http://{Config.API_HOST}:{Config.API_PORT}/internal/notify",
                    json={
                        "userId": user_id,
                        "message": message,
                        "timestamp": asyncio.get_event_loop().time(),
                        # "severity": severity,
                    },
                    timeout=5.0
                )
            logger.info(f"Forwarded to API for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to forward: {e}")