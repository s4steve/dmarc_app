#!/usr/bin/env python3
"""
Debug logout-all functionality
"""

from fastapi.testclient import TestClient

def debug_logout_all():
    print("🔍 Debugging Logout-All...")
    
    from app.main import app
    
    with TestClient(app) as client:
        # Login to get tokens
        login_data = {"email": "admin@example.com", "password": "admin123"}
        
        # Create multiple sessions
        tokens = []
        for i in range(2):  # Only create 2 to avoid rate limiting
            response = client.post("/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token = response.json().get("access_token")
                tokens.append(token)
                print(f"  ✅ Created session {i+1}: {token[:20]}...")
            else:
                print(f"  ❌ Failed to create session {i+1}: {response.status_code}")
                return
        
        # Test that all tokens work initially
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/auth/sessions", headers=headers)
            print(f"  🔍 Token {i+1} status: {response.status_code}")
        
        # Logout-all using the first token
        headers1 = {"Authorization": f"Bearer {tokens[0]}"}
        print(f"\n  🔍 Calling logout-all with token 1...")
        logout_all_response = client.post("/api/v1/auth/logout-all", headers=headers1)
        print(f"  🔍 Logout-all response: {logout_all_response.status_code}")
        print(f"  🔍 Logout-all body: {logout_all_response.json()}")
        
        # Test all tokens after logout-all
        print(f"\n  🔍 Testing tokens after logout-all...")
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/auth/sessions", headers=headers)
            print(f"  🔍 Token {i+1} status after logout-all: {response.status_code}")
            if response.status_code != 401:
                print(f"     Response: {response.json()}")
        
        # Check Redis state
        print(f"\n  🔍 Checking Redis state...")
        from app.services.session_service import session_service
        from app.core.security import verify_token
        
        # Get user info from first token
        try:
            payload = verify_token(tokens[0])
            user_id = payload.get("sub", "unknown")
            print(f"  🔍 User ID from token: {user_id}")
            
            # Check user sessions
            sessions = session_service.get_user_sessions(user_id)
            print(f"  🔍 Active sessions for user: {len(sessions)}")
            
        except Exception as e:
            print(f"  🔍 Error getting user info: {e}")
        
        for i, token in enumerate(tokens):
            is_blacklisted = session_service.is_token_blacklisted(token)
            print(f"  🔍 Token {i+1} blacklisted: {is_blacklisted}")
            
            # Check Redis keys directly
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            blacklist_key = f"blacklist:{token_hash}"
            token_map_key = f"token_map:{token_hash}"
            
            blacklist_exists = session_service.redis.exists(blacklist_key)
            token_map_exists = session_service.redis.exists(token_map_key)
            
            print(f"  🔍 Token {i+1} Redis blacklist key exists: {blacklist_exists}")
            print(f"  🔍 Token {i+1} Redis token map exists: {token_map_exists}")

if __name__ == "__main__":
    debug_logout_all()