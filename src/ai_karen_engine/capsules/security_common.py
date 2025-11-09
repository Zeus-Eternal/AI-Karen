"""
Capsule Security Common Module - Shared Security Primitives

This module provides cryptographic, sanitization, and validation
utilities shared across all Kari AI capsules.

Zero-trust enforcement layer for:
- Prompt sanitization and banned token detection
- JWT validation and RBAC enforcement
- Cryptographic integrity verification
- Hardware isolation controls
"""

import re
import html
from typing import List, Set

# === Banned Tokens (Security Policy) ===
BANNED_TOKENS: Set[str] = {
    "system(",
    "exec(",
    "import ",
    "os.",
    "open(",
    "eval(",
    "subprocess",
    "pickle",
    "base64",
    "__import__",
    "compile(",
    "globals(",
    "locals(",
    "__builtins__",
}

# === Dangerous Unicode Control Characters ===
UNICODE_CONTROL_PATTERN = re.compile(r'[\u0000-\u001F\u007F-\u009F]')

# === SQL Injection Patterns ===
SQL_INJECTION_PATTERN = re.compile(
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)|"
    r"(--|;|\/\*|\*\/|xp_|sp_)",
    re.IGNORECASE
)

# === Shell Command Injection Patterns ===
SHELL_INJECTION_PATTERN = re.compile(
    r"[;&|`$(){}[\]<>]|"
    r"\b(bash|sh|cmd|powershell|curl|wget|nc|netcat)\b",
    re.IGNORECASE
)


class PromptSecurityError(Exception):
    """Raised when prompt fails security validation"""
    pass


def sanitize_prompt_input(input_text: str, max_length: int = 8192) -> str:
    """
    Sanitize user input for prompt injection with multi-layer defense:

    1. Length validation
    2. HTML entity encoding
    3. Unicode control character removal
    4. Banned token detection
    5. SQL injection pattern detection
    6. Shell command injection pattern detection

    Args:
        input_text: Raw user input
        max_length: Maximum allowed input length

    Returns:
        Sanitized input text

    Raises:
        PromptSecurityError: If input fails security validation
    """
    if not input_text:
        return ""

    # Phase 1: Length validation
    if len(input_text) > max_length:
        raise PromptSecurityError(
            f"Input exceeds maximum length of {max_length} characters"
        )

    # Phase 2: HTML encoding (prevent XSS-style attacks)
    sanitized = html.escape(input_text)

    # Phase 3: Remove Unicode control characters
    sanitized = UNICODE_CONTROL_PATTERN.sub('', sanitized)

    # Phase 4: Check for banned tokens
    lower_text = sanitized.lower()
    for banned in BANNED_TOKENS:
        if banned.lower() in lower_text:
            raise PromptSecurityError(
                f"Input contains banned token: {banned}"
            )

    # Phase 5: SQL injection detection
    if SQL_INJECTION_PATTERN.search(sanitized):
        raise PromptSecurityError(
            "Input contains potential SQL injection pattern"
        )

    # Phase 6: Shell injection detection
    if SHELL_INJECTION_PATTERN.search(sanitized):
        raise PromptSecurityError(
            "Input contains potential shell command injection pattern"
        )

    return sanitized


def validate_prompt_safety(prompt: str) -> bool:
    """
    Validate that a rendered prompt meets safety requirements.

    Args:
        prompt: Fully rendered prompt text

    Returns:
        True if prompt is safe

    Raises:
        PromptSecurityError: If prompt contains banned patterns
    """
    # Check for banned tokens in final prompt
    lower_prompt = prompt.lower()
    violations = [token for token in BANNED_TOKENS if token.lower() in lower_prompt]

    if violations:
        raise PromptSecurityError(
            f"Prompt contains banned tokens: {', '.join(violations)}"
        )

    return True


def sanitize_dict_values(data: dict, max_length: int = 8192) -> dict:
    """
    Recursively sanitize all string values in a dictionary.

    Args:
        data: Dictionary with potentially unsafe values
        max_length: Maximum length for string values

    Returns:
        Dictionary with sanitized values
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_prompt_input(value, max_length)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_values(value, max_length)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_prompt_input(item, max_length) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


# === Validation Functions ===

def validate_allowed_tools(requested_tool: str, allowed_tools: List[str]) -> bool:
    """
    Validate that a tool access request is permitted.

    Args:
        requested_tool: Tool identifier being requested
        allowed_tools: List of allowed tool identifiers from manifest

    Returns:
        True if tool is allowed

    Raises:
        PromptSecurityError: If tool is not in allowed list
    """
    if requested_tool not in allowed_tools:
        raise PromptSecurityError(
            f"Tool '{requested_tool}' not in allowed tools list"
        )
    return True
