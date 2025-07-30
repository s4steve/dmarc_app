#!/usr/bin/env python3
"""
Test script to validate Phase 2 security improvements:
- Session management and token blacklisting
- Security headers
- Error message sanitization
- Logout functionality
"""

import sys
import requests
import json
from fastapi.testclient import TestClient

def test_session_management():
    """Test session management and token blacklisting"""
    print("🔍 Testing Session Management...")
    
    try:
        from app.main import app
        from app.services.session_service import session_service
        
        with TestClient(app) as client:
            # Test login to get token
            login_data = {"email": "admin@example.com", "password": "admin123"}
            login_response = client.post("/api/v1/auth/login", json=login_data)
            
            if login_response.status_code != 200:
                print(f"  ❌ Login failed: {login_response.status_code}")
                return False
            
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test authenticated endpoint works
            profile_response = client.get("/api/v1/auth/sessions", headers=headers)
            if profile_response.status_code == 200:
                print(f"  ✅ Authentication working with token")
            else:
                print(f"  ❌ Token authentication failed: {profile_response.status_code}")
                return False
            
            # Test logout (should blacklist token)
            logout_response = client.post("/api/v1/auth/logout", headers=headers)
            if logout_response.status_code == 200:
                print(f"  ✅ Logout endpoint working")
            else:
                print(f"  ❌ Logout failed: {logout_response.status_code}")
                return False
            
            # Test that token is now blacklisted
            profile_response2 = client.get("/api/v1/auth/sessions", headers=headers)
            if profile_response2.status_code == 401:
                print(f"  ✅ Token successfully blacklisted after logout")
            else:
                print(f"  ❌ Token not blacklisted: {profile_response2.status_code}")
                return False
            
            # Test logout-all endpoint
            login_response2 = client.post("/api/v1/auth/login", json=login_data)
            token2 = login_response2.json().get("access_token")
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            logout_all_response = client.post("/api/v1/auth/logout-all", headers=headers2)
            if logout_all_response.status_code == 200:
                print(f"  ✅ Logout-all endpoint working")
            else:
                print(f"  ❌ Logout-all failed: {logout_all_response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Session management test error: {e}")
        return False

def test_security_headers():
    """Test security headers middleware"""
    print("🔍 Testing Security Headers...")
    
    try:
        from app.main import app
        
        with TestClient(app) as client:
            response = client.get("/health")
            
            expected_headers = [
                "X-Content-Type-Options",
                "X-XSS-Protection", 
                "X-Frame-Options",
                "Referrer-Policy",
                "Content-Security-Policy",
                "Permissions-Policy",
                "Cache-Control"
            ]
            
            missing_headers = []
            for header in expected_headers:
                if header not in response.headers:
                    missing_headers.append(header)
                else:
                    print(f"  ✅ {header}: {response.headers[header][:50]}...")
            
            if missing_headers:
                print(f"  ❌ Missing security headers: {missing_headers}")
                return False
            
            # Check specific header values
            if response.headers.get("X-Frame-Options") != "DENY":
                print(f"  ❌ X-Frame-Options should be DENY")
                return False
            
            if "nosniff" not in response.headers.get("X-Content-Type-Options", ""):
                print(f"  ❌ X-Content-Type-Options should contain nosniff")
                return False
            
            print(f"  ✅ All required security headers present")
            return True
        
    except Exception as e:
        print(f"  ❌ Security headers test error: {e}")
        return False

def test_error_sanitization():
    """Test error message sanitization"""
    print("🔍 Testing Error Message Sanitization...")
    
    try:
        from app.main import app
        from app.utils.error_sanitizer import ErrorSanitizer
        
        # Test error sanitizer directly
        sensitive_error = "Database connection failed at postgresql://user:pass@localhost:5432/db"
        sanitized = ErrorSanitizer.sanitize_error_message(sensitive_error, "database")
        
        if "postgresql://" in sanitized:
            print(f"  ❌ Database connection string not sanitized: {sanitized}")
            return False
        else:
            print(f"  ✅ Database connection string sanitized")
        
        # Test file path sanitization
        path_error = "File not found: /home/user/app/secrets.py line 123"
        sanitized_path = ErrorSanitizer.sanitize_error_message(path_error, "file")
        
        if "/home/user/" in sanitized_path:
            print(f"  ❌ File path not sanitized: {sanitized_path}")
            return False
        else:
            print(f"  ✅ File path sanitized")
        
        # Test API error handling
        with TestClient(app) as client:
            # Test invalid JSON to trigger validation error
            response = client.post("/api/v1/auth/login", json={"invalid": "data"})
            
            if response.status_code != 422:
                print(f"  ❌ Expected validation error, got: {response.status_code}")
                return False
            
            error_data = response.json()
            if "error" not in error_data:
                print(f"  ❌ Error response missing error field: {error_data}")
                return False
            
            print(f"  ✅ Validation errors properly formatted")
            
            # Test 404 error handling
            response = client.get("/nonexistent-endpoint")
            if response.status_code == 404:
                print(f"  ✅ 404 errors handled properly")
            else:
                print(f"  ❌ Unexpected response for 404: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error sanitization test error: {e}")
        return False

def test_logout_functionality():
    """Test comprehensive logout functionality"""
    print("🔍 Testing Logout Functionality...")
    
    try:
        from app.main import app
        
        with TestClient(app) as client:
            # Login to get tokens
            login_data = {"email": "admin@example.com", "password": "admin123"}
            
            # Create multiple sessions
            tokens = []
            for i in range(3):
                response = client.post("/api/v1/auth/login", json=login_data)
                if response.status_code == 200:
                    tokens.append(response.json().get("access_token"))
                else:
                    print(f"  ❌ Failed to create session {i+1}")
                    return False
            
            print(f"  ✅ Created {len(tokens)} sessions")
            
            # Test that all tokens work
            working_tokens = 0
            for i, token in enumerate(tokens):
                headers = {"Authorization": f"Bearer {token}"}
                response = client.get("/api/v1/auth/sessions", headers=headers)
                if response.status_code == 200:
                    working_tokens += 1
            
            if working_tokens != len(tokens):
                print(f"  ❌ Not all tokens working: {working_tokens}/{len(tokens)}")
                return False
            
            print(f"  ✅ All {working_tokens} tokens working")
            
            # Logout from one session
            headers1 = {"Authorization": f"Bearer {tokens[0]}"}
            logout_response = client.post("/api/v1/auth/logout", headers=headers1)
            
            if logout_response.status_code != 200:
                print(f"  ❌ Single logout failed: {logout_response.status_code}")
                return False
            
            # Check that first token is invalidated but others work
            response1 = client.get("/api/v1/auth/sessions", headers=headers1)
            headers2 = {"Authorization": f"Bearer {tokens[1]}"}
            response2 = client.get("/api/v1/auth/sessions", headers=headers2)
            
            if response1.status_code != 401:
                print(f"  ❌ First token not invalidated after logout")
                return False
            
            if response2.status_code != 200:
                print(f"  ❌ Second token incorrectly invalidated")
                return False
            
            print(f"  ✅ Single logout working correctly")
            
            # Test logout-all
            logout_all_response = client.post("/api/v1/auth/logout-all", headers=headers2)
            if logout_all_response.status_code != 200:
                print(f"  ❌ Logout-all failed: {logout_all_response.status_code}")
                return False
            
            # Check that all remaining tokens are invalidated
            invalidated_count = 0
            for i, token in enumerate(tokens[1:], 1):  # Skip first token (already logged out)
                headers = {"Authorization": f"Bearer {token}"}
                response = client.get("/api/v1/auth/sessions", headers=headers)
                if response.status_code == 401:
                    invalidated_count += 1
            
            if invalidated_count != len(tokens) - 1:
                print(f"  ❌ Not all tokens invalidated by logout-all: {invalidated_count}/{len(tokens)-1}")
                return False
            
            print(f"  ✅ Logout-all working correctly")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Logout functionality test error: {e}")
        return False

def main():
    """Run all Phase 2 security tests"""
    print("🛡️  DMARC Analytics Platform - Phase 2 Security Validation")
    print("=" * 65)
    
    tests = [
        ("Session Management", test_session_management),
        ("Security Headers", test_security_headers),
        ("Error Sanitization", test_error_sanitization),
        ("Logout Functionality", test_logout_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 65)
    print("📊 PHASE 2 SECURITY VALIDATION SUMMARY")
    print("=" * 65)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All Phase 2 security improvements are working!")
        return 0
    else:
        print("⚠️  Some Phase 2 security features need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())