#!/usr/bin/env python3
"""
Debug script to test session service directly
"""

def test_session_service():
    print("🔍 Testing Session Service Directly...")
    
    try:
        from app.services.session_service import session_service
        from app.core.security import create_access_token, verify_token
        from datetime import datetime, timedelta
        
        # Test Redis connection
        if session_service.redis:
            try:
                session_service.redis.ping()
                print("  ✅ Redis connection working")
            except Exception as e:
                print(f"  ❌ Redis connection failed: {e}")
                return False
        else:
            print("  ❌ Redis not initialized")
            return False
        
        # Test token creation and session tracking
        test_user_data = {
            "sub": "test@example.com",
            "customer_id": "test_customer", 
            "role": "user",
            "user_id": "test_user"
        }
        
        # Create token
        token = create_access_token(test_user_data)
        print(f"  ✅ Token created: {token[:20]}...")
        
        # Verify token works
        payload = verify_token(token)
        print(f"  ✅ Token verification works: {payload['sub']}")
        
        # Test blacklisting
        print(f"  🔍 About to blacklist token: {token[:30]}...")
        
        # First check token expiration
        from jose import jwt
        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_timestamp = payload.get('exp', 0)
        expires_at = datetime.fromtimestamp(exp_timestamp)
        current_time = datetime.utcnow()
        ttl = int((expires_at - current_time).total_seconds())
        print(f"  🔍 Token expires at: {expires_at}")
        print(f"  🔍 Current time: {current_time}")
        print(f"  🔍 TTL: {ttl} seconds")
        
        blacklist_result = session_service.blacklist_token(token, "test")
        print(f"  ✅ Token blacklisted: {blacklist_result}")
        
        # Test if token is blacklisted
        print(f"  🔍 Checking blacklist for token: {token[:30]}...")
        is_blacklisted = session_service.is_token_blacklisted(token)
        print(f"  🔍 Token blacklist check result: {is_blacklisted}")
        
        # Debug: Check Redis directly
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        blacklist_key = f"blacklist:{token_hash}"
        redis_exists = session_service.redis.exists(blacklist_key)
        print(f"  🔍 Redis direct check: key={blacklist_key[:30]}..., exists={redis_exists}")
        
        # Try to verify blacklisted token
        try:
            verify_token(token)
            print(f"  ❌ Blacklisted token still works!")
            return False
        except Exception as e:
            print(f"  ✅ Blacklisted token properly rejected: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Session service test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_session_service()