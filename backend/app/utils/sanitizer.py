import re
from typing import Any, Optional
from fastapi import HTTPException

class InputSanitizer:
    """Utility class for sanitizing and validating user inputs to prevent injection attacks"""
    
    @staticmethod
    def sanitize_domain(domain: Optional[str]) -> Optional[str]:
        """
        Sanitize domain input for safe use in Elasticsearch queries
        
        Args:
            domain: Raw domain input from user
            
        Returns:
            Sanitized domain string or None
            
        Raises:
            HTTPException: If domain format is invalid
        """
        if not domain:
            return None
        
        # Remove leading/trailing whitespace and convert to lowercase
        domain = domain.lower().strip()
        
        # Check for suspicious patterns BEFORE sanitization to catch injection attempts
        suspicious_patterns = [
            r'\$\w+',  # MongoDB operators like $ne, $gt, $where
            r'[\{\}\[\]]',  # JSON/NoSQL injection characters
            r'[<>]',  # XML/HTML characters
            r'[;|&]',  # Command injection characters
            r'[\'\"`]',  # Quote characters for SQL/NoSQL injection
            r'drop\s+table',  # SQL injection patterns
            r'select\s+\*',  # SQL injection patterns
            r'where\s+',  # SQL injection patterns
            r'union\s+select',  # SQL injection patterns
            r'insert\s+into',  # SQL injection patterns
            r'delete\s+from',  # SQL injection patterns
            r'\.\./|\.\.\\',  # Path traversal
            r'script\s*[>\(]',  # XSS patterns
            r'javascript:',  # JavaScript protocol
            r'vbscript:',  # VBScript protocol
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # JavaScript eval
            r'expression\s*\(',  # CSS expressions
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters
            r'\\x[0-9a-f]{2}',  # Hex encoded characters
            r'%[0-9a-f]{2}',  # URL encoded characters
            r'//.*--',  # SQL comment patterns
            r'/\*.*\*/',  # Multi-line comment patterns
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Domain contains invalid characters or suspicious patterns."
                )
        
        # Remove potentially dangerous characters after pattern check
        sanitized = re.sub(r'[^\w\.-]', '', domain)
        
        # If sanitization removed too much, it's suspicious
        if len(sanitized) < len(domain) * 0.5:  # More than 50% of characters removed
            raise HTTPException(
                status_code=400,
                detail="Domain contains too many invalid characters."
            )
        
        # Validate domain format (basic DNS name validation)
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if not re.match(domain_pattern, sanitized):
            raise HTTPException(
                status_code=400, 
                detail="Invalid domain format. Domain must contain only letters, numbers, dots, and hyphens."
            )
        
        # Additional security checks
        if len(sanitized) > 253:  # Maximum domain length
            raise HTTPException(
                status_code=400,
                detail="Domain name too long. Maximum length is 253 characters."
            )
        
        return sanitized
    
    @staticmethod
    def validate_integer_range(value: Any, min_val: int, max_val: int, default: int, field_name: str = "value") -> int:
        """
        Validate and sanitize integer inputs within a specified range
        
        Args:
            value: Input value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value  
            default: Default value if input is invalid
            field_name: Name of the field for error messages
            
        Returns:
            Validated integer value
            
        Raises:
            HTTPException: If value is outside allowed range
        """
        try:
            int_val = int(value)
            if int_val < min_val:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field_name} must be at least {min_val}"
                )
            if int_val > max_val:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field_name} must be at most {max_val}"
                )
            return int_val
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}. Must be a number between {min_val} and {max_val}"
            )
    
    @staticmethod
    def sanitize_string_input(input_str: Optional[str], max_length: int = 1000, field_name: str = "input") -> Optional[str]:
        """
        Sanitize general string input to prevent various injection attacks
        
        Args:
            input_str: Raw string input
            max_length: Maximum allowed length
            field_name: Field name for error messages
            
        Returns:
            Sanitized string or None
            
        Raises:
            HTTPException: If input contains dangerous patterns
        """
        if not input_str:
            return None
        
        # Trim whitespace
        sanitized = input_str.strip()
        
        # Check length
        if len(sanitized) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} exceeds maximum length of {max_length} characters"
            )
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'<script.*?>.*?</script.*?>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'vbscript:',  # VBScript protocol
            r'on\w+\s*=',  # Event handlers (onclick, onload, etc.)
            r'expression\s*\(',  # CSS expressions
            r'eval\s*\(',  # JavaScript eval
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {field_name}. Contains potentially dangerous content."
                )
        
        return sanitized
    
    @staticmethod
    def sanitize_elasticsearch_field(field_value: Optional[str]) -> Optional[str]:
        """
        Sanitize field values specifically for Elasticsearch queries
        
        Args:
            field_value: Raw field value
            
        Returns:
            Sanitized field value safe for ES queries
        """
        if not field_value:
            return None
        
        # Remove Elasticsearch special characters that could be used for injection
        dangerous_chars = ['/', '\\', '?', '#', '[', ']', '@', '!', '$', '&', "'", '(', ')', '*', '+', ',', ';', '=']
        sanitized = field_value
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Remove multiple spaces and trim
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized if sanitized else None
    
    @staticmethod
    def validate_pagination_params(page: Any = 1, size: Any = 10) -> tuple[int, int]:
        """
        Validate pagination parameters
        
        Args:
            page: Page number
            size: Page size
            
        Returns:
            Tuple of (validated_page, validated_size)
        """
        validated_page = InputSanitizer.validate_integer_range(page, 1, 1000, 1, "page")
        validated_size = InputSanitizer.validate_integer_range(size, 1, 100, 10, "size")
        
        return validated_page, validated_size
    
    @staticmethod
    def validate_email_format(email: Optional[str]) -> Optional[str]:
        """
        Basic email format validation
        
        Args:
            email: Email address to validate
            
        Returns:
            Sanitized email or None
            
        Raises:
            HTTPException: If email format is invalid
        """
        if not email:
            return None
        
        email = email.lower().strip()
        
        # Basic email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        # Check for dangerous characters
        if any(char in email for char in ['<', '>', '"', "'", '\\', '/', ';']):
            raise HTTPException(
                status_code=400,
                detail="Email contains invalid characters"
            )
        
        return email