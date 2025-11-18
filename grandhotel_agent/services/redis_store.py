"""
Redis session store with sliding TTL.
Sessions auto-expire after 60 minutes of inactivity.
"""
import json
from datetime import datetime, timezone
from typing import Optional
import redis.asyncio as redis
from grandhotel_agent.config import REDIS_URL, SESSION_TTL_MIN


class SessionStore:
    """
    Redis session manager with sliding TTL.

    Key pattern: sessions:{sessionId}
    TTL: 60 min (refreshed on each access)
    """

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.ttl_seconds = SESSION_TTL_MIN * 60

    async def connect(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"sessions:{session_id}"

    async def get(self, session_id: str) -> Optional[dict]:
        """
        Get session data and refresh TTL (sliding window).

        Returns:
            Session dict or None if not exists
        """
        if not self.redis_client:
            return None

        key = self._key(session_id)
        data = await self.redis_client.get(key)

        if data:
            # Refresh TTL (sliding window)
            await self.redis_client.expire(key, self.ttl_seconds)
            return json.loads(data)

        return None

    async def set(self, session_id: str, data: dict):
        """
        Set session data with TTL.
        Auto-creates session if doesn't exist.
        """
        if not self.redis_client:
            return

        key = self._key(session_id)
        await self.redis_client.setex(
            key,
            self.ttl_seconds,
            json.dumps(data)
        )

    async def touch(self, session_id: str):
        """
        Refresh session TTL without modifying data.
        Creates empty session if doesn't exist.
        """
        session = await self.get(session_id)

        if session is None:
            # Auto-create session with conversation history structure
            await self.set(session_id, {
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "language": None
            })
        # TTL already refreshed by get()


# Global store instance
_store: Optional[SessionStore] = None


async def get_session_store() -> SessionStore:
    """Get or create global session store"""
    global _store
    if _store is None:
        _store = SessionStore()
        await _store.connect()
    return _store
