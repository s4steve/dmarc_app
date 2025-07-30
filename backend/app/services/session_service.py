"""
Session Management Service for secure token handling and session tracking
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from redis import Redis
from jose import jwt, JWTError
from ..core.config import settings
import logging

logger = logging.getLogger("security")

class SessionService:
    """Service for managing user sessions and token blacklisting"""
    
    def __init__(self):
        try:
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis.ping()
            logger.info("Session service initialized with Redis connection")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for session management: {e}")
            self.redis = None
    
    def _get_token_hash(self, token: str) -> str:
        """Create a hash of the token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def create_session(self, user_id: str, customer_id: str, token: str, expires_at: datetime) -> bool:
        """
        Create a new user session
        
        Args:
            user_id: User identifier
            customer_id: Customer identifier  
            token: JWT token
            expires_at: Token expiration time
            
        Returns:
            True if session created successfully
        """
        if not self.redis:
            logger.warning("Redis not available, sessions not tracked")
            return True
        
        try:
            token_hash = self._get_token_hash(token)
            session_key = f"session:{user_id}:{token_hash}"
            
            session_data = {
                "user_id": user_id,
                "customer_id": customer_id,
                "token_hash": token_hash,  # Store hash for reference
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "ip_address": None,  # Will be set by middleware
                "user_agent": None   # Will be set by middleware
            }
            
            # Store session with expiration
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            self.redis.setex(session_key, ttl, json.dumps(session_data))
            
            # Add to user's active sessions set with token hash mapping
            user_sessions_key = f"user_sessions:{user_id}"
            self.redis.sadd(user_sessions_key, token_hash)
            self.redis.expire(user_sessions_key, ttl)
            
            # Store token hash to token mapping for logout-all (with short TTL)
            token_mapping_key = f"token_map:{token_hash}"
            self.redis.setex(token_mapping_key, ttl, token)
            
            logger.info(f"Session created for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted
        """
        if not self.redis:
            return False
        
        try:
            token_hash = self._get_token_hash(token)
            blacklist_key = f"blacklist:{token_hash}"
            return bool(self.redis.exists(blacklist_key))
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    def blacklist_token(self, token: str, reason: str = "logout") -> bool:
        """
        Add token to blacklist
        
        Args:
            token: JWT token to blacklist
            reason: Reason for blacklisting
            
        Returns:
            True if successfully blacklisted
        """
        if not self.redis:
            logger.warning("Redis not available, token blacklisting disabled")
            return True
        
        try:
            # Extract expiration from token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            exp_timestamp = payload.get('exp', 0)
            expires_at = datetime.fromtimestamp(exp_timestamp)
            
            # Only blacklist if token hasn't expired
            current_time = datetime.utcnow()
            if expires_at > current_time:
                token_hash = self._get_token_hash(token)
                blacklist_key = f"blacklist:{token_hash}"
                
                blacklist_data = {
                    "reason": reason,
                    "blacklisted_at": current_time.isoformat(),
                    "expires_at": expires_at.isoformat()
                }
                
                # Store until token would naturally expire (minimum 60 seconds)
                ttl = max(int((expires_at - current_time).total_seconds()), 60)
                self.redis.setex(blacklist_key, ttl, json.dumps(blacklist_data))
                
                # Remove from active sessions
                user_id = payload.get('sub')
                if user_id:
                    self._remove_from_user_sessions(user_id, token_hash)
                
                logger.info(f"Token blacklisted for reason: {reason}")
                return True
            
            return True  # Already expired
            
        except JWTError:
            logger.warning("Invalid token provided for blacklisting")
            return False
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def _remove_from_user_sessions(self, user_id: str, token_hash: str):
        """Remove token from user's active sessions"""
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            self.redis.srem(user_sessions_key, token_hash)
            
            # Remove session data
            session_key = f"session:{user_id}:{token_hash}"
            self.redis.delete(session_key)
        except Exception as e:
            logger.error(f"Failed to remove from user sessions: {e}")
    
    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of session information
        """
        if not self.redis:
            return []
        
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            token_hashes = self.redis.smembers(user_sessions_key)
            
            sessions = []
            for token_hash in token_hashes:
                session_key = f"session:{user_id}:{token_hash}"
                session_data = self.redis.get(session_key)
                if session_data:
                    sessions.append(json.loads(session_data))
            
            return sessions
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def invalidate_all_user_sessions(self, user_id: str, reason: str = "security") -> bool:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User identifier
            reason: Reason for invalidation
            
        Returns:
            True if successful
        """
        if not self.redis:
            return True
        
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            token_hashes = self.redis.smembers(user_sessions_key)
            
            for token_hash in token_hashes:
                # Get the actual token from mapping
                token_mapping_key = f"token_map:{token_hash}"
                token = self.redis.get(token_mapping_key)
                
                if token:
                    # Blacklist the actual token using the proper method
                    self.blacklist_token(token, reason)
                else:
                    # Fallback: blacklist using hash (for already logged out sessions)
                    blacklist_key = f"blacklist:{token_hash}"
                    blacklist_data = {
                        "reason": reason,
                        "blacklisted_at": datetime.utcnow().isoformat(),
                        "user_id": user_id
                    }
                    self.redis.setex(blacklist_key, 86400, json.dumps(blacklist_data))  # 24 hours
                
                # Remove session
                session_key = f"session:{user_id}:{token_hash}"
                self.redis.delete(session_key)
                
                # Remove token mapping
                self.redis.delete(token_mapping_key)
            
            # Clear user sessions set
            self.redis.delete(user_sessions_key)
            
            logger.info(f"All sessions invalidated for user {user_id}, reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {e}")
            return False
    
    def update_session_activity(self, token: str, ip_address: str, user_agent: str) -> bool:
        """
        Update session activity information
        
        Args:
            token: JWT token
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if updated successfully
        """
        if not self.redis:
            return True
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get('sub')
            
            if user_id:
                token_hash = self._get_token_hash(token)
                session_key = f"session:{user_id}:{token_hash}"
                
                session_data = self.redis.get(session_key)
                if session_data:
                    session = json.loads(session_data)
                    session['last_accessed'] = datetime.utcnow().isoformat()
                    session['ip_address'] = ip_address
                    session['user_agent'] = user_agent
                    
                    # Update with same TTL
                    ttl = self.redis.ttl(session_key)
                    if ttl > 0:
                        self.redis.setex(session_key, ttl, json.dumps(session))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions and blacklist entries
        
        Returns:
            Number of entries cleaned up
        """
        if not self.redis:
            return 0
        
        try:
            cleaned = 0
            
            # Redis automatically expires keys, but we can clean up empty sets
            pattern = "user_sessions:*"
            for key in self.redis.scan_iter(match=pattern):
                if self.redis.scard(key) == 0:
                    self.redis.delete(key)
                    cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} expired session entries")
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

# Global session service instance
session_service = SessionService()