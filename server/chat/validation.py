"""
Comprehensive input validation and sanitization for AI-Karen production chat system.
"""

import re
import html
import logging
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse
import bleach
from pathlib import Path

from .security import ThreatLevel, SecurityLevel

# Try to import magic, but make it optional
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class ValidationResult:
    """Result of input validation."""
    
    def __init__(
        self,
        is_valid: bool,
        threats_detected: List[str],
        max_threat_level: ThreatLevel,
        sanitized_content: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.is_valid = is_valid
        self.threats_detected = threats_detected
        self.max_threat_level = max_threat_level
        self.sanitized_content = sanitized_content
        self.error_message = error_message
    
    def get_max_threat_value(self) -> int:
        """Get numeric value for threat level comparison."""
        threat_values = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        return threat_values.get(self.max_threat_level, 1)


class InputValidator:
    """Comprehensive input validator for chat system."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.content_validator = self._get_content_validator(security_level)
    
    def _get_content_validator(self, security_level: SecurityLevel):
        """Get appropriate content validator based on security level."""
        if security_level == SecurityLevel.LOW:
            return self._low_security_validator()
        elif security_level == SecurityLevel.MEDIUM:
            return self._medium_security_validator()
        elif security_level == SecurityLevel.HIGH:
            return self._high_security_validator()
        else:
            return self._medium_security_validator()
    
    def _low_security_validator(self):
        """Low security level validator - basic checks."""
        patterns = {
            'sql_injection': r'(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            'xss': r'<script[^>]*>.*?</script>',
            'command_injection': r'[;&|`|$]',
            'path_traversal': r'\.\.[\\/]',
            'excessive_length': 10000
        }
        return patterns
    
    def _medium_security_validator(self):
        """Medium security level validator - standard checks."""
        patterns = {
            'sql_injection': r'(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            'xss': r'<script[^>]*>.*?</script>',
            'xss_attr': r'on\w*(load|error|mouseover)',
            'css_injection': r'<style[^>]*>.*?</style>',
            'javascript_injection': r'javascript:',
            'command_injection': r'[;&|`|$]',
            'path_traversal': r'\.\.[\\/]',
            'excessive_length': 5000,
            'too_many_urls': 10,
            'malicious_extensions': r'\.(exe|bat|cmd|scr|pif|com)$',
            'base64_injection': r'(?:[A-Za-z0-9+/]{4,})={0,}',
            'null_bytes': r'\x00'
        }
        return patterns
    
    def _high_security_validator(self):
        """High security level validator - strict checks."""
        patterns = {
            'sql_injection': r'(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
            'xss': r'<script[^>]*>.*?</script>',
            'xss_attr': r'on\w*(load|error|mouseover)',
            'css_injection': r'<style[^>]*>.*?</style>',
            'javascript_injection': r'javascript:',
            'command_injection': r'[;&|`|$]',
            'path_traversal': r'\.\.[\\/]',
            'excessive_length': 2000,
            'too_many_urls': 5,
            'malicious_extensions': r'\.(exe|bat|cmd|scr|pif|com)$',
            'base64_injection': r'(?:[A-Za-z0-9+/]{4,})={0,}',
            'null_bytes': r'\x00',
            'lfi_injection': r'(?:[A-Za-z0-9+/]{4,})={0,}',
            'ssrf_injection': r'<(iframe|frame|object|embed)',
            'ldap_injection': r'[()&|]',
            'xml_injection': r'<\?xml',
            'eval_injection': r'(eval|exec|system)\('
        }
        return patterns
    
    def _update_max_threat(self, current_threat: ThreatLevel, new_threat: ThreatLevel) -> ThreatLevel:
        """Update max threat level based on numeric values."""
        threat_values = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        
        current_value = threat_values.get(current_threat, 1)
        new_value = threat_values.get(new_threat, 1)
        
        if new_value > current_value:
            return new_threat
        return current_threat
    
    def validate_text_content(
        self, 
        content: str, 
        context: Optional[str] = None
    ) -> ValidationResult:
        """Validate text content for security threats."""
        threats = []
        max_threat = ThreatLevel.LOW
        
        if not content or not content.strip():
            return ValidationResult(
                is_valid=False,
                threats_detected=["empty_content"],
                max_threat_level=ThreatLevel.MEDIUM,
                error_message="Content cannot be empty"
            )
        
        # Check length
        patterns = self.content_validator
        if len(content) > patterns.get('excessive_length', 1000):
            threats.append("excessive_length")
            max_threat = self._update_max_threat(max_threat, ThreatLevel.MEDIUM)
        
        # Check for malicious patterns
        malicious_patterns = [
            patterns['sql_injection'],
            patterns['xss'],
            patterns['xss_attr'],
            patterns['css_injection'],
            patterns['javascript_injection'],
            patterns['command_injection'],
            patterns['path_traversal'],
            patterns['base64_injection'],
            patterns['null_bytes']
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                threat_name = self._get_threat_name(pattern)
                threats.append(threat_name)
                max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
        
        # Check for suspicious keywords
        suspicious_keywords = [
            'document.cookie', 'window.location', 'eval(', 'exec(', 'system(',
            'powershell', 'cmd.exe', '/etc/passwd', '/etc/shadow',
            '../', '<script>', 'javascript:', 'vbscript:'
        ]
        
        for keyword in suspicious_keywords:
            if keyword.lower() in content.lower():
                threats.append("suspicious_keyword")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
        
        # Sanitize content
        sanitized = self._sanitize_text(content)
        
        return ValidationResult(
            is_valid=len(threats) == 0,
            threats_detected=threats,
            max_threat_level=max_threat,
            sanitized_content=sanitized
        )
    
    def validate_url(
        self, 
        url: str
    ) -> ValidationResult:
        """Validate URL for security threats."""
        threats = []
        max_threat = ThreatLevel.LOW
        
        if not url:
            return ValidationResult(
                is_valid=False,
                threats_detected=["empty_url"],
                max_threat_level=ThreatLevel.MEDIUM,
                error_message="URL cannot be empty"
            )
        
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                threats.append("invalid_scheme")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
            
            # Check for dangerous patterns
            dangerous_patterns = [
                'javascript:', 'data:', 'vbscript:', 'file:',
                'ftp:', 'mailto:', 'telnet:'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in url.lower():
                    threats.append("dangerous_url_scheme")
                    max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
            
            # Check for path traversal
            if '../' in url or '..' in url:
                threats.append("path_traversal")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
            
            # Check for excessive length
            patterns = self.content_validator
            if len(url) > patterns.get('excessive_length', 1000):
                threats.append("excessive_length")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.MEDIUM)
            
        except Exception:
            threats.append("invalid_url_format")
            max_threat = ThreatLevel.HIGH
        
        return ValidationResult(
            is_valid=len(threats) == 0,
            threats_detected=threats,
            max_threat_level=max_threat
        )
    
    def validate_file_upload(
        self,
        filename: str,
        file_content: bytes,
        file_size: int
    ) -> ValidationResult:
        """Validate file upload for security threats."""
        threats = []
        max_threat = ThreatLevel.LOW
        
        if not filename:
            return ValidationResult(
                is_valid=False,
                threats_detected=["empty_filename"],
                max_threat_level=ThreatLevel.MEDIUM,
                error_message="Filename cannot be empty"
            )
        
        # Check file size
        max_file_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_file_size:
            threats.append("file_too_large")
            max_threat = self._update_max_threat(max_threat, ThreatLevel.MEDIUM)
        
        # Check filename patterns
        patterns = self.content_validator
        
        # Check for malicious extensions
        malicious_extensions = patterns.get('malicious_extensions', r'\.(exe|bat|cmd|scr|pif|com)$')
        if re.search(malicious_extensions, filename, re.IGNORECASE):
            threats.append("malicious_extension")
            max_threat = self._update_max_threat(max_threat, ThreatLevel.CRITICAL)
        
        # Check for path traversal in filename
        if re.search(patterns['path_traversal'], filename):
            threats.append("path_traversal_filename")
            max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.scr$', r'\.pif$',
            r'\.com$', r'\.exe$', r'\.dll$', r'\.so$',
            r'\.sh$', r'\.bash$', r'\.ps1$', r'\.vbs$'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                threats.append("suspicious_filename")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
        
        # Check file content for malicious signatures
        try:
            # Use python-magic to detect file type if available
            if HAS_MAGIC:
                file_type = magic.from_buffer(file_content)
                
                # Check for executable files
                if any(executable in file_type.lower() for executable in [
                    'executable', 'application/x-executable', 'application/x-msdownload',
                    'application/x-msdos-program', 'application/x-shellscript'
                ]):
                    threats.append("executable_file")
                    max_threat = self._update_max_threat(max_threat, ThreatLevel.CRITICAL)
                
                # Check for script files
                if any(script in file_type.lower() for script in [
                    'text/x-php', 'text/x-python', 'application/x-javascript',
                    'text/x-vbscript', 'application/x-sh'
                ]):
                    threats.append("script_file")
                    max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
            
            # Check for suspicious content in files
            suspicious_signatures = [
                b'<script', b'javascript:', b'vbscript:', b'powershell',
                b'cmd.exe', b'/bin/sh', b'/bin/bash',
                b'eval(', b'exec(', b'system('
            ]
            
            for signature in suspicious_signatures:
                if signature in file_content.lower():
                    threats.append("suspicious_content")
                    max_threat = self._update_max_threat(max_threat, ThreatLevel.CRITICAL)
            
        except Exception as e:
            print(f"File content analysis failed: {e}")
        
        return ValidationResult(
            is_valid=len(threats) == 0,
            threats_detected=threats,
            max_threat_level=max_threat
        )
    
    def validate_json_content(
        self,
        json_content: str,
        max_depth: int = 10
    ) -> ValidationResult:
        """Validate JSON content for security threats."""
        threats = []
        max_threat = ThreatLevel.LOW
        
        if not json_content:
            return ValidationResult(
                is_valid=False,
                threats_detected=["empty_json"],
                max_threat_level=ThreatLevel.MEDIUM,
                error_message="JSON content cannot be empty"
            )
        
        try:
            import json
            
            # Parse JSON to check structure
            parsed = json.loads(json_content)
            
            # Check depth
            json_str = json.dumps(parsed)
            if len(json_str) > 50000:  # 50KB limit
                threats.append("json_too_large")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.MEDIUM)
            
            # Check for suspicious keys
            suspicious_keys = [
                'eval', 'exec', 'system', 'cmd', 'powershell',
                'document.cookie', 'window.location', 'alert(',
                '<script', 'javascript:', 'vbscript:'
            ]
            
            def check_keys(obj, depth=0):
                nonlocal max_threat
                if depth > max_depth:
                    return
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if any(sus in key.lower() for sus in suspicious_keys):
                            threats.append("suspicious_json_key")
                            max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
                            return True
                        if isinstance(value, (dict, list)):
                            if check_keys(value, depth + 1):
                                return True
                elif isinstance(obj, list):
                    for item in obj:
                        if check_keys(item, depth + 1):
                            return True
                return False
            
            if check_keys(parsed):
                threats.append("suspicious_json_structure")
                max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
            
        except json.JSONDecodeError:
            threats.append("invalid_json")
            max_threat = ThreatLevel.HIGH
        
        return ValidationResult(
            is_valid=len(threats) == 0,
            threats_detected=threats,
            max_threat_level=max_threat
        )
    
    def validate_metadata(
        self,
        metadata: Dict[str, Any]
    ) -> ValidationResult:
        """Validate metadata for security threats."""
        threats = []
        max_threat = ThreatLevel.LOW
        
        if not metadata:
            return ValidationResult(
                is_valid=True,
                threats_detected=[],
                max_threat_level=ThreatLevel.LOW
            )
        
        # Check for suspicious keys
        suspicious_keys = [
            'eval', 'exec', 'system', 'cmd', 'powershell',
            '<script', 'javascript:', 'vbscript:'
        ]
        
        def check_keys(obj, path=""):
            nonlocal max_threat
            if isinstance(obj, dict):
                for key in obj.keys():
                    if any(sus in key.lower() for sus in suspicious_keys):
                        threats.append("suspicious_metadata_key")
                        max_threat = self._update_max_threat(max_threat, ThreatLevel.HIGH)
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_keys(item, path + "[]"):
                        return True
            return False
        
        if check_keys(metadata):
            return ValidationResult(
                is_valid=False,
                threats_detected=threats,
                max_threat_level=max_threat,
                error_message="Suspicious metadata detected"
            )
        
        return ValidationResult(
            is_valid=True,
            threats_detected=[],
            max_threat_level=ThreatLevel.LOW
        )
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content to prevent XSS."""
        if not text:
            return text
        
        # Remove HTML tags
        text = html.escape(text)
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _get_threat_name(self, pattern: str) -> str:
        """Get human-readable threat name from regex pattern."""
        threat_mapping = {
            'sql_injection': 'SQL Injection',
            'xss': 'XSS Attack',
            'xss_attr': 'XSS Attribute Injection',
            'css_injection': 'CSS Injection',
            'javascript_injection': 'JavaScript Injection',
            'command_injection': 'Command Injection',
            'path_traversal': 'Path Traversal',
            'excessive_length': 'Excessive Length',
            'malicious_extensions': 'Malicious File Extension',
            'base64_injection': 'Base64 Injection',
            'null_bytes': 'Null Byte Injection',
            'lfi_injection': 'Local File Inclusion',
            'ssrf_injection': 'CSRF Attack',
            'ldap_injection': 'LDAP Injection',
            'xml_injection': 'XML Injection',
            'eval_injection': 'Code Injection'
        }
        
        for threat_name, threat_pattern in threat_mapping.items():
            if threat_pattern in pattern:
                return threat_name
        
        return "Unknown Threat"


class ContentSanitizer:
    """Content sanitizer for removing malicious content."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.allowed_tags = self._get_allowed_tags()
    
    def _get_allowed_tags(self):
        """Get allowed HTML tags based on security level."""
        if self.security_level == SecurityLevel.LOW:
            return {
                'p', 'br', 'strong', 'em', 'u', 'i',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre'
            }
        elif self.security_level == SecurityLevel.MEDIUM:
            return {
                'p', 'br', 'strong', 'em', 'u', 'i',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'blockquote', 'code', 'pre'
            }
        elif self.security_level == SecurityLevel.HIGH:
            return {
                'p', 'br', 'strong', 'em'
            }
        else:
            return {
                'p', 'br'
            }
    
    def sanitize_html(self, content: str) -> str:
        """Sanitize HTML content using bleach."""
        if not content:
            return content
        
        return bleach.clean(
            content,
            tags=self.allowed_tags,
            attributes={},
            strip=True
        )
    
    def sanitize_text(self, content: str) -> str:
        """Sanitize text content by removing dangerous characters."""
        if not content:
            return content
        
        # Remove null bytes
        content = content.replace('\x00', '')
        
        # Remove control characters
        content = ''.join(char for char in content if ord(char) >= 32)
        
        # Normalize whitespace
        content = ' '.join(content.split())
        
        return content
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        if not filename:
            return filename
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove null bytes
        filename = filename.replace('\x00', '')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename


# Global validator instance
default_validator = InputValidator()


def get_validator(security_level: SecurityLevel = SecurityLevel.MEDIUM) -> InputValidator:
    """Get input validator for specified security level."""
    return InputValidator(security_level)


def get_sanitizer(security_level: SecurityLevel = SecurityLevel.MEDIUM) -> ContentSanitizer:
    """Get content sanitizer for specified security level."""
    return ContentSanitizer(security_level)


def validate_content(
    content: str, 
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    context: Optional[str] = None
) -> ValidationResult:
    """Validate content using default validator."""
    return default_validator.validate_text_content(content, context)


def validate_url(url: str, security_level: SecurityLevel = SecurityLevel.MEDIUM) -> ValidationResult:
    """Validate URL using default validator."""
    validator = get_validator(security_level)
    return validator.validate_url(url)


def validate_file_upload(
    filename: str,
    file_content: bytes,
    file_size: int,
    security_level: SecurityLevel = SecurityLevel.MEDIUM
) -> ValidationResult:
    """Validate file upload using default validator."""
    validator = get_validator(security_level)
    return validator.validate_file_upload(filename, file_content, file_size)


def validate_json_content(
    json_content: str,
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    max_depth: int = 10
) -> ValidationResult:
    """Validate JSON content using default validator."""
    validator = get_validator(security_level)
    return validator.validate_json_content(json_content, max_depth)


def validate_metadata(
    metadata: Dict[str, Any],
    security_level: SecurityLevel = SecurityLevel.MEDIUM
) -> ValidationResult:
    """Validate metadata using default validator."""
    validator = get_validator(security_level)
    return validator.validate_metadata(metadata)


def sanitize_content(
    content: str,
    security_level: SecurityLevel = SecurityLevel.MEDIUM
) -> str:
    """Sanitize content using default sanitizer."""
    sanitizer = get_sanitizer(security_level)
    return sanitizer.sanitize_text(content)


def sanitize_html(
    content: str,
    security_level: SecurityLevel = SecurityLevel.MEDIUM
) -> str:
    """Sanitize HTML content using default sanitizer."""
    sanitizer = get_sanitizer(security_level)
    return sanitizer.sanitize_html(content)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename using default sanitizer."""
    sanitizer = get_sanitizer(SecurityLevel.HIGH)  # Use high security for filenames
    return sanitizer.sanitize_filename(filename)