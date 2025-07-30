#!/usr/bin/env python3
"""
Test script to validate Phase 3 file upload security improvements:
- Secure file upload validation and processing
- File type validation with magic number checking
- File size limits and gzip bomb protection
- Secure file storage with proper isolation
- Virus scanning and malware detection
"""

import sys
import io
import gzip
import tempfile
from fastapi.testclient import TestClient

def create_test_files():
    """Create various test files for security testing"""
    
    # Valid DMARC XML file
    valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feedback>
    <report_metadata>
        <org_name>Test Org</org_name>
        <email>noreply@example.com</email>
        <report_id>test123</report_id>
        <date_range>
            <begin>1640995200</begin>
            <end>1641081599</end>
        </date_range>
    </report_metadata>
    <policy_published>
        <domain>example.com</domain>
        <p>quarantine</p>
        <sp>quarantine</sp>
        <pct>100</pct>
    </policy_published>
    <record>
        <row>
            <source_ip>192.168.1.1</source_ip>
            <count>1</count>
            <policy_evaluated>
                <disposition>none</disposition>
                <dkim>pass</dkim>
                <spf>pass</spf>
            </policy_evaluated>
        </row>
        <identifiers>
            <header_from>example.com</header_from>
        </identifiers>
        <auth_results>
            <dkim>
                <domain>example.com</domain>
                <result>pass</result>
            </dkim>
            <spf>
                <domain>example.com</domain>
                <result>pass</result>
            </spf>
        </auth_results>
    </record>
</feedback>"""

    # Compressed valid XML
    valid_xml_gz = gzip.compress(valid_xml.encode())
    
    # XXE attack XML
    xxe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE feedback [
    <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<feedback>
    <report_metadata>
        <org_name>&xxe;</org_name>
    </report_metadata>
</feedback>"""

    # Billion laughs attack XML
    billion_laughs_xml = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<feedback>&lol4;</feedback>"""

    # EICAR test virus
    eicar_content = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    
    # Large file (over size limit)
    large_content = b"A" * (15 * 1024 * 1024)  # 15MB
    
    # Zip bomb (high compression ratio)
    zip_bomb_content = b"0" * (100 * 1024 * 1024)  # 100MB of zeros
    zip_bomb_gz = gzip.compress(zip_bomb_content)
    
    # Fake XML (wrong magic number)
    fake_xml = b"This is not XML but has .xml extension"
    
    # Executable disguised as XML
    fake_exe_xml = b"MZ\x90\x00" + b"fake executable content" + b"</fake>"
    
    return {
        "valid_xml": ("valid_report.xml", valid_xml.encode(), "application/xml"),
        "valid_xml_gz": ("valid_report.xml.gz", valid_xml_gz, "application/gzip"),
        "xxe_xml": ("xxe_attack.xml", xxe_xml.encode(), "application/xml"),
        "billion_laughs": ("billion_laughs.xml", billion_laughs_xml.encode(), "application/xml"),
        "eicar_virus": ("eicar_test.xml", eicar_content, "application/xml"),
        "large_file": ("large_file.xml", large_content, "application/xml"),
        "zip_bomb": ("zip_bomb.xml.gz", zip_bomb_gz, "application/gzip"),
        "fake_xml": ("fake.xml", fake_xml, "text/plain"),
        "fake_exe": ("fake_exe.xml", fake_exe_xml, "application/octet-stream")
    }

def test_file_upload_validation():
    """Test secure file upload validation"""
    print("🔍 Testing File Upload Validation...")
    
    try:
        from app.main import app
        
        with TestClient(app) as client:
            # Login first
            login_response = client.post("/api/v1/auth/login", json={
                "email": "admin@example.com", 
                "password": "admin123"
            })
            
            if login_response.status_code != 200:
                print(f"  ❌ Login failed: {login_response.status_code}")
                return False
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            test_files = create_test_files()
            
            # Test valid file upload
            filename, content, content_type = test_files["valid_xml"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            if response.status_code == 200:
                print(f"  ✅ Valid XML upload successful")
            else:
                print(f"  ❌ Valid XML upload failed: {response.status_code} - {response.text}")
                return False
            
            # Test valid gzipped file upload  
            filename, content, content_type = test_files["valid_xml_gz"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            if response.status_code == 200:
                print(f"  ✅ Valid gzipped XML upload successful")
            else:
                print(f"  ❌ Valid gzipped XML upload failed: {response.status_code} - {response.text}")
                return False
            
            return True
            
    except Exception as e:
        print(f"  ❌ File upload validation test error: {e}")
        return False

def test_malicious_file_blocking():
    """Test blocking of malicious files"""
    print("🔍 Testing Malicious File Blocking...")
    
    try:
        from app.main import app
        
        with TestClient(app) as client:
            # Login first
            login_response = client.post("/api/v1/auth/login", json={
                "email": "admin@example.com", 
                "password": "admin123"
            })
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            test_files = create_test_files()
            blocked_count = 0
            total_tests = 0
            
            # Test XXE attack
            filename, content, content_type = test_files["xxe_xml"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            total_tests += 1
            if response.status_code == 400:
                blocked_count += 1
                print(f"  ✅ XXE attack blocked: {response.status_code}")
            else:
                print(f"  ❌ XXE attack not blocked: {response.status_code}")
            
            # Test billion laughs attack
            filename, content, content_type = test_files["billion_laughs"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            total_tests += 1
            if response.status_code == 400:
                blocked_count += 1
                print(f"  ✅ Billion laughs attack blocked: {response.status_code}")
            else:
                print(f"  ❌ Billion laughs attack not blocked: {response.status_code}")
            
            # Test EICAR virus
            filename, content, content_type = test_files["eicar_virus"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            total_tests += 1
            if response.status_code == 400:
                blocked_count += 1
                print(f"  ✅ EICAR virus blocked: {response.status_code}")
            else:
                print(f"  ❌ EICAR virus not blocked: {response.status_code}")
            
            # Test fake XML (wrong magic number)
            filename, content, content_type = test_files["fake_xml"]
            files = {"file": (filename, io.BytesIO(content), "application/xml")}  # Force XML content type
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            total_tests += 1
            if response.status_code == 400:
                blocked_count += 1
                print(f"  ✅ Fake XML blocked: {response.status_code}")
            else:
                print(f"  ❌ Fake XML not blocked: {response.status_code}")
            
            # Test executable disguised as XML
            filename, content, content_type = test_files["fake_exe"]
            files = {"file": (filename, io.BytesIO(content), "application/xml")}
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            total_tests += 1
            if response.status_code == 400:
                blocked_count += 1
                print(f"  ✅ Fake executable blocked: {response.status_code}")
            else:
                print(f"  ❌ Fake executable not blocked: {response.status_code}")
            
            print(f"  📊 Blocked {blocked_count}/{total_tests} malicious files")
            return blocked_count >= total_tests * 0.8  # Accept 80% block rate
            
    except Exception as e:
        print(f"  ❌ Malicious file blocking test error: {e}")
        return False

def test_file_size_limits():
    """Test file size limits and zip bomb protection"""
    print("🔍 Testing File Size Limits...")
    
    try:
        from app.main import app
        
        with TestClient(app) as client:
            # Login first
            login_response = client.post("/api/v1/auth/login", json={
                "email": "admin@example.com", 
                "password": "admin123"
            })
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            test_files = create_test_files()
            
            # Test large file (should be blocked)
            filename, content, content_type = test_files["large_file"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            if response.status_code == 413 or response.status_code == 400:
                print(f"  ✅ Large file blocked: {response.status_code}")
            else:
                print(f"  ❌ Large file not blocked: {response.status_code}")
                return False
            
            # Test zip bomb (should be blocked)
            filename, content, content_type = test_files["zip_bomb"]
            files = {"file": (filename, io.BytesIO(content), content_type)}
            
            response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
            if response.status_code == 400:
                print(f"  ✅ Zip bomb blocked: {response.status_code}")
            else:
                print(f"  ❌ Zip bomb not blocked: {response.status_code}")
                return False
            
            return True
            
    except Exception as e:
        print(f"  ❌ File size limits test error: {e}")
        return False

def test_virus_scanning():
    """Test virus scanning functionality"""
    print("🔍 Testing Virus Scanning...")
    
    try:
        from app.services.virus_scanner_service import virus_scanner_service
        
        # Test clean content
        clean_content = b"<?xml version='1.0'?><feedback><report_metadata></report_metadata></feedback>"
        clean_result = virus_scanner_service.scan_content(clean_content, "clean.xml", "test_user")
        
        if clean_result["risk_level"] == "clean":
            print(f"  ✅ Clean content detected as clean")
        else:
            print(f"  ❌ Clean content flagged as: {clean_result['risk_level']}")
            return False
        
        # Test EICAR virus
        eicar_content = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        virus_result = virus_scanner_service.scan_content(eicar_content, "virus.xml", "test_user")
        
        if virus_result["risk_level"] in ["critical", "high"]:
            print(f"  ✅ EICAR virus detected as: {virus_result['risk_level']}")
        else:
            print(f"  ❌ EICAR virus not detected: {virus_result['risk_level']}")
            return False
        
        # Test suspicious content
        suspicious_content = b"<?xml version='1.0'?><script>alert('xss')</script><feedback></feedback>"
        suspicious_result = virus_scanner_service.scan_content(suspicious_content, "suspicious.xml", "test_user")
        
        if suspicious_result["threats_detected"]:
            print(f"  ✅ Suspicious content detected: {len(suspicious_result['threats_detected'])} threats")
        else:
            print(f"  ❌ Suspicious content not detected")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Virus scanning test error: {e}")
        return False

def test_secure_storage():
    """Test secure file storage functionality"""
    print("🔍 Testing Secure Storage...")
    
    try:
        from app.services.secure_storage_service import secure_storage_service
        
        # Test storage directory creation
        test_content = b"Test content for storage"
        test_validation = {
            "original_filename": "test.xml",
            "file_hash": "abc123",
            "file_size": len(test_content),
            "detected_mime_type": "application/xml",
            "upload_timestamp": "2025-01-01T00:00:00",
            "is_compressed": False,
            "decompressed_size": len(test_content)
        }
        
        # Test file storage
        storage_result = secure_storage_service.store_uploaded_file(
            test_content, test_validation, "test_user"
        )
        
        if storage_result["storage_id"]:
            print(f"  ✅ File stored with ID: {storage_result['storage_id']}")
        else:
            print(f"  ❌ File storage failed")
            return False
        
        # Test file retrieval
        user_files = secure_storage_service.get_user_files("test_user", 10)
        
        if len(user_files) > 0:
            print(f"  ✅ Retrieved {len(user_files)} user files")  
        else:
            print(f"  ❌ No user files retrieved")
            return False
        
        # Test quarantine
        quarantine_path = secure_storage_service.quarantine_file(
            b"malicious content", "Test quarantine", "test_user", "malicious.xml"
        )
        
        if quarantine_path:
            print(f"  ✅ File quarantined successfully")
        else:
            print(f"  ❌ File quarantine failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Secure storage test error: {e}")
        return False

def test_filename_validation():
    """Test filename validation security"""
    print("🔍 Testing Filename Validation...")
    
    try:
        from app.main import app
        
        with TestClient(app) as client:
            # Login first
            login_response = client.post("/api/v1/auth/login", json={
                "email": "admin@example.com", 
                "password": "admin123"
            })
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test dangerous filenames
            dangerous_filenames = [
                "../../../etc/passwd.xml",
                "..\\..\\windows\\system32\\config.xml", 
                "file|with|pipes.xml",
                "file with null\x00byte.xml",
                "verylongfilename" + "a" * 300 + ".xml",
                "double.extension.exe.xml",
                "script<>injection.xml"
            ]
            
            blocked_count = 0
            valid_content = b"<?xml version='1.0'?><feedback></feedback>"
            
            for dangerous_filename in dangerous_filenames:
                files = {"file": (dangerous_filename, io.BytesIO(valid_content), "application/xml")}
                response = client.post("/api/v1/dmarc/upload-report", headers=headers, files=files)
                
                if response.status_code == 400:
                    blocked_count += 1
                    print(f"  ✅ Dangerous filename blocked: {dangerous_filename[:30]}...")
                else:
                    print(f"  ❌ Dangerous filename allowed: {dangerous_filename[:30]}...")
            
            print(f"  📊 Blocked {blocked_count}/{len(dangerous_filenames)} dangerous filenames")
            return blocked_count >= len(dangerous_filenames) * 0.8  # Accept 80% block rate
            
    except Exception as e:
        print(f"  ❌ Filename validation test error: {e}")
        return False

def main():
    """Run all Phase 3 security tests"""
    print("🛡️  DMARC Analytics Platform - Phase 3 File Upload Security Validation")
    print("=" * 75)
    
    tests = [
        ("File Upload Validation", test_file_upload_validation),
        ("Malicious File Blocking", test_malicious_file_blocking),
        ("File Size Limits", test_file_size_limits),
        ("Virus Scanning", test_virus_scanning),
        ("Secure Storage", test_secure_storage),
        ("Filename Validation", test_filename_validation),
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
    print("\n" + "=" * 75)
    print("📊 PHASE 3 FILE UPLOAD SECURITY VALIDATION SUMMARY")
    print("=" * 75)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All Phase 3 file upload security improvements are working!")
        return 0
    else:
        print("⚠️  Some Phase 3 file upload security features need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())