"""
Secure File Storage Service with Isolation and Sandboxing
"""
import os
import shutil
import tempfile
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from ..core.config import settings
from ..utils.error_sanitizer import ErrorSanitizer
import logging

logger = logging.getLogger("security")

class SecureStorageService:
    """Service for secure file storage with proper isolation"""
    
    # Storage configuration
    BASE_STORAGE_DIR = "/tmp/dmarc_storage"
    QUARANTINE_DIR = "/tmp/quarantine"
    PROCESSING_DIR = "/tmp/processing"
    ARCHIVE_DIR = "/tmp/archive"
    
    # Storage limits
    MAX_STORAGE_SIZE = 1024 * 1024 * 1024  # 1GB total storage
    MAX_FILES_PER_USER = 100
    FILE_RETENTION_DAYS = 30
    
    def __init__(self):
        """Initialize secure storage service"""
        self._initialize_storage_structure()
        
    def _initialize_storage_structure(self):
        """Create secure storage directory structure"""
        directories = [
            self.BASE_STORAGE_DIR,
            self.QUARANTINE_DIR,
            self.PROCESSING_DIR,
            self.ARCHIVE_DIR,
            f"{self.BASE_STORAGE_DIR}/uploads",
            f"{self.BASE_STORAGE_DIR}/validated",
            f"{self.BASE_STORAGE_DIR}/processed",
            f"{self.BASE_STORAGE_DIR}/metadata"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True, mode=0o700)
            
        # Create .gitkeep files to maintain directory structure
        for directory in directories:
            gitkeep_file = Path(directory) / ".gitkeep"
            gitkeep_file.touch(mode=0o600)
    
    def store_uploaded_file(self, content: bytes, validation_result: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Store uploaded file in secure isolation
        
        Args:
            content: Raw file content
            validation_result: File validation results
            user_id: User ID for isolation
            
        Returns:
            Storage metadata
        """
        try:
            # Check storage limits
            self._check_storage_limits(user_id)
            
            # Generate secure file paths
            file_hash = validation_result["file_hash"]
            storage_id = self._generate_storage_id(file_hash, user_id)
            
            # Create user-specific storage directory
            user_storage_dir = Path(self.BASE_STORAGE_DIR) / "uploads" / self._sanitize_user_id(user_id)
            user_storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            # Store raw file
            raw_file_path = user_storage_dir / f"{storage_id}.raw"
            self._write_file_securely(raw_file_path, content)
            
            # Store metadata
            metadata = {
                "storage_id": storage_id,
                "user_id": user_id,
                "original_filename": validation_result["original_filename"],
                "file_hash": file_hash,
                "file_size": validation_result["file_size"],
                "mime_type": validation_result["detected_mime_type"],
                "upload_timestamp": validation_result["upload_timestamp"],
                "validation_status": "passed",
                "storage_path": str(raw_file_path),
                "is_compressed": validation_result["is_compressed"],
                "decompressed_size": validation_result["decompressed_size"]
            }
            
            metadata_path = self._store_metadata(metadata, user_id, storage_id)
            
            logger.info(f"File stored securely: {storage_id} for user {user_id}")
            
            return {
                "storage_id": storage_id,
                "storage_path": str(raw_file_path),
                "metadata_path": str(metadata_path),
                "user_storage_dir": str(user_storage_dir)
            }
            
        except Exception as e:
            logger.error(f"Secure storage error for user {user_id}: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                500, "File storage failed", "storage"
            )
    
    def store_processed_file(self, xml_content: str, storage_id: str, user_id: str, processing_id: str) -> str:
        """
        Store processed XML content
        
        Args:
            xml_content: Processed XML content
            storage_id: Original storage ID
            user_id: User ID for isolation
            processing_id: Processing session ID
            
        Returns:
            Path to processed file
        """
        try:
            # Create processed file storage
            user_processed_dir = Path(self.BASE_STORAGE_DIR) / "processed" / self._sanitize_user_id(user_id)
            user_processed_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            processed_file_path = user_processed_dir / f"{storage_id}_{processing_id}.xml"
            
            # Store processed XML
            self._write_file_securely(processed_file_path, xml_content.encode('utf-8'))
            
            # Update metadata
            self._update_processing_metadata(storage_id, user_id, processing_id, str(processed_file_path))
            
            logger.info(f"Processed file stored: {processed_file_path}")
            return str(processed_file_path)
            
        except Exception as e:
            logger.error(f"Processed file storage error: {str(e)}")
            raise ErrorSanitizer.create_http_exception(
                500, "Processed file storage failed", "storage"
            )
    
    def quarantine_file(self, content: bytes, reason: str, user_id: str, filename: str) -> str:
        """
        Quarantine suspicious files
        
        Args:
            content: File content to quarantine
            reason: Quarantine reason
            user_id: User ID
            filename: Original filename
            
        Returns:
            Quarantine file path
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = self._sanitize_filename(filename)
            quarantine_filename = f"{timestamp}_{self._sanitize_user_id(user_id)}_{safe_filename}"
            
            quarantine_path = Path(self.QUARANTINE_DIR) / quarantine_filename
            
            # Store quarantined file
            self._write_file_securely(quarantine_path, content)
            
            # Store quarantine metadata
            quarantine_metadata = {
                "quarantine_reason": reason,
                "user_id": user_id,
                "original_filename": filename,
                "quarantine_timestamp": datetime.utcnow().isoformat(),
                "file_size": len(content),
                "file_hash": hashlib.sha256(content).hexdigest()
            }
            
            metadata_path = quarantine_path.with_suffix('.meta')
            self._write_file_securely(metadata_path, json.dumps(quarantine_metadata, indent=2).encode())
            
            logger.warning(f"File quarantined: {quarantine_path} - Reason: {reason}")
            
            ErrorSanitizer.log_security_event(
                "file_quarantined",
                {
                    "user_id": user_id,
                    "filename": filename,
                    "reason": reason,
                    "quarantine_path": str(quarantine_path)
                }
            )
            
            return str(quarantine_path)
            
        except Exception as e:
            logger.error(f"File quarantine error: {str(e)}")
            # Don't fail the operation, just log the error
            return ""
    
    def get_user_files(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of files for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata
        """
        try:
            user_metadata_dir = Path(self.BASE_STORAGE_DIR) / "metadata" / self._sanitize_user_id(user_id)
            
            if not user_metadata_dir.exists():
                return []
            
            files = []
            metadata_files = sorted(
                user_metadata_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Sanitize metadata for response
                    safe_metadata = {
                        "storage_id": metadata.get("storage_id"),
                        "original_filename": metadata.get("original_filename"),
                        "file_size": metadata.get("file_size"),
                        "upload_timestamp": metadata.get("upload_timestamp"),
                        "mime_type": metadata.get("mime_type"),
                        "validation_status": metadata.get("validation_status"),
                        "processing_status": metadata.get("processing_status", "pending")
                    }
                    files.append(safe_metadata)
                    
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_file}: {str(e)}")
                    continue
            
            return files
            
        except Exception as e:
            logger.error(f"Error retrieving user files for {user_id}: {str(e)}")
            return []
    
    def cleanup_expired_files(self) -> int:
        """
        Clean up expired files based on retention policy
        
        Returns:
            Number of files cleaned up
        """
        try:
            cleanup_count = 0
            cutoff_date = datetime.utcnow() - timedelta(days=self.FILE_RETENTION_DAYS)
            
            # Cleanup storage directories
            storage_dirs = [
                Path(self.BASE_STORAGE_DIR) / "uploads",
                Path(self.BASE_STORAGE_DIR) / "processed",
                Path(self.QUARANTINE_DIR)
            ]
            
            for storage_dir in storage_dirs:
                if not storage_dir.exists():
                    continue
                
                for file_path in storage_dir.rglob("*"):
                    if not file_path.is_file():
                        continue
                    
                    try:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_date:
                            file_path.unlink()
                            cleanup_count += 1
                            logger.info(f"Cleaned up expired file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Error cleaning up file {file_path}: {str(e)}")
            
            logger.info(f"Cleanup completed: {cleanup_count} files removed")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"File cleanup error: {str(e)}")
            return 0
    
    def _check_storage_limits(self, user_id: str) -> None:
        """Check storage limits for user"""
        try:
            user_storage_dir = Path(self.BASE_STORAGE_DIR) / "uploads" / self._sanitize_user_id(user_id)
            
            if user_storage_dir.exists():
                # Check file count
                file_count = len(list(user_storage_dir.glob("*.raw")))
                if file_count >= self.MAX_FILES_PER_USER:
                    raise ErrorSanitizer.create_http_exception(
                        429, f"Maximum file limit reached ({self.MAX_FILES_PER_USER} files)", "storage"
                    )
                
                # Check total size
                total_size = sum(f.stat().st_size for f in user_storage_dir.rglob("*") if f.is_file())
                if total_size > self.MAX_STORAGE_SIZE // 10:  # 10% of total limit per user
                    raise ErrorSanitizer.create_http_exception(
                        429, "Storage quota exceeded", "storage"
                    )
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Storage limit check error for {user_id}: {str(e)}")
    
    def _generate_storage_id(self, file_hash: str, user_id: str) -> str:
        """Generate unique storage ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_data = f"{file_hash}_{user_id}_{timestamp}"
        storage_id = hashlib.sha256(unique_data.encode()).hexdigest()[:16]
        return storage_id
    
    def _sanitize_user_id(self, user_id: str) -> str:
        """Sanitize user ID for safe filesystem usage"""
        import re
        sanitized = re.sub(r'[^\w@.-]', '_', user_id)
        return sanitized[:50]  # Limit length
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        sanitized = re.sub(r'[^\w.-]', '_', filename)
        return sanitized[:100]  # Limit length
    
    def _write_file_securely(self, file_path: Path, content: bytes) -> None:
        """Write file with secure permissions"""
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            
        # Move with secure permissions
        shutil.move(temp_file.name, file_path)
        os.chmod(file_path, 0o600)  # Owner read/write only
    
    def _store_metadata(self, metadata: Dict[str, Any], user_id: str, storage_id: str) -> Path:
        """Store file metadata"""
        user_metadata_dir = Path(self.BASE_STORAGE_DIR) / "metadata" / self._sanitize_user_id(user_id)
        user_metadata_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        metadata_path = user_metadata_dir / f"{storage_id}.json"
        metadata_content = json.dumps(metadata, indent=2).encode()
        
        self._write_file_securely(metadata_path, metadata_content)
        return metadata_path
    
    def _update_processing_metadata(self, storage_id: str, user_id: str, processing_id: str, processed_path: str) -> None:
        """Update metadata with processing information"""
        try:
            user_metadata_dir = Path(self.BASE_STORAGE_DIR) / "metadata" / self._sanitize_user_id(user_id)
            metadata_path = user_metadata_dir / f"{storage_id}.json"
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                metadata.update({
                    "processing_id": processing_id,
                    "processed_path": processed_path,
                    "processing_timestamp": datetime.utcnow().isoformat(),
                    "processing_status": "completed"
                })
                
                self._write_file_securely(metadata_path, json.dumps(metadata, indent=2).encode())
                
        except Exception as e:
            logger.warning(f"Failed to update processing metadata: {str(e)}")

# Global secure storage service instance
secure_storage_service = SecureStorageService()