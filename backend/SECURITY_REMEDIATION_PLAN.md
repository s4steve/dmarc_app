# 🛡️ Security Remediation Plan - DMARC Analytics Platform

**Date**: July 29, 2025  
**Plan Version**: 1.0  
**Scope**: Fix all security vulnerabilities except hardcoded credentials  

---

## 📋 **Executive Summary**

This plan addresses **14 critical and high-severity vulnerabilities** identified in the security analysis. The remediation is structured in phases based on risk priority and implementation complexity.

**Timeline**: 3-4 weeks  
**Resources Required**: 2-3 developers, 1 security reviewer  
**Testing**: Each fix includes validation tests and security verification  

---

## 🎯 **Phase 1: Critical Infrastructure Security (Week 1)**

### 🔴 **Priority 1.1: Enable Elasticsearch Security**
**Issue**: Elasticsearch security completely disabled  
**Risk**: Unauthorized database access  

#### Implementation Steps:
1. **Update Docker Compose Configuration**
   ```yaml
   # File: docker-compose.yml
   elasticsearch:
     environment:
       - xpack.security.enabled=true
       - ELASTIC_PASSWORD=strong_generated_password
       - discovery.type=single-node
       - xpack.security.enrollment.enabled=true
   ```

2. **Create Elasticsearch User Management**
   ```bash
   # Generate certificates
   docker exec es01 /usr/share/elasticsearch/bin/elasticsearch-certutil ca
   docker exec es01 /usr/share/elasticsearch/bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12
   ```

3. **Update Backend Configuration**
   ```python
   # File: app/core/config.py
   ELASTICSEARCH_USERNAME: str = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
   ELASTICSEARCH_PASSWORD: str = os.getenv("ELASTICSEARCH_PASSWORD")
   ELASTICSEARCH_USE_SSL: bool = os.getenv("ELASTICSEARCH_USE_SSL", "true").lower() == "true"
   ```

4. **Update Elasticsearch Service**
   ```python
   # File: app/services/elasticsearch.py
   def __init__(self):
       self.client = Elasticsearch(
           [settings.ELASTICSEARCH_URL],
           basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
           verify_certs=settings.ELASTICSEARCH_USE_SSL,
           ssl_show_warn=False
       )
   ```

**Validation**: Test database connectivity with authentication enabled  
**Timeline**: 2 days  

### 🔴 **Priority 1.2: Implement Input Sanitization**
**Issue**: NoSQL injection in Elasticsearch queries  
**Risk**: Data exfiltration, query manipulation  

#### Implementation Steps:
1. **Create Input Sanitization Utility**
   ```python
   # File: app/utils/sanitizer.py
   import re
   from typing import Any, Optional
   
   class InputSanitizer:
       @staticmethod
       def sanitize_domain(domain: Optional[str]) -> Optional[str]:
           """Sanitize domain input for Elasticsearch queries"""
           if not domain:
               return None
           
           # Remove potentially dangerous characters
           sanitized = re.sub(r'[^\w\.-]', '', domain.lower().strip())
           
           # Validate domain format
           domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
           if not re.match(domain_pattern, sanitized):
               raise ValueError("Invalid domain format")
           
           return sanitized
       
       @staticmethod
       def validate_integer_range(value: Any, min_val: int, max_val: int, default: int) -> int:
           """Validate and sanitize integer inputs"""
           try:
               int_val = int(value)
               if int_val < min_val or int_val > max_val:
                   return default
               return int_val
           except (ValueError, TypeError):
               return default
   ```

2. **Update DMARC Service with Sanitization**
   ```python
   # File: app/services/dmarc_service.py
   from ..utils.sanitizer import InputSanitizer
   
   def get_reports_summary(self, customer_id: str, days: int = 7, domain: Optional[str] = None) -> DMARCReportSummary:
       # Sanitize inputs
       days = InputSanitizer.validate_integer_range(days, 1, 365, 7)
       domain = InputSanitizer.sanitize_domain(domain) if domain else None
       
       # Build safe query conditions
       must_conditions = [
           {"term": {"customer_id.keyword": customer_id}},  # Use .keyword for exact match
           {"range": {
               "metadata.date_range_begin": {
                   "gte": start_date.isoformat(),
                   "lte": end_date.isoformat()
               }
           }}
       ]
       
       if domain:
           must_conditions.append({"term": {"policy.domain.keyword": domain}})
   ```

3. **Update API Endpoints**
   ```python
   # File: app/api/dmarc.py
   from ..utils.sanitizer import InputSanitizer
   
   @router.get("/summary", response_model=DMARCReportSummary)
   async def get_dmarc_summary(
       days: int = Query(7, ge=1, le=365),
       domain: str = Query(None, description="Filter by domain"),
       current_user: User = Depends(get_current_active_user)
   ):
       try:
           # Sanitize domain input
           sanitized_domain = InputSanitizer.sanitize_domain(domain) if domain else None
           summary = dmarc_service.get_reports_summary(current_user.customer_id, days, sanitized_domain)
           return summary
       except ValueError as e:
           raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
   ```

**Validation**: Test with malicious payloads to ensure they're blocked  
**Timeline**: 3 days  

---

## 🎯 **Phase 2: Authentication & Session Security (Week 1-2)**

### 🔴 **Priority 2.1: Implement Rate Limiting**
**Issue**: No brute force protection  
**Risk**: Account compromise, DoS attacks  

#### Implementation Steps:
1. **Install Rate Limiting Dependency**
   ```bash
   pip install slowapi
   ```

2. **Create Rate Limiting Middleware**
   ```python
   # File: app/middleware/rate_limiter.py
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   from fastapi import Request, HTTPException
   from fastapi.responses import JSONResponse
   import redis
   
   # Create limiter with Redis backend for distributed rate limiting
   limiter = Limiter(
       key_func=get_remote_address,
       storage_uri="redis://localhost:6379",
       default_limits=["100/hour"]
   )
   
   async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
       return JSONResponse(
           status_code=429,
           content={
               "detail": "Rate limit exceeded. Please try again later.",
               "retry_after": exc.retry_after
           }
       )
   ```

3. **Apply Rate Limiting to Authentication**
   ```python
   # File: app/api/auth.py
   from ..middleware.rate_limiter import limiter
   
   @router.post("/login")
   @limiter.limit("5/minute")  # 5 login attempts per minute per IP
   async def login(
       request: Request,
       user_credentials: UserLogin
   ):
       # Existing login logic
   ```

4. **Update Main Application**
   ```python
   # File: app/main.py
   from slowapi import Limiter
   from .middleware.rate_limiter import limiter, rate_limit_handler
   
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
   ```

**Validation**: Test that excessive requests are blocked  
**Timeline**: 2 days  

### 🔴 **Priority 2.2: Implement Secure Session Management**
**Issue**: No token blacklisting, unlimited concurrent sessions  
**Risk**: Session hijacking, unauthorized access  

#### Implementation Steps:
1. **Create Token Management Service**
   ```python
   # File: app/services/token_service.py
   import redis
   from datetime import datetime, timedelta
   from typing import Optional, Set
   from ..core.config import settings
   
   class TokenService:
       def __init__(self):
           self.redis_client = redis.Redis(
               host=settings.REDIS_HOST,
               port=settings.REDIS_PORT,
               decode_responses=True
           )
       
       def blacklist_token(self, token: str, expires_at: datetime):
           """Add token to blacklist"""
           ttl = int((expires_at - datetime.utcnow()).total_seconds())
           if ttl > 0:
               self.redis_client.setex(f"blacklisted:{token}", ttl, "1")
       
       def is_token_blacklisted(self, token: str) -> bool:
           """Check if token is blacklisted"""
           return self.redis_client.exists(f"blacklisted:{token}") > 0
       
       def get_active_sessions(self, user_id: str) -> Set[str]:
           """Get active sessions for user"""
           return self.redis_client.smembers(f"sessions:{user_id}")
       
       def add_session(self, user_id: str, token: str):
           """Add session to active sessions"""
           self.redis_client.sadd(f"sessions:{user_id}", token)
           self.redis_client.expire(f"sessions:{user_id}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
       
       def remove_session(self, user_id: str, token: str):
           """Remove session from active sessions"""
           self.redis_client.srem(f"sessions:{user_id}", token)
       
       def limit_concurrent_sessions(self, user_id: str, max_sessions: int = 3):
           """Limit concurrent sessions per user"""
           sessions = self.get_active_sessions(user_id)
           if len(sessions) >= max_sessions:
               # Remove oldest session
               oldest_token = sessions.pop()
               self.blacklist_token(oldest_token, datetime.utcnow() + timedelta(hours=1))
               self.remove_session(user_id, oldest_token)
   
   token_service = TokenService()
   ```

2. **Update Authentication to Use Token Service**
   ```python
   # File: app/api/auth.py
   from ..services.token_service import token_service
   
   @router.post("/login")
   async def login(user_credentials: UserLogin):
       # Existing authentication logic
       
       # Limit concurrent sessions
       token_service.limit_concurrent_sessions(user.id, max_sessions=3)
       
       # Create token
       access_token = create_access_token(data={"sub": user.email})
       
       # Add to active sessions
       token_service.add_session(user.id, access_token)
       
       return {"access_token": access_token, "token_type": "bearer"}
   
   @router.post("/logout")
   async def logout(
       request: Request,
       current_user: User = Depends(get_current_active_user)
   ):
       # Extract token from request
       token = request.headers.get("authorization", "").replace("Bearer ", "")
       
       # Blacklist token
       token_service.blacklist_token(token, datetime.utcnow() + timedelta(hours=1))
       
       # Remove from active sessions
       token_service.remove_session(current_user.id, token)
       
       return {"message": "Successfully logged out"}
   ```

3. **Update Token Verification**
   ```python
   # File: app/api/auth.py
   def get_current_user(token: str = Depends(oauth2_scheme)):
       # Check if token is blacklisted
       if token_service.is_token_blacklisted(token):
           raise HTTPException(
               status_code=401,
               detail="Token has been revoked"
           )
       
       # Existing token verification logic
   ```

**Validation**: Test logout functionality and concurrent session limits  
**Timeline**: 3 days  

---

## 🎯 **Phase 3: Secure Error Handling & Headers (Week 2)**

### 🔴 **Priority 3.1: Implement Security Headers**
**Issue**: Missing all critical security headers  
**Risk**: XSS, clickjacking, MIME sniffing attacks  

#### Implementation Steps:
1. **Create Security Headers Middleware**
   ```python
   # File: app/middleware/security_headers.py
   from fastapi import Request, Response
   from starlette.middleware.base import BaseHTTPMiddleware
   
   class SecurityHeadersMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           response: Response = await call_next(request)
           
           # Security headers
           response.headers["X-Content-Type-Options"] = "nosniff"
           response.headers["X-Frame-Options"] = "DENY"
           response.headers["X-XSS-Protection"] = "1; mode=block"
           response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
           response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
           response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
           
           # Content Security Policy
           csp = (
               "default-src 'self'; "
               "script-src 'self' 'unsafe-inline'; "
               "style-src 'self' 'unsafe-inline'; "
               "img-src 'self' data: https:; "
               "font-src 'self' https:; "
               "connect-src 'self'; "
               "frame-ancestors 'none';"
           )
           response.headers["Content-Security-Policy"] = csp
           
           return response
   ```

2. **Add Middleware to Application**
   ```python
   # File: app/main.py
   from .middleware.security_headers import SecurityHeadersMiddleware
   
   app.add_middleware(SecurityHeadersMiddleware)
   ```

**Validation**: Verify all security headers are present in responses  
**Timeline**: 1 day  

### 🔴 **Priority 3.2: Sanitize Error Messages**
**Issue**: Verbose error messages expose system information  
**Risk**: Information disclosure, system reconnaissance  

#### Implementation Steps:
1. **Create Error Handler Service**
   ```python
   # File: app/services/error_handler.py
   import logging
   from typing import Dict, Any
   from fastapi import HTTPException
   
   logger = logging.getLogger(__name__)
   
   class SecureErrorHandler:
       @staticmethod
       def handle_database_error(e: Exception, context: str = "") -> HTTPException:
           """Handle database errors without exposing details"""
           logger.error(f"Database error in {context}: {str(e)}")
           return HTTPException(
               status_code=500,
               detail="A database error occurred. Please try again later."
           )
       
       @staticmethod
       def handle_validation_error(e: Exception, context: str = "") -> HTTPException:
           """Handle validation errors safely"""
           logger.warning(f"Validation error in {context}: {str(e)}")
           return HTTPException(
               status_code=400,
               detail="Invalid input provided. Please check your data and try again."
           )
       
       @staticmethod
       def handle_file_processing_error(e: Exception, context: str = "") -> HTTPException:
           """Handle file processing errors securely"""
           logger.error(f"File processing error in {context}: {str(e)}")
           return HTTPException(
               status_code=400,
               detail="Unable to process the uploaded file. Please ensure it's a valid DMARC report."
           )
       
       @staticmethod
       def handle_authentication_error(e: Exception, context: str = "") -> HTTPException:
           """Handle authentication errors"""
           logger.warning(f"Authentication error in {context}: {str(e)}")
           return HTTPException(
               status_code=401,
               detail="Authentication failed. Please check your credentials."
           )
   ```

2. **Update API Endpoints with Secure Error Handling**
   ```python
   # File: app/api/dmarc.py
   from ..services.error_handler import SecureErrorHandler
   
   @router.post("/upload-report")
   async def upload_dmarc_report(
       file: UploadFile = File(...),
       current_user: User = Depends(get_current_active_user)
   ):
       try:
           # Existing file processing logic
           report_id = dmarc_service.ingest_report(xml_string, current_user.customer_id)
           return {"message": "DMARC report uploaded successfully", "report_id": report_id}
       
       except ValueError as e:
           raise SecureErrorHandler.handle_validation_error(e, "upload_report")
       except Exception as e:
           raise SecureErrorHandler.handle_file_processing_error(e, "upload_report")
   ```

3. **Add Global Exception Handler**
   ```python
   # File: app/main.py
   from fastapi.exceptions import RequestValidationError
   from starlette.exceptions import HTTPException as StarletteHTTPException
   
   @app.exception_handler(StarletteHTTPException)
   async def http_exception_handler(request, exc):
       logger.error(f"HTTP error: {exc.detail}")
       return JSONResponse(
           status_code=exc.status_code,
           content={"detail": "An error occurred while processing your request."}
       )
   
   @app.exception_handler(RequestValidationError)
   async def validation_exception_handler(request, exc):
       logger.error(f"Validation error: {exc}")
       return JSONResponse(
           status_code=422,
           content={"detail": "Invalid request data provided."}
       )
   ```

**Validation**: Test that detailed error information is not exposed  
**Timeline**: 2 days  

---

## 🎯 **Phase 4: File Upload Security (Week 2-3)**

### 🔴 **Priority 4.1: Implement File Upload Security**
**Issue**: No size limits, basic validation only  
**Risk**: DoS attacks, malicious file uploads  

#### Implementation Steps:
1. **Create File Validation Service**
   ```python
   # File: app/services/file_validator.py
   import magic
   from typing import BinaryIO, Tuple
   from fastapi import HTTPException, UploadFile
   
   class FileValidator:
       MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
       MAX_DECOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB
       ALLOWED_MIME_TYPES = ['text/xml', 'application/xml', 'application/gzip']
       
       @staticmethod
       def validate_file_size(file: UploadFile) -> None:
           """Validate file size"""
           file.file.seek(0, 2)  # Seek to end
           file_size = file.file.tell()
           file.file.seek(0)  # Reset to beginning
           
           if file_size > FileValidator.MAX_FILE_SIZE:
               raise HTTPException(
                   status_code=413,
                   detail=f"File too large. Maximum size is {FileValidator.MAX_FILE_SIZE // (1024*1024)}MB"
               )
       
       @staticmethod
       def validate_file_type(file_content: bytes, filename: str) -> None:
           """Validate file type using magic numbers"""
           mime_type = magic.from_buffer(file_content, mime=True)
           
           if mime_type not in FileValidator.ALLOWED_MIME_TYPES:
               raise HTTPException(
                   status_code=400,
                   detail="Invalid file type. Only XML and GZIP files are allowed."
               )
       
       @staticmethod
       def safe_decompress(compressed_data: bytes) -> bytes:
           """Safely decompress gzip data with size limits"""
           import gzip
           import io
           
           decompressed_size = 0
           decompressed_data = io.BytesIO()
           
           with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
               while True:
                   chunk = gz.read(8192)
                   if not chunk:
                       break
                   
                   decompressed_size += len(chunk)
                   if decompressed_size > FileValidator.MAX_DECOMPRESSED_SIZE:
                       raise HTTPException(
                           status_code=413,
                           detail="Decompressed file too large"
                       )
                   
                   decompressed_data.write(chunk)
           
           return decompressed_data.getvalue()
       
       @staticmethod
       def scan_for_malicious_content(xml_content: str) -> None:
           """Scan XML for potentially malicious content"""
           dangerous_patterns = [
               '<!ENTITY',  # External entities
               'SYSTEM ',   # System entities
               'PUBLIC ',   # Public entities
               '<!DOCTYPE', # DOCTYPE declarations
               'javascript:', # JavaScript URIs
               'data:',     # Data URIs
           ]
           
           xml_upper = xml_content.upper()
           for pattern in dangerous_patterns:
               if pattern.upper() in xml_upper:
                   raise HTTPException(
                       status_code=400,
                       detail="File contains potentially malicious content"
                   )
   ```

2. **Update File Upload Endpoint**
   ```python
   # File: app/api/dmarc.py
   from ..services.file_validator import FileValidator
   
   @router.post("/upload-report")
   async def upload_dmarc_report(
       file: UploadFile = File(...),
       current_user: User = Depends(get_current_active_user)
   ):
       try:
           # Validate file size
           FileValidator.validate_file_size(file)
           
           # Read file content
           file_content = await file.read()
           
           # Validate file type
           FileValidator.validate_file_type(file_content, file.filename)
           
           # Process based on file type
           if file.filename.endswith('.gz'):
               xml_content = FileValidator.safe_decompress(file_content).decode('utf-8')
           else:
               xml_content = file_content.decode('utf-8')
           
           # Scan for malicious content
           FileValidator.scan_for_malicious_content(xml_content)
           
           # Process the file
           report_id = dmarc_service.ingest_report(xml_content, current_user.customer_id)
           
           return {
               "message": "DMARC report uploaded successfully",
               "report_id": report_id
           }
           
       except HTTPException:
           raise
       except Exception as e:
           raise SecureErrorHandler.handle_file_processing_error(e, "upload_report")
   ```

**Validation**: Test file size limits and malicious content detection  
**Timeline**: 3 days  

---

## 🎯 **Phase 5: XML Security & Dependencies (Week 3)**

### 🔴 **Priority 5.1: Secure XML Processing**
**Issue**: XXE vulnerability in XML parsing  
**Risk**: File system access, denial of service  

#### Implementation Steps:
1. **Create Secure XML Parser**
   ```python
   # File: app/services/secure_xml_parser.py
   import xml.etree.ElementTree as ET
   from xml.parsers.expat import ParserCreate
   from typing import Dict, Any
   from fastapi import HTTPException
   
   class SecureXMLParser:
       @staticmethod
       def parse_xml_safely(xml_content: str) -> Dict[str, Any]:
           """Parse XML with security restrictions"""
           
           # Create parser with security restrictions
           parser = ParserCreate()
           
           # Disable external entity processing
           parser.DefaultHandler = lambda data: None
           parser.ExternalEntityRefHandler = lambda context, base, sysId, notationName: False
           parser.EntityDeclHandler = lambda entityName, is_parameter_entity, value, base, systemId, publicId, notationName: False
           
           try:
               # Parse XML with restricted parser
               root = ET.fromstring(xml_content, parser=None)  # Use default parser initially
               
               # Convert to dictionary safely
               return SecureXMLParser._xml_to_dict(root)
               
           except ET.ParseError as e:
               raise HTTPException(
                   status_code=400,
                   detail="Invalid XML format"
               )
           except Exception as e:
               raise HTTPException(
                   status_code=400,
                   detail="XML processing error"
               )
       
       @staticmethod
       def _xml_to_dict(element) -> Dict[str, Any]:
           """Convert XML element to dictionary safely"""
           result = {}
           
           # Add attributes
           if element.attrib:
               result.update(element.attrib)
           
           # Add text content
           if element.text and element.text.strip():
               if len(result) == 0:
                   return element.text.strip()
               else:
                   result['_text'] = element.text.strip()
           
           # Add child elements
           for child in element:
               child_data = SecureXMLParser._xml_to_dict(child)
               if child.tag in result:
                   if not isinstance(result[child.tag], list):
                       result[child.tag] = [result[child.tag]]
                   result[child.tag].append(child_data)
               else:
                   result[child.tag] = child_data
           
           return result
   ```

2. **Update DMARC Parser**
   ```python
   # File: app/services/dmarc_parser.py
   from .secure_xml_parser import SecureXMLParser
   
   class DMARCParser:
       def parse_xml_report(self, xml_content: str, customer_id: str) -> DMARCReport:
           try:
               # Use secure XML parser instead of xmltodict
               data = SecureXMLParser.parse_xml_safely(xml_content)
               
               # Parse the feedback element
               feedback = data.get('feedback', data)
               
               # Extract report metadata
               metadata_data = feedback.get('report_metadata', {})
               metadata = DMARCReportMetadata(
                   org_name=metadata_data.get('org_name'),
                   email=metadata_data.get('email'),
                   report_id=metadata_data.get('report_id'),
                   date_range_begin=datetime.fromtimestamp(int(metadata_data.get('date_range', {}).get('begin', 0))),
                   date_range_end=datetime.fromtimestamp(int(metadata_data.get('date_range', {}).get('end', 0)))
               )
               
               # Continue with existing parsing logic...
               
           except Exception as e:
               raise ValueError(f"Failed to parse DMARC report: {str(e)}")
   ```

**Validation**: Test XXE payloads are blocked  
**Timeline**: 2 days  

### 🔴 **Priority 5.2: Update Dependencies**
**Issue**: Multiple known CVEs in dependencies  
**Risk**: Remote code execution, security bypass  

#### Implementation Steps:
1. **Update Requirements File**
   ```python
   # File: requirements.txt
   fastapi>=0.104.0
   uvicorn[standard]>=0.24.0
   python-jose[cryptography]>=3.5.1  # Update to patched version
   python-multipart>=0.0.6
   passlib[bcrypt]>=1.7.4
   bcrypt>=4.1.0
   pydantic>=2.5.0
   pydantic-settings>=2.1.0
   elasticsearch>=8.11.0  # Major version update for security
   urllib3>=2.5.0  # Fix CVE-2025-50181, CVE-2025-50182
   cryptography>=41.0.0
   python-magic>=0.4.27
   redis>=5.0.0
   slowapi>=0.1.9
   ```

2. **Create Dependency Update Script**
   ```bash
   #!/bin/bash
   # File: scripts/update_dependencies.sh
   
   echo "Updating Python dependencies..."
   pip install --upgrade -r requirements.txt
   
   echo "Checking for security vulnerabilities..."
   safety check
   
   echo "Running tests to ensure compatibility..."
   python -m pytest tests/
   
   echo "Dependency update complete!"
   ```

3. **Add Dependency Security Scanning to CI**
   ```yaml
   # File: .github/workflows/security.yml
   name: Security Scan
   on: [push, pull_request]
   
   jobs:
     security:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.12'
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install safety
         - name: Run security scan
           run: safety check --json
   ```

**Validation**: Run safety check to confirm vulnerabilities are resolved  
**Timeline**: 1 day  

---

## 🎯 **Phase 6: Production Hardening (Week 3-4)**

### 🔴 **Priority 6.1: Docker Security Configuration**
**Issue**: Production mode disabled, security misconfigurations  
**Risk**: Information disclosure, container escape  

#### Implementation Steps:
1. **Update Docker Configuration**
   ```dockerfile
   # File: backend/Dockerfile
   FROM python:3.12-slim as builder
   
   # Create non-root user
   RUN groupadd -r appuser && useradd -r -g appuser appuser
   
   # Set working directory
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       libmagic1 \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy and install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir --user -r requirements.txt
   
   # Production stage
   FROM python:3.12-slim
   
   # Copy user from builder
   RUN groupadd -r appuser && useradd -r -g appuser appuser
   
   # Install runtime dependencies
   RUN apt-get update && apt-get install -y \
       libmagic1 \
       && rm -rf /var/lib/apt/lists/* \
       && apt-get clean
   
   # Copy Python packages from builder
   COPY --from=builder /root/.local /home/appuser/.local
   
   # Copy application code
   WORKDIR /app
   COPY --chown=appuser:appuser . .
   
   # Switch to non-root user
   USER appuser
   
   # Add local Python packages to PATH
   ENV PATH=/home/appuser/.local/bin:$PATH
   
   # Expose port
   EXPOSE 8000
   
   # Run application (production mode, no reload)
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
   ```

2. **Update Docker Compose Security**
   ```yaml
   # File: docker-compose.yml
   version: '3.8'
   
   services:
     elasticsearch:
       image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
       container_name: dmarc-elasticsearch
       environment:
         - discovery.type=single-node
         - xpack.security.enabled=true
         - ELASTIC_PASSWORD=${ELASTICSEARCH_PASSWORD:-strongpassword123}
         - xpack.security.http.ssl.enabled=false  # Internal network only
       volumes:
         - elasticsearch_data:/usr/share/elasticsearch/data
       networks:
         - dmarc-network
       security_opt:
         - no-new-privileges:true
       read_only: true
       tmpfs:
         - /tmp
   
     redis:
       image: redis:7-alpine
       container_name: dmarc-redis
       networks:
         - dmarc-network
       security_opt:
         - no-new-privileges:true
       read_only: true
       tmpfs:
         - /tmp
   
     api:
       build:
         context: ./backend
         dockerfile: Dockerfile
       container_name: dmarc-api
       environment:
         - ELASTICSEARCH_URL=http://elasticsearch:9200
         - ELASTICSEARCH_PASSWORD=${ELASTICSEARCH_PASSWORD:-strongpassword123}
         - REDIS_HOST=redis
         - SECRET_KEY=${SECRET_KEY}
       depends_on:
         - elasticsearch
         - redis
       networks:
         - dmarc-network
       security_opt:
         - no-new-privileges:true
       read_only: true
       tmpfs:
         - /tmp
   
     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile
       container_name: dmarc-frontend
       ports:
         - "3000:80"
       depends_on:
         - api
       networks:
         - dmarc-network
       security_opt:
         - no-new-privileges:true
       read_only: true
       tmpfs:
         - /tmp
   
   volumes:
     elasticsearch_data:
   
   networks:
     dmarc-network:
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16  # Isolated network
   ```

**Validation**: Test containers run with restricted privileges  
**Timeline**: 2 days  

### 🔴 **Priority 6.2: Monitoring & Logging**
**Issue**: No security monitoring or audit logging  
**Risk**: Undetected attacks, compliance issues  

#### Implementation Steps:
1. **Create Security Logging Service**
   ```python
   # File: app/services/security_logger.py
   import logging
   import json
   from datetime import datetime
   from typing import Dict, Any, Optional
   from fastapi import Request
   
   # Configure security logger
   security_logger = logging.getLogger('security')
   handler = logging.FileHandler('/var/log/dmarc/security.log')
   formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
   handler.setFormatter(formatter)
   security_logger.addHandler(handler)
   security_logger.setLevel(logging.INFO)
   
   class SecurityLogger:
       @staticmethod
       def log_authentication_attempt(
           request: Request,
           email: str,
           success: bool,
           reason: Optional[str] = None
       ):
           """Log authentication attempts"""
           event = {
               'event_type': 'authentication',
               'timestamp': datetime.utcnow().isoformat(),
               'ip_address': request.client.host,
               'user_agent': request.headers.get('user-agent'),
               'email': email,
               'success': success,
               'reason': reason
           }
           
           level = logging.INFO if success else logging.WARNING
           security_logger.log(level, json.dumps(event))
       
       @staticmethod
       def log_permission_denied(
           request: Request,
           user_id: str,
           resource: str,
           action: str
       ):
           """Log permission denied events"""
           event = {
               'event_type': 'permission_denied',
               'timestamp': datetime.utcnow().isoformat(),
               'ip_address': request.client.host,
               'user_id': user_id,
               'resource': resource,
               'action': action
           }
           
           security_logger.warning(json.dumps(event))
       
       @staticmethod
       def log_suspicious_activity(
           request: Request,
           activity_type: str,
           details: Dict[str, Any]
       ):
           """Log suspicious activities"""
           event = {
               'event_type': 'suspicious_activity',
               'timestamp': datetime.utcnow().isoformat(),
               'ip_address': request.client.host,
               'user_agent': request.headers.get('user-agent'),
               'activity_type': activity_type,
               'details': details
           }
           
           security_logger.error(json.dumps(event))
   ```

2. **Add Security Logging to Endpoints**
   ```python
   # File: app/api/auth.py
   from ..services.security_logger import SecurityLogger
   
   @router.post("/login")
   async def login(
       request: Request,
       user_credentials: UserLogin
   ):
       try:
           # Existing authentication logic
           
           # Log successful authentication
           SecurityLogger.log_authentication_attempt(
               request, user_credentials.email, True
           )
           
           return {"access_token": access_token, "token_type": "bearer"}
           
       except HTTPException as e:
           # Log failed authentication
           SecurityLogger.log_authentication_attempt(
               request, user_credentials.email, False, str(e.detail)
           )
           raise
   ```

**Validation**: Verify security events are logged properly  
**Timeline**: 2 days  

---

## 📊 **Implementation Timeline & Resources**

### **Week 1: Critical Infrastructure**
- **Days 1-2**: Enable Elasticsearch Security
- **Days 3-5**: Implement Input Sanitization & Rate Limiting

### **Week 2: Authentication & Error Handling**  
- **Days 1-3**: Secure Session Management
- **Days 4-5**: Security Headers & Error Sanitization

### **Week 3: File Security & Dependencies**
- **Days 1-3**: File Upload Security
- **Days 4-5**: Secure XML Processing & Dependency Updates

### **Week 4: Production Hardening**
- **Days 1-2**: Docker Security Configuration
- **Days 3-4**: Monitoring & Logging
- **Day 5**: Final Testing & Validation

---

## ✅ **Validation & Testing Plan**

### **Security Test Integration**
1. **Automated Testing**: Run existing security tests after each fix
2. **Penetration Testing**: Manual validation of critical fixes
3. **Code Review**: Security-focused review of all changes
4. **Performance Testing**: Ensure security additions don't impact performance

### **Acceptance Criteria**
- [ ] All critical vulnerabilities resolved
- [ ] Security tests pass (25/25)
- [ ] No new vulnerabilities introduced
- [ ] Performance impact < 10%
- [ ] Production deployment successful

---

## 🎯 **Success Metrics**

### **Before Remediation**
- Security Score: 🔴 2/10 (Critical Risk)
- Vulnerabilities: 15+ Critical/High
- Security Headers: 0/5
- Authentication: Hardcoded/Bypassed

### **After Remediation Target**
- Security Score: 🟢 8/10 (Low Risk)
- Vulnerabilities: 0 Critical, <2 Medium
- Security Headers: 5/5
- Authentication: Multi-layer Protection

---

This comprehensive plan addresses all identified security vulnerabilities (except hardcoded credentials) through systematic remediation, proper testing, and production hardening. Each phase builds upon the previous one to create a robust, secure application architecture.