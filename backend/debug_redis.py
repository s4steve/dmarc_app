#!/usr/bin/env python3
"""
Debug Redis storage directly
"""

def debug_redis():
    import redis
    import hashlib
    from app.core.security import create_access_token
    
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Test token
    test_user_data = {
        "sub": "test@example.com",
        "customer_id": "test_customer", 
        "role": "user",
        "user_id": "test_user"
    }
    
    token = create_access_token(test_user_data)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    print(f"Token: {token[:20]}...")
    print(f"Token hash: {token_hash}")
    
    # Blacklist the token manually
    blacklist_key = f"blacklist:{token_hash}"
    r.setex(blacklist_key, 3600, "test")
    
    print(f"Blacklist key: {blacklist_key}")
    print(f"Key exists: {r.exists(blacklist_key)}")
    print(f"Key value: {r.get(blacklist_key)}")
    
    # List all keys
    keys = r.keys("blacklist:*")
    print(f"All blacklist keys: {keys}")
    
    # Test with session service
    from app.services.session_service import session_service
    is_blacklisted = session_service.is_token_blacklisted(token)
    print(f"Session service check: {is_blacklisted}")

if __name__ == "__main__":
    debug_redis()