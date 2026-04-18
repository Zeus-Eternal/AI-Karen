"""
Comprehensive input validation and sanitization for AI-Karen chat system.
Extends canonical validation with production validation features.
"""

import re
import html
import logging
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse
import bleach
from pathlib import Path

from .security import ThreatLevel, SecurityLevel, ValidationResult

# Try to import magic, but make it optional
try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class EnhancedValidationResult(ValidationResult):
    """Enhanced validation result with additional features."""

    def __init__(
        self,
        is_valid: bool,
        threats_detected: List[str],
        max_threat_level: ThreatLevel,
        sanitized_content: Optional[str] = None,
        error_message: Optional[str] = None,
        validation_metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            is_valid=is_valid,
            threats_detected=threats_detected,
            max_threat_level=max_threat_level,
            sanitized_content=sanitized_content,
            error_message=error_message,
        )
        self.validation_metadata = validation_metadata or {}

    def get_max_threat_value(self) -> int:
        """Get numeric value for threat level comparison."""
        threat_values = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4,
        }
        return threat_values.get(self.max_threat_level, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "threats_detected": self.threats_detected,
            "max_threat_level": self.max_threat_level.value,
            "sanitized_content": self.sanitized_content,
            "error_message": self.error_message,
            "validation_metadata": self.validation_metadata,
        }


class ContentValidator:
    """Enhanced content validator with comprehensive threat detection."""

    def __init__(self, security_level: SecurityLevel = SecurityLevel.MEDIUM):
        self.security_level = security_level
        self.threat_patterns = self._load_threat_patterns()
        self.allowed_tags = self._get_allowed_tags()
        self.allowed_attributes = self._get_allowed_attributes()

    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load comprehensive threat detection patterns."""
        return {
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
                r"<form[^>]*>",
                r"<input[^>]*>",
                r"<link[^>]*>",
                r"<meta[^>]*>",
                r"expression\s*\(",
                r"url\s*\(",
                r"@import",
                r"eval\s*\(",
                r"exec\s*\(",
                r"vbscript:",
                r"data:text/html",
                r"<!--",
                r"-->",
                r"<!DOCTYPE",
                r"<svg",
                r"<math",
            ],
            "sql_injection": [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
                r"(--|#|\/\*|\*\/)",
                r"(\bOR\b|\bAND\b)\s+\w+\s*=\s*\w+",
                r"(\'\s*OR\s*\'.*\'.*\')|(\".*OR.*\")",
                r"\;\s*(DROP|DELETE|UPDATE|INSERT)",
                r"UNION\s+SELECT",
                r"EXEC\s*\(",
                r"SPIDER\s*",
                r"SYSTEM\s*",
                r"WAITFOR\s+DELAY",
                r"BENCHMARK\s*\(",
                r"SLEEP\s*\(",
                r"PG_SLEEP\s*\(",
            ],
            "command_injection": [
                r"[;&|`$()]",
                r"\b(curl|wget|nc|netcat|telnet|ssh|ftp|scp)\b",
                r"\b(rm|mv|cp|cat|ls|ps|kill|chmod|chown)\b",
                r"\b(python|perl|ruby|bash|sh|cmd|powershell)\b",
                r"\/dev\/(null|zero|random|urandom)",
                r"\.\.\/",
                r"\/etc\/(passwd|shadow|hosts)",
                r"\/proc\/",
                r"\/sys\/",
                r"windows\/system32",
                r"cmd\.exe",
                r"powershell\.exe",
                r"sh\.exe",
                r"bash\.exe",
            ],
            "path_traversal": [
                r"\.\.[\/\\]",
                r"%2e%2e[\/\\]",
                r"%252e%252e[\/\\]",
                r"\.\.%2f",
                r"\.\.%5c",
                r"\/etc\/",
                r"\/proc\/",
                r"\/sys\/",
                r"windows\/system32",
                r"\/var\/www",
                r"\/usr\/bin",
                r"\/bin",
            ],
            "sensitive_data": [
                r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email
                r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IP addresses
                r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",  # IP regex
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # Email regex
            ],
            "api_keys": [
                r'(?i)(api[_-]?key|secret|token|password|credential)[\s]*[:=][\s]*["\']?[a-zA-Z0-9]{10,}["\']?',
                r"(?i)(bearer|basic)[\s]+[a-zA-Z0-9+/=]{20,}",
                r'(?i)(access[_-]?token|auth[_-]?token)[\s]*[:=][\s]*["\']?[a-zA-Z0-9\-_.]{10,}["\']?',
            ],
            "file_inclusion": [
                r"php://",
                r"file://",
                r"expect://",
                r"phar://",
                r"zip://",
                r"zlib://",
                r"data://",
                r"glob://",
                r"ssh2://",
                r"ogg://",
            ],
        }

    def _get_allowed_tags(self) -> List[str]:
        """Get allowed HTML tags based on security level."""
        if self.security_level == SecurityLevel.LOW:
            return [
                "p",
                "br",
                "strong",
                "em",
                "u",
                "i",
                "b",
                "a",
                "img",
                "div",
                "span",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ul",
                "ol",
                "li",
                "blockquote",
                "code",
                "pre",
            ]
        elif self.security_level == SecurityLevel.MEDIUM:
            return [
                "p",
                "br",
                "strong",
                "em",
                "u",
                "i",
                "b",
                "a",
                "ul",
                "ol",
                "li",
                "blockquote",
                "code",
                "pre",
            ]
        elif self.security_level == SecurityLevel.HIGH:
            return ["p", "br", "strong", "em", "u", "i", "b", "code", "pre"]
        else:  # STRICT
            return ["p", "br"]

    def _get_allowed_attributes(self) -> Dict[str, List[str]]:
        """Get allowed HTML attributes based on security level."""
        if self.security_level == SecurityLevel.LOW:
            return {
                "*": ["class", "id", "style"],
                "a": ["href", "title", "target"],
                "img": ["src", "alt", "width", "height", "title"],
                "div": ["class", "id", "style"],
                "span": ["class", "id", "style"],
            }
        elif self.security_level == SecurityLevel.MEDIUM:
            return {"a": ["href", "title"], "*": ["class", "id"], "img": ["src", "alt"]}
        else:  # HIGH, STRICT
            return {}

    def validate_content(
        self,
        content: str,
        content_type: str = "text",
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> EnhancedValidationResult:
        """
        Validate and sanitize content with comprehensive threat detection.

        Args:
            content: The content to validate
            content_type: Type of content (text, html, markdown, json)
            additional_context: Additional context for validation

        Returns:
            EnhancedValidationResult with validation results
        """
        threats_detected = []
        sanitized_content = content
        max_threat_level = ThreatLevel.LOW
        validation_metadata = {
            "original_length": len(content),
            "content_type": content_type,
            "security_level": self.security_level.value,
            "validation_time": datetime.utcnow().isoformat(),
            "additional_context": additional_context or {},
        }

        # Check for threats
        for threat_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    threats_detected.append(f"{threat_type}: {pattern}")
                    # Update max threat level based on threat type
                    if threat_type in ["xss", "sql_injection", "command_injection"]:
                        max_threat_level = max(max_threat_level, ThreatLevel.HIGH)
                    elif threat_type in ["path_traversal", "file_inclusion"]:
                        max_threat_level = max(max_threat_level, ThreatLevel.HIGH)
                    elif threat_type in ["sensitive_data", "api_keys"]:
                        max_threat_level = max(max_threat_level, ThreatLevel.MEDIUM)

        # Sanitize content based on type
        if content_type == "html":
            sanitized_content = self._sanitize_html(content)
        elif content_type == "markdown":
            sanitized_content = self._sanitize_markdown(content)
        elif content_type == "json":
            sanitized_content = self._sanitize_json(content)
        else:
            sanitized_content = self._sanitize_text(content)

        # Check content length
        max_length = self._get_max_content_length()
        if len(sanitized_content) > max_length:
            threats_detected.append(
                f"content_too_long: {len(sanitized_content)} > {max_length}"
            )
            sanitized_content = sanitized_content[:max_length]
            max_threat_level = max(max_threat_level, ThreatLevel.MEDIUM)

        # Additional validation based on content type
        if content_type == "url":
            url_result = self._validate_url(content)
            if not url_result.is_valid:
                threats_detected.extend(url_result.threats_detected)
                max_threat_level = max(max_threat_level, url_result.max_threat_level)

        # Determine if valid
        is_valid = len(threats_detected) == 0 and max_threat_level == ThreatLevel.LOW

        validation_metadata.update(
            {
                "sanitized_length": len(sanitized_content),
                "threats_detected_count": len(threats_detected),
                "max_threat_level": max_threat_level.value,
            }
        )

        return EnhancedValidationResult(
            is_valid=is_valid,
            threats_detected=threats_detected,
            max_threat_level=max_threat_level,
            sanitized_content=sanitized_content,
            validation_metadata=validation_metadata,
        )

    def _sanitize_html(self, content: str) -> str:
        """Sanitize HTML content using bleach."""
        return bleach.clean(
            content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True,
        )

    def _sanitize_markdown(self, content: str) -> str:
        """Sanitize markdown content."""
        # Remove potentially dangerous markdown patterns
        content = re.sub(
            r"!\[.*?\]\(javascript:.*?\)", "", content, flags=re.IGNORECASE
        )
        content = re.sub(r"\[.*?\]\(javascript:.*?\)", "", content, flags=re.IGNORECASE)
        content = re.sub(
            r"`[^`]*<[^>]*`", "", content, flags=re.IGNORECASE
        )  # Code with HTML
        content = re.sub(
            r"```[^`]*<[^>]*```", "", content, flags=re.IGNORECASE
        )  # Code blocks with HTML

        # Then sanitize as text
        return self._sanitize_text(content)

    def _sanitize_json(self, content: str) -> str:
        """Sanitize JSON content."""
        try:
            # Parse and re-serialize to ensure valid JSON
            import json

            parsed = json.loads(content)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            # If invalid JSON, sanitize as text
            return self._sanitize_text(content)

    def _sanitize_text(self, content: str) -> str:
        """Sanitize plain text content."""
        # HTML escape
        content = html.escape(content)

        # Remove dangerous patterns
        for patterns in self.threat_patterns.values():
            for pattern in patterns:
                content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        return content

    def _get_max_content_length(self) -> int:
        """Get maximum content length based on security level."""
        if self.security_level == SecurityLevel.LOW:
            return 10000
        elif self.security_level == SecurityLevel.MEDIUM:
            return 5000
        elif self.security_level == SecurityLevel.HIGH:
            return 2000
        else:  # STRICT
            return 1000

    def _validate_url(self, url: str) -> EnhancedValidationResult:
        """Validate URL content."""
        threats_detected = []
        max_threat_level = ThreatLevel.LOW

        try:
            parsed = urlparse(url)

            # Check for dangerous protocols
            dangerous_protocols = ["javascript:", "data:", "vbscript:", "file:"]
            if parsed.scheme in dangerous_protocols:
                threats_detected.append(f"dangerous_protocol: {parsed.scheme}")
                max_threat_level = max(max_threat_level, ThreatLevel.HIGH)

            # Check for IP addresses (might indicate scanning)
            if re.match(r"^https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", url):
                threats_detected.append("ip_address_url")
                max_threat_level = max(max_threat_level, ThreatLevel.MEDIUM)

            # Check for excessive length
            if len(url) > 2000:
                threats_detected.append("url_too_long")
                max_threat_level = max(max_threat_level, ThreatLevel.MEDIUM)

            return EnhancedValidationResult(
                is_valid=len(threats_detected) == 0,
                threats_detected=threats_detected,
                max_threat_level=max_threat_level,
                validation_metadata={"url": url},
            )

        except Exception as e:
            return EnhancedValidationResult(
                is_valid=False,
                threats_detected=[f"url_parse_error: {str(e)}"],
                max_threat_level=ThreatLevel.HIGH,
                validation_metadata={"url": url},
            )

    def validate_file_upload(
        self, file_data: bytes, filename: str, mime_type: Optional[str] = None
    ) -> EnhancedValidationResult:
        """Validate uploaded file with comprehensive checks."""
        threats_detected = []
        max_threat_level = ThreatLevel.LOW
        validation_metadata = {
            "filename": filename,
            "file_size": len(file_data),
            "mime_type": mime_type,
            "validation_time": datetime.utcnow().isoformat(),
        }

        # Check file size (max 10MB)
        if len(file_data) > 10 * 1024 * 1024:
            threats_detected.append("file_too_large")
            max_threat_level = max(max_threat_level, ThreatLevel.HIGH)

        # Check file extension
        allowed_extensions = [
            ".txt",
            ".pdf",
            ".doc",
            ".docx",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".json",
            ".csv",
        ]
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

        if file_ext not in allowed_extensions:
            threats_detected.append(f"disallowed_file_type: {file_ext}")
            max_threat_level = max(max_threat_level, ThreatLevel.HIGH)

        # Check for malicious content patterns
        content_str = file_data[:1024].decode("utf-8", errors="ignore")
        malicious_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<?php",
            r"<%",
            r"eval\s*\(",
            r"exec\s*\(",
            r"base64_decode\s*\(",
            r"file_get_contents\s*\(",
            r"fopen\s*\(",
            r"system\s*\(",
            r"exec\s*\(",
            r"shell_exec\s*\(",
            r"passthru\s*\(",
            r"assert\s*\(",
        ]

        for pattern in malicious_patterns:
            if re.search(pattern, content_str, re.IGNORECASE):
                threats_detected.append(f"malicious_content: {pattern}")
                max_threat_level = max(max_threat_level, ThreatLevel.HIGH)

        # File type validation using magic if available
        if HAS_MAGIC and mime_type:
            try:
                detected_type = magic.from_buffer(file_data[:1024])
                if detected_type != mime_type:
                    threats_detected.append(
                        f"mime_type_mismatch: {mime_type} vs {detected_type}"
                    )
                    max_threat_level = max(max_threat_level, ThreatLevel.MEDIUM)
            except Exception:
                pass

        # Determine if valid
        is_valid = len(threats_detected) == 0 and max_threat_level == ThreatLevel.LOW

        validation_metadata.update(
            {
                "file_extension": file_ext,
                "threats_detected_count": len(threats_detected),
                "max_threat_level": max_threat_level.value,
            }
        )

        return EnhancedValidationResult(
            is_valid=is_valid,
            threats_detected=threats_detected,
            max_threat_level=max_threat_level,
            validation_metadata=validation_metadata,
        )


# Global instance
enhanced_validator = ContentValidator()


def get_enhanced_validator(
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
) -> ContentValidator:
    """Get an enhanced content validator instance."""
    return ContentValidator(security_level)


# Import datetime for validation_metadata
from datetime import datetime
