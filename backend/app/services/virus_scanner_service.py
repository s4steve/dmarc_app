"""
Virus Scanner Service for File Upload Security
This is a basic implementation with pattern-based detection.
In production, integrate with ClamAV or similar antivirus engines.
"""
import re
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from ..utils.error_sanitizer import ErrorSanitizer
import logging

logger = logging.getLogger("security")

class VirusScannerService:
    """Basic virus scanning service with signature-based detection"""
    
    def __init__(self):
        """Initialize virus scanner with known signatures"""
        self.malware_signatures = self._load_malware_signatures()
        self.suspicious_patterns = self._load_suspicious_patterns()
        
    def _load_malware_signatures(self) -> Dict[str, str]:
        """Load known malware signatures (simplified for demo)"""
        # In production, this would load from a proper signature database
        return {
            # EICAR test string (standard antivirus test)
            "eicar": "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*",
            
            # Common malware patterns (simplified)
            "suspicious_base64": r"(?i)(?:powershell|cmd|bash).*(?:base64|encoded)",
            "suspicious_download": r"(?i)(?:wget|curl|invoke-webrequest).*(?:http|ftp)",
            "suspicious_execute": r"(?i)(?:exec|eval|system|shell_exec|passthru)",
            
            # XML-specific threats
            "xml_external_entity": r"<!ENTITY.*SYSTEM.*['\"](?:file|http|ftp)://",
            "xml_parameter_entity": r"<!ENTITY\s+%\s+\w+.*SYSTEM",
            "xml_billion_laughs": r"<!ENTITY\s+\w+.*&\w+;.*&\w+;.*&\w+;",
        }
    
    def _load_suspicious_patterns(self) -> List[Tuple[str, str]]:
        """Load suspicious content patterns"""
        return [
            # Script injection patterns
            (r"<script[^>]*>", "script_injection"),
            (r"javascript:", "javascript_protocol"),
            (r"vbscript:", "vbscript_protocol"),
            (r"on\w+\s*=", "event_handler_injection"),
            
            # Obfuscation patterns
            (r"(?i)(?:char|string).*fromcharcode", "javascript_obfuscation"),
            (r"(?i)eval\s*\(\s*(?:unescape|decode)", "eval_obfuscation"),
            (r"(?i)document\.write.*unescape", "document_write_obfuscation"),
            
            # Suspicious URLs/IPs
            (r"(?i)(?:http|ftp)://(?:\d{1,3}\.){3}\d{1,3}", "suspicious_ip_url"),
            (r"(?i)\.(?:tk|ml|ga|cf|bit\.ly|tinyurl)", "suspicious_domain"),
            
            # Packing/encryption indicators
            (r"(?i)(?:packed|crypted|protected|obfuscated)", "packing_indicators"),
            (r"[A-Za-z0-9+/]{100,}={0,2}", "base64_large_block"),
            
            # Command injection patterns
            (r"(?i)(?:cmd|powershell|bash|sh)\s*[|&;]", "command_injection"),
            (r"(?i)(?:rm|del|format|fdisk)\s+(?:-rf|/s|/q)", "destructive_commands"),
            
            # Network activity
            (r"(?i)(?:socket|connect|bind|listen)\s*\(", "network_activity"),
            (r"(?i)(?:tcp|udp|http).*(?:connect|request)", "network_requests"),
            
            # HTML/XML injection
            (r"<[^>]*alert\s*\(", "alert_injection"),
            (r"<[^>]*prompt\s*\(", "prompt_injection"),
        ]
    
    def scan_content(self, content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """
        Scan file content for malware and suspicious patterns
        
        Args:
            content: File content to scan
            filename: Original filename
            user_id: User ID for logging
            
        Returns:
            Scan results dictionary
        """
        scan_start = datetime.utcnow()
        
        try:
            # Initialize scan results
            scan_result = {
                "scan_timestamp": scan_start.isoformat(),
                "filename": filename,
                "file_size": len(content),
                "file_hash": hashlib.sha256(content).hexdigest(),
                "threats_detected": [],
                "risk_level": "clean",
                "scan_status": "completed",
                "recommendations": []
            }
            
            # Convert content to string for pattern matching
            try:
                content_str = content.decode('utf-8', errors='ignore')
            except:
                content_str = str(content)
            
            # 1. Signature-based detection
            signature_threats = self._scan_signatures(content, content_str)
            scan_result["threats_detected"].extend(signature_threats)
            
            # 2. Pattern-based detection
            pattern_threats = self._scan_patterns(content_str)
            scan_result["threats_detected"].extend(pattern_threats)
            
            # 3. Behavioral analysis
            behavioral_threats = self._analyze_behavior(content_str, filename)
            scan_result["threats_detected"].extend(behavioral_threats)
            
            # 4. File structure analysis
            structure_threats = self._analyze_file_structure(content, filename)
            scan_result["threats_detected"].extend(structure_threats)
            
            # Determine overall risk level
            scan_result["risk_level"] = self._calculate_risk_level(scan_result["threats_detected"])
            
            # Generate recommendations
            scan_result["recommendations"] = self._generate_recommendations(scan_result)
            
            # Log scan results
            self._log_scan_results(scan_result, user_id)
            
            scan_duration = (datetime.utcnow() - scan_start).total_seconds()
            scan_result["scan_duration_seconds"] = scan_duration
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Virus scan error for {filename}: {str(e)}")
            return {
                "scan_timestamp": scan_start.isoformat(),
                "filename": filename,
                "scan_status": "error",
                "error_message": "Scan failed due to technical error",
                "risk_level": "unknown",
                "threats_detected": [],
                "recommendations": ["File could not be scanned - manual review recommended"]
            }
    
    def _scan_signatures(self, content: bytes, content_str: str) -> List[Dict[str, Any]]:
        """Scan for known malware signatures"""
        threats = []
        
        for signature_name, signature_pattern in self.malware_signatures.items():
            try:
                # Check binary content for exact matches
                if signature_name == "eicar":
                    if signature_pattern.encode() in content:
                        threats.append({
                            "type": "malware_signature",
                            "name": signature_name,
                            "severity": "critical",
                            "description": "EICAR test virus detected",
                            "action_required": "block_file"
                        })
                
                # Check string content with regex
                elif re.search(signature_pattern, content_str, re.IGNORECASE | re.MULTILINE):
                    severity = "high" if "entity" in signature_name else "medium"
                    threats.append({
                        "type": "malware_signature",
                        "name": signature_name,
                        "severity": severity,
                        "description": f"Malicious pattern detected: {signature_name}",
                        "action_required": "quarantine" if severity == "high" else "warn"
                    })
                    
            except Exception as e:
                logger.warning(f"Error checking signature {signature_name}: {str(e)}")
                continue
        
        return threats
    
    def _scan_patterns(self, content_str: str) -> List[Dict[str, Any]]:
        """Scan for suspicious patterns"""
        threats = []
        
        for pattern, pattern_name in self.suspicious_patterns:
            try:
                matches = re.findall(pattern, content_str, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Determine severity based on pattern type
                    severity = "medium"
                    if "injection" in pattern_name or "destructive" in pattern_name:
                        severity = "high"
                    elif "obfuscation" in pattern_name or "suspicious" in pattern_name:
                        severity = "low"
                    
                    threats.append({
                        "type": "suspicious_pattern",
                        "name": pattern_name,
                        "severity": severity,
                        "description": f"Suspicious pattern detected: {pattern_name}",
                        "match_count": len(matches),
                        "action_required": "warn" if severity == "low" else "review"
                    })
                    
            except Exception as e:
                logger.warning(f"Error checking pattern {pattern_name}: {str(e)}")
                continue
        
        return threats
    
    def _analyze_behavior(self, content_str: str, filename: str) -> List[Dict[str, Any]]:
        """Analyze behavioral indicators"""
        threats = []
        
        # Check for excessive complexity (potential obfuscation)
        if len(content_str) > 10000:
            # Calculate entropy to detect obfuscation
            entropy = self._calculate_entropy(content_str)
            if entropy > 7.5:  # High entropy suggests obfuscation
                threats.append({
                    "type": "behavioral_analysis",
                    "name": "high_entropy_content",
                    "severity": "medium",
                    "description": f"High entropy content detected (entropy: {entropy:.2f})",
                    "action_required": "review"
                })
        
        # Check for filename/content mismatch
        if filename.lower().endswith('.xml'):
            # DMARC XML should have feedback root element
            if 'feedback' not in content_str.lower() and 'dmarc' not in content_str.lower():
                threats.append({
                    "type": "behavioral_analysis",
                    "name": "content_filename_mismatch",
                    "severity": "medium",
                    "description": "File content doesn't match expected DMARC report format",
                    "action_required": "review"
                })
        
        # Check for excessive external references
        external_refs = len(re.findall(r'(?i)(?:http|ftp|file)://', content_str))
        if external_refs > 5:
            threats.append({
                "type": "behavioral_analysis",
                "name": "excessive_external_references",
                "severity": "medium",
                "description": f"Excessive external references detected: {external_refs}",
                "action_required": "review"
            })
        
        return threats
    
    def _analyze_file_structure(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """Analyze file structure for anomalies"""
        threats = []
        
        # Check for embedded executables
        executable_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
            b'\xfe\xed\xfa',  # Mach-O executable
            b'PK\x03\x04',  # ZIP/JAR (could contain executables)
        ]
        
        for signature in executable_signatures:
            if signature in content:
                threats.append({
                    "type": "file_structure",
                    "name": "embedded_executable",
                    "severity": "high",
                    "description": "Embedded executable content detected",
                    "action_required": "block_file"
                })
                break
        
        # Check for unusual file structure
        if filename.lower().endswith('.xml'):
            # XML files should start with XML declaration or have proper structure
            if not (content.startswith(b'<?xml') or content.startswith(b'\xef\xbb\xbf<?xml') or content.startswith(b'<')):
                threats.append({
                    "type": "file_structure",
                    "name": "invalid_xml_structure",
                    "severity": "medium",
                    "description": "XML file doesn't start with proper XML declaration",
                    "action_required": "review"
                })
        
        return threats
    
    def _calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        
        # Count character frequencies
        frequencies = {}
        for char in data:
            frequencies[char] = frequencies.get(char, 0) + 1
        
        # Calculate entropy
        import math
        entropy = 0.0
        data_len = len(data)
        
        for count in frequencies.values():
            probability = count / data_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _calculate_risk_level(self, threats: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on detected threats"""
        if not threats:
            return "clean"
        
        # Count threats by severity
        critical_count = sum(1 for t in threats if t.get("severity") == "critical")
        high_count = sum(1 for t in threats if t.get("severity") == "high")
        medium_count = sum(1 for t in threats if t.get("severity") == "medium")
        low_count = sum(1 for t in threats if t.get("severity") == "low")
        
        if critical_count > 0:
            return "critical"
        elif high_count > 0 or medium_count > 2:
            return "high"
        elif medium_count > 0 or low_count > 3:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, scan_result: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []
        
        risk_level = scan_result["risk_level"]
        threats = scan_result["threats_detected"]
        
        if risk_level == "critical":
            recommendations.append("BLOCK FILE: Critical malware detected - do not process")
            recommendations.append("Quarantine file immediately")
            recommendations.append("Notify security team")
        
        elif risk_level == "high":
            recommendations.append("QUARANTINE: High-risk content detected")
            recommendations.append("Manual security review required before processing")
            recommendations.append("Consider additional malware scanning")
        
        elif risk_level == "medium":
            recommendations.append("CAUTION: Potentially suspicious content detected")
            recommendations.append("Enhanced monitoring during processing")
            recommendations.append("Log all processing activities")
        
        elif risk_level == "low":
            recommendations.append("MINOR ISSUES: Low-risk patterns detected")
            recommendations.append("Standard processing with logging")
        
        else:
            recommendations.append("File appears clean - standard processing")
        
        # Add specific recommendations based on threat types
        for threat in threats:
            if threat.get("type") == "malware_signature":
                recommendations.append(f"Malware signature detected: {threat.get('name')}")
            elif "injection" in threat.get("name", ""):
                recommendations.append("Potential injection attack - sanitize all inputs")
            elif "obfuscation" in threat.get("name", ""):
                recommendations.append("Obfuscated content - consider deobfuscation analysis")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _log_scan_results(self, scan_result: Dict[str, Any], user_id: str) -> None:
        """Log scan results for security monitoring"""
        if scan_result["risk_level"] in ["critical", "high"]:
            ErrorSanitizer.log_security_event(
                "high_risk_file_detected",
                {
                    "user_id": user_id,
                    "filename": scan_result["filename"],
                    "risk_level": scan_result["risk_level"],
                    "threats_count": len(scan_result["threats_detected"]),
                    "file_hash": scan_result["file_hash"][:16]
                }
            )
        
        elif scan_result["threats_detected"]:
            ErrorSanitizer.log_security_event(
                "suspicious_file_detected",
                {
                    "user_id": user_id,
                    "filename": scan_result["filename"],
                    "risk_level": scan_result["risk_level"],
                    "threats_count": len(scan_result["threats_detected"])
                }
            )

# Global virus scanner service instance
virus_scanner_service = VirusScannerService()