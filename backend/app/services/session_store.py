
"""
app/services/session_store.py
 
Lightweight in-memory conversation session store.
Replace with Redis for multi-worker / production deployments:
 
    pip install redis
    from redis import Redis
    r = Redis.from_url(settings.REDIS_URL)
    r.setex(session_id, 3600, json.dumps(session))
"""

from __future__ import annotations
import uuid
from typing import Optional

class SessionStore:
    def __init__(self):
        self._data: dict[str, dict] = {}

    # Creeate session with a unique session_id and owner_id
    def create_session(self, session_id: str, owner_id: str) -> dict:
        if session_id not in self._data:
            self._data[session_id] = {
                "session_id": session_id,
                "owner_id": owner_id,
                "history": []
            }

        return self._data[session_id]

    # Get session by session_id
    def get_session(self, session_id: str) -> Optional[dict]:
        return self._data.get(session_id)

    def save_session(self, session_id: str, session_data: dict) -> None:
        self._data[session_id] = session_data

    # Delete session by session_id
    def delete_session(self, session_id: str) -> None:
        if session_id in self._data:
            del self._data[session_id]