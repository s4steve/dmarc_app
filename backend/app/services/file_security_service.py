"""
Secure File Upload and Processing Service
"""
import os
import gzip
import tempfile
import hashlib
import magic
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Tuple, BinaryIO
from pathlib import Path
from datetime import datetime
from fastapi import HTTPException, UploadFile
from ..core.config import settings
from ..utils.error_sanitizer import ErrorSanitizer
from .secure_storage_service import secure_storage_service
from .virus_scanner_service import virus_scanner_service
import logging

logger = logging.getLogger("security")

class FileSecurityService:
    """Service for secure file upload validation and processing"""
    
    # Configuration constants
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DECOMPRESSED_SIZE = 50 * 1024 * 1024  # 50MB after decompression
    MAX_XML_ENTITIES = 1000  # Limit XML entities to prevent XXE
    ALLOWED_EXTENSIONS = {'.xml', '.gz'}
    QUARANTINE_DIR = "/tmp/quarantine"
    SAFE_PROCESSING_DIR = "/tmp/dmarc_processing"
    
    # MIME types with magic number validation
    ALLOWED_MIME_TYPES = {
        'application/xml': [
            b'<?xml',  # XML header
            b'\xef\xbb\xbf<?xml',  # XML with BOM
        ],
        'application/gzip': [
            b'\x1f\x8b',  # Gzip magic number
        ],
        'text/xml': [
            b'<?xml',
            b'\xef\xbb\xbf<?xml',
        ]
    }
    
    def __init__(self):
        """Initialize the file security service"""
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist with proper permissions"""
        for directory in [self.QUARANTINE_DIR, self.SAFE_PROCESSING_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True, mode=0o700)
    
    def validate_upload(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Comprehensive file upload validation
        
        Args:
            file: Uploaded file object
            user_id: ID of the user uploading the file
            
        Returns:
            Dictionary with validation results and metadata
            
        Raises:
            HTTPException: If file validation fails
        """
        try:
            # Basic file information
            original_filename = file.filename or "unknown"
            file_size = 0
            
            # Log upload attempt
            logger.info(f"File upload attempt by user {user_id}: {original_filename}")
            
            # 1. Filename validation
            self._validate_filename(original_filename)
            
            # 2. Read file content for validation
            file_content = self._read_file_safely(file)
            file_size = len(file_content)
            
            # 3. File size validation
            self._validate_file_size(file_size, original_filename)
            
            # 4. Magic number validation
            detected_mime = self._validate_magic_numbers(file_content, original_filename)
            
            # 5. Content structure validation
            content_validation = self._validate_content_structure(file_content, original_filename)
            
            # 6. Generate file hash for tracking
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 7. Virus scanning
            virus_scan_result = virus_scanner_service.scan_content(file_content, original_filename, user_id)
            
            # Handle virus scan results
            if virus_scan_result["risk_level"] in ["critical", "high"]:
                # Quarantine high-risk files
                quarantine_path = secure_storage_service.quarantine_file(
                    file_content, 
                    f"Virus scan risk level: {virus_scan_result['risk_level']}", 
                    user_id, 
                    original_filename
                )
                
                risk_description = f"File blocked due to {virus_scan_result['risk_level']} risk level"
                if virus_scan_result["threats_detected"]:
                    threat_names = [t.get("name", "unknown") for t in virus_scan_result["threats_detected"]]
                    risk_description += f". Threats: {', '.join(threat_names[:3])}"
                
                raise ErrorSanitizer.create_http_exception(
                    400, risk_description, "validation"
                )
            
            # 8. Check for additional malicious patterns
            self._scan_malicious_patterns(file_content, original_filename)
            
            validation_result = {
                "status": "valid",
                "original_filename": original_filename,
                "file_size": file_size,
                "file_hash": file_hash,
                "detected_mime_type": detected_mime,
                "content_type": content_validation["type"],
                "is_compressed": content_validation["compressed"],
                "decompressed_size": content_validation.get("decompressed_size", file_size),
                "upload_timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "virus_scan_result": virus_scan_result
            }
            
            logger.info(f"File validation successful: {file_hash[:16]}...")
            return validation_result
            
        except HTTPException:
            # Re-raise HTTP exceptions (validation failures)
            raise
        except Exception as e:
            logger.error(f"File validation error for user {user_id}: {str(e)}")
            ErrorSanitizer.log_security_event(
                "file_validation_error",
                {"user_id": user_id, "filename": original_filename, "error": str(e)}
            )
            raise ErrorSanitizer.create_http_exception(
                500,
                "File validation failed due to server error",
                "file"
            )
    
    def _validate_filename(self, filename: str) -> None:
        """Validate filename for security issues"""
        if not filename:
            raise ErrorSanitizer.create_http_exception(
                400, "Filename is required", "validation"
            )
        
        # Check filename length
        if len(filename) > 255:
            raise ErrorSanitizer.create_http_exception(
                400, "Filename too long", "validation"
            )
        
        # Check for dangerous characters and patterns
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00', '\n', '\r', '\t']
        dangerous_patterns = [
            r'\.\.',  # Directory traversal
            r'[<>"|*?\\/:]+',  # Windows/Unix reserved characters
            r'[\x00-\x1f\x7f]',  # Control characters
            r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
        ]
        
        # Check individual characters
        if any(char in filename for char in dangerous_chars):
            ErrorSanitizer.log_security_event(
                "malicious_filename",
                {"filename": filename, "reason": "dangerous_characters"}
            )
            raise ErrorSanitizer.create_http_exception(
                400, "Filename contains invalid characters", "validation"
            )
        
        # Check patterns with regex
        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                ErrorSanitizer.log_security_event(
                    "malicious_filename",
                    {"filename": filename, "reason": f"dangerous_pattern: {pattern}"}
                )
                raise ErrorSanitizer.create_http_exception(
                    400, "Filename contains invalid patterns", "validation"
                )
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise ErrorSanitizer.create_http_exception(
                400, f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}", "validation"
            )
        
        # Check for double extensions (potential evasion)
        parts = filename.lower().split('.')
        if len(parts) > 3:  # filename.xml.gz is OK, but filename.exe.xml.gz is suspicious
            ErrorSanitizer.log_security_event(
                "suspicious_filename",
                {"filename": filename, "reason": "multiple_extensions"}
            )
            raise ErrorSanitizer.create_http_exception(
                400, "Suspicious filename structure", "validation"
            )
    
    def _read_file_safely(self, file: UploadFile) -> bytes:
        """Safely read file with size limits"""
        try:
            # Reset file pointer
            file.file.seek(0)
            
            # Read with size limit
            content = file.file.read(self.MAX_FILE_SIZE + 1)
            
            if len(content) > self.MAX_FILE_SIZE:
                raise ErrorSanitizer.create_http_exception(
                    413, f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB", "validation"
                )
            
            return content
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"File read error: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                400, "Unable to read uploaded file", "file"
            )
    
    def _validate_file_size(self, file_size: int, filename: str) -> None:
        """Validate file size constraints"""
        if file_size == 0:
            raise ErrorSanitizer.create_http_exception(
                400, "Empty file not allowed", "validation"
            )
        
        if file_size > self.MAX_FILE_SIZE:
            ErrorSanitizer.log_security_event(
                "oversized_file_upload",
                {"filename": filename, "size": file_size, "limit": self.MAX_FILE_SIZE}
            )
            raise ErrorSanitizer.create_http_exception(
                413, f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB", "validation"
            )
    
    def _validate_magic_numbers(self, content: bytes, filename: str) -> str:
        """Validate file content using magic numbers"""
        if len(content) < 4:
            raise ErrorSanitizer.create_http_exception(
                400, "File too small to validate", "validation"
            )
        
        try:
            # Use python-magic to detect MIME type
            detected_mime = magic.from_buffer(content, mime=True)
            
            # Check if detected MIME type is allowed
            if detected_mime not in self.ALLOWED_MIME_TYPES:
                ErrorSanitizer.log_security_event(
                    "invalid_file_type",
                    {
                        "filename": filename,
                        "detected_mime": detected_mime,
                        "expected": list(self.ALLOWED_MIME_TYPES.keys())
                    }
                )
                raise ErrorSanitizer.create_http_exception(
                    400, f"File type not allowed: {detected_mime}", "validation"
                )
            
            # Additional magic number validation
            file_header = content[:8]
            valid_header = False
            
            for magic_bytes in self.ALLOWED_MIME_TYPES[detected_mime]:
                if file_header.startswith(magic_bytes):
                    valid_header = True
                    break
            
            if not valid_header:
                ErrorSanitizer.log_security_event(
                    "invalid_magic_number",
                    {"filename": filename, "detected_mime": detected_mime, "header": file_header.hex()}
                )
                raise ErrorSanitizer.create_http_exception(
                    400, "File header validation failed", "validation"
                )
            
            return detected_mime
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Magic number validation error: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                400, "File type validation failed", "validation"
            )
    
    def _validate_content_structure(self, content: bytes, filename: str) -> Dict[str, Any]:
        """Validate file content structure and handle compression"""
        result = {
            "type": "unknown",
            "compressed": False,
            "valid": False
        }
        
        try:
            # Check if file is gzipped
            if content.startswith(b'\x1f\x8b'):
                result["compressed"] = True
                result["type"] = "gzip"
                
                # Safely decompress with size limits
                decompressed_content = self._safe_decompress(content, filename)
                result["decompressed_size"] = len(decompressed_content)
                
                # Validate decompressed XML
                self._validate_xml_content(decompressed_content, filename)
                result["valid"] = True
                
            elif content.startswith(b'<?xml') or content.startswith(b'\xef\xbb\xbf<?xml'):
                result["type"] = "xml"
                result["decompressed_size"] = len(content)
                
                # Validate XML directly
                self._validate_xml_content(content, filename)
                result["valid"] = True
                
            else:
                raise ErrorSanitizer.create_http_exception(
                    400, "Unrecognized file format", "validation"
                )
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Content validation error for {filename}: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                400, "File content validation failed", "validation"
            )
    
    def _safe_decompress(self, content: bytes, filename: str) -> bytes:
        """Safely decompress gzip content with bomb protection"""
        try:
            # Create a decompressor with size limits
            import io
            decompressor = gzip.GzipFile(fileobj=io.BytesIO(content))
            
            # Read in chunks to prevent memory exhaustion
            decompressed_chunks = []
            total_size = 0
            chunk_size = 64 * 1024  # 64KB chunks
            
            while True:
                chunk = decompressor.read(chunk_size)
                if not chunk:
                    break
                
                total_size += len(chunk)
                
                # Check for zip bomb (excessive decompression ratio)
                if total_size > self.MAX_DECOMPRESSED_SIZE:
                    ErrorSanitizer.log_security_event(
                        "gzip_bomb_detected",
                        {
                            "filename": filename,
                            "compressed_size": len(content),
                            "decompressed_size": total_size,
                            "ratio": total_size / len(content)
                        }
                    )
                    raise ErrorSanitizer.create_http_exception(
                        400, "File decompression ratio too high (potential zip bomb)", "validation"
                    )
                
                decompressed_chunks.append(chunk)
            
            decompressed_content = b''.join(decompressed_chunks)
            
            # Check compression ratio for additional zip bomb detection
            compression_ratio = len(decompressed_content) / len(content)
            if compression_ratio > 100:  # More than 100x compression is suspicious
                ErrorSanitizer.log_security_event(
                    "suspicious_compression_ratio",
                    {
                        "filename": filename,
                        "ratio": compression_ratio,
                        "compressed_size": len(content),
                        "decompressed_size": len(decompressed_content)
                    }
                )
                raise ErrorSanitizer.create_http_exception(
                    400, "Suspicious compression ratio detected", "validation"
                )
            
            return decompressed_content
            
        except gzip.BadGzipFile:
            raise ErrorSanitizer.create_http_exception(
                400, "Invalid gzip file format", "validation"
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Decompression error for {filename}: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                400, "File decompression failed", "validation"
            )
    
    def _validate_xml_content(self, content: bytes, filename: str) -> None:
        """Validate XML content for security issues"""
        try:
            # Convert to string safely
            try:
                xml_string = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    xml_string = content.decode('iso-8859-1')
                except UnicodeDecodeError:
                    raise ErrorSanitizer.create_http_exception(
                        400, "Invalid file encoding", "validation"
                    )
            
            # Check for XXE attack patterns
            xxe_patterns = [
                '<!ENTITY',
                '<!DOCTYPE',
                'SYSTEM',
                'PUBLIC',
                '&',
                'file://',
                'http://',
                'https://',
                'ftp://'
            ]
            
            xml_lower = xml_string.lower()
            suspicious_patterns = [pattern for pattern in xxe_patterns if pattern.lower() in xml_lower]
            
            if suspicious_patterns:
                ErrorSanitizer.log_security_event(
                    "xxe_attempt_detected",
                    {
                        "filename": filename,
                        "patterns": suspicious_patterns
                    }
                )
                raise ErrorSanitizer.create_http_exception(
                    400, "XML contains potentially dangerous content", "validation"
                )
            
            # Parse XML with security restrictions
            # Create parser that forbids DTD processing and entity expansion
            try:
                # Use defusedxml if available, otherwise basic ET with restrictions
                try:
                    import defusedxml.ElementTree as DefusedET
                    root = DefusedET.fromstring(xml_string)
                except ImportError:
                    # Fallback to standard ET with basic protections
                    root = ET.fromstring(xml_string)
            except ET.ParseError as e:
                raise ErrorSanitizer.create_http_exception(
                    400, "Invalid XML format", "validation"
                )
            
            # Check XML structure and size
            element_count = len(list(root.iter()))
            if element_count > 10000:  # Reasonable limit for DMARC reports
                ErrorSanitizer.log_security_event(
                    "oversized_xml",
                    {"filename": filename, "elements": element_count}
                )
                raise ErrorSanitizer.create_http_exception(
                    400, "XML file too complex", "validation"
                )
            
            # Basic DMARC report structure validation
            if root.tag != "feedback":
                raise ErrorSanitizer.create_http_exception(
                    400, "Invalid DMARC report structure", "validation"
                )
            
            # Check for required DMARC elements
            required_elements = ["report_metadata", "policy_published"]
            for required in required_elements:
                if root.find(required) is None:
                    raise ErrorSanitizer.create_http_exception(
                        400, f"Missing required DMARC element: {required}", "validation"
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"XML validation error for {filename}: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                400, "XML validation failed", "validation"
            )
    
    def _scan_malicious_patterns(self, content: bytes, filename: str) -> None:
        """Scan for known malicious patterns"""
        try:
            # Convert to string for pattern matching
            try:
                content_str = content.decode('utf-8', errors='ignore')
            except:
                content_str = str(content)
            
            # Malicious patterns to detect
            malicious_patterns = [
                # Script injection
                r'<script[^>]*>',
                r'javascript:',
                r'vbscript:',
                r'on\w+\s*=',
                
                # Command injection
                r'`[^`]*`',
                r'\$\([^)]*\)',
                r';\s*(rm|del|format|fdisk)',
                
                # Path traversal
                r'\.\./|\.\.\\',
                r'/etc/passwd',
                r'/etc/shadow',
                r'c:\\windows\\system32',
                
                # Network requests
                r'http://\d+\.\d+\.\d+\.\d+',
                r'curl\s+',
                r'wget\s+',
                
                # Suspicious XML
                r'<!ENTITY.*SYSTEM',
                r'<!ENTITY.*PUBLIC',
            ]
            
            import re
            for pattern in malicious_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    ErrorSanitizer.log_security_event(
                        "malicious_pattern_detected",
                        {"filename": filename, "pattern": pattern}
                    )
                    raise ErrorSanitizer.create_http_exception(
                        400, "File contains potentially malicious content", "validation"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Malicious pattern scan error for {filename}: {str(e)}")
            # Don't fail the upload for scan errors, just log them
    
    def process_validated_file(self, content: bytes, validation_result: Dict[str, Any], user_id: str) -> Tuple[str, str]:
        """
        Process a validated file safely with secure storage
        
        Args:
            content: Raw file content
            validation_result: Result from validate_upload
            user_id: User ID for storage isolation
            
        Returns:
            Tuple of (processed_xml_content, processing_id)
        """
        try:
            processing_id = hashlib.sha256(
                f"{validation_result['file_hash']}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16]
            
            # Store uploaded file securely
            storage_result = secure_storage_service.store_uploaded_file(
                content, validation_result, user_id
            )
            
            # Extract XML content based on file type
            if validation_result["is_compressed"]:
                xml_content = self._safe_decompress(content, validation_result["original_filename"])
            else:
                xml_content = content
            
            # Convert to string
            xml_string = xml_content.decode('utf-8')
            
            # Store processed file
            processed_file_path = secure_storage_service.store_processed_file(
                xml_string, storage_result["storage_id"], user_id, processing_id
            )
            
            logger.info(f"File processed and stored successfully: {processing_id}")
            
            return xml_string, processing_id
            
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                500, "File processing failed", "file"
            )

# Global file security service instance
file_security_service = FileSecurityService()