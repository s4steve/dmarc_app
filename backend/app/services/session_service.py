"""
Session tracking and token revocation, backed by Redis.

Tokens are only ever stored as SHA-256 hashes. Revocation checks fail closed:
if Redis is unreachable, is_token_blacklisted raises and the request is rejected.
"""
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional
from redis import Redis
from ..core.config import settings

logger = logging.getLogger("security")

def _now() -> datetime:
    return datetime.now(timezone.utc)

class SessionService:
    def __init__(self):
        # redis-py connects lazily, so a Redis outage at startup recovers on its own
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def create_session(self, user_id: str, token: str, expires_at: datetime) -> None:
        token_hash = self._hash(token)
        ttl = max(int((expires_at - _now()).total_seconds()), 1)
        session = {
            "created_at": _now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_accessed": _now().isoformat(),
            "ip_address": None,
            "user_agent": None
        }
        pipe = self.redis.pipeline()
        pipe.set(f"session:{user_id}:{token_hash}", json.dumps(session), ex=ttl)
        pipe.sadd(f"user_sessions:{user_id}", token_hash)
        # Keep the set alive as long as the newest session
        pipe.expire(f"user_sessions:{user_id}", ttl, gt=True)
        pipe.expire(f"user_sessions:{user_id}", ttl, nx=True)
        pipe.execute()

    def is_token_blacklisted(self, token: str) -> bool:
        # Deliberately no try/except: a Redis failure must reject the token, not accept it
        return bool(self.redis.exists(f"blacklist:{self._hash(token)}"))

    def _revoke(self, user_id: str, token_hash: str, reason: str) -> None:
        session_key = f"session:{user_id}:{token_hash}"
        # Blacklist for as long as the token could still be valid
        ttl = self.redis.ttl(session_key)
        if ttl is None or ttl < 0:
            ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        pipe = self.redis.pipeline()
        pipe.set(
            f"blacklist:{token_hash}",
            json.dumps({"reason": reason, "blacklisted_at": _now().isoformat()}),
            ex=ttl
        )
        pipe.delete(session_key)
        pipe.srem(f"user_sessions:{user_id}", token_hash)
        pipe.execute()

    def blacklist_token(self, token: str, user_id: str, reason: str = "logout") -> None:
        self._revoke(user_id, self._hash(token), reason)
        logger.info(f"Token revoked for {user_id}, reason: {reason}")

    def invalidate_all_user_sessions(self, user_id: str, reason: str = "security") -> None:
        for token_hash in self.redis.smembers(f"user_sessions:{user_id}"):
            self._revoke(user_id, token_hash, reason)
        self.redis.delete(f"user_sessions:{user_id}")
        logger.info(f"All sessions invalidated for {user_id}, reason: {reason}")

    def get_user_sessions(self, user_id: str) -> list:
        sessions = []
        for token_hash in self.redis.smembers(f"user_sessions:{user_id}"):
            data = self.redis.get(f"session:{user_id}:{token_hash}")
            if data:
                sessions.append(json.loads(data))
        return sessions

    def update_session_activity(self, user_id: str, token: str, ip_address: Optional[str], user_agent: str) -> None:
        session_key = f"session:{user_id}:{self._hash(token)}"
        data = self.redis.get(session_key)
        ttl = self.redis.ttl(session_key)
        if not data or ttl <= 0:
            return
        session = json.loads(data)
        session.update(last_accessed=_now().isoformat(), ip_address=ip_address, user_agent=user_agent)
        self.redis.set(session_key, json.dumps(session), ex=ttl)

session_service = SessionService()
