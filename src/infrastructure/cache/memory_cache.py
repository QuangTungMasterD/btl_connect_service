from src.core.interfaces import IdempotencyCache
from datetime import datetime, timedelta

class MemoryCache(IdempotencyCache):
    def __init__(self, ttl_minutes=1440):  # 24h
        self._store = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    async def is_processed(self, event_id: str) -> bool:
        if event_id in self._store:
            timestamp, _ = self._store[event_id]
            if datetime.now() - timestamp < self.ttl:
                return True
            else:
                del self._store[event_id]
        return False
    
    async def mark_processed(self, event_id: str):
        self._store[event_id] = (datetime.now(), True)