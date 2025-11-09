"""Validate tool parameters based on simple YAML rules."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


class ValidationError(Exception):
    pass


def validate(rules: Dict[str, Any], params: Dict[str, Any]) -> None:
    for name, cfg in rules.items():
        value = params.get(name)
        if value is None:
            raise ValidationError(f"missing {name}")
        if "regex" in cfg and not re.match(cfg["regex"], str(value)):
            raise ValidationError(f"{name} invalid")
        if "enum" in cfg and value not in cfg["enum"]:
            raise ValidationError(f"{name} not allowed")


# Login form validation rules
LOGIN_FORM_RULES = {
    "username": {
        "regex": r"^[a-zA-Z0-9._-]{3,50}$",
        "required": False,  # Either username or email for login
        "min_length": 3,
        "max_length": 50
    },
    "email": {
        "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "required": False,  # Either username or email for login
        "max_length": 254
    },
    "password": {
        "regex": r"^.{8,128}$",  # Relaxed for login
        "required": True,
        "min_length": 8,
        "max_length": 128
    },
    "remember_me": {
        "enum": [True, False, "true", "false", "1", "0"],
        "required": False
    },
    "two_factor_code": {
        "regex": r"^\d{6}$",
        "required": False
    }
}

# Registration form validation rules (stricter)
REGISTRATION_FORM_RULES = {
    "username": {
        "regex": r"^[a-zA-Z0-9._-]{3,50}$",
        "required": True,
        "min_length": 3,
        "max_length": 50
    },
    "email": {
        "regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "required": True,
        "max_length": 254
    },
    "password": {
        "regex": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$",
        "required": True,
        "min_length": 8,
        "max_length": 128
    },
    "confirm_password": {
        "required": True,
        "match_field": "password"
    }
}


def validate_form(params: Dict[str, Any], rules: Dict[str, Any], form_type: str = "form") -> None:
    """Generic form validation with enhanced security checks."""
    errors = []
    
    # Special case for login: require either username or email
    if form_type == "login":
        username = params.get("username")
        email = params.get("email")
        if not username and not email:
            errors.append("Either username or email is required")
    
    # Check required fields
    for field, field_rules in rules.items():
        value = params.get(field)
        
        if field_rules.get("required", False) and not value:
            errors.append(f"{field} is required")
            continue
            
        if value is None:
            continue
            
        # String length validation
        if isinstance(value, str):
            min_len = field_rules.get("min_length")
            max_len = field_rules.get("max_length")
            
            if min_len and len(value) < min_len:
                errors.append(f"{field} must be at least {min_len} characters")
            if max_len and len(value) > max_len:
                errors.append(f"{field} must be no more than {max_len} characters")
        
        # Regex validation
        if "regex" in field_rules and isinstance(value, str):
            if not re.match(field_rules["regex"], value):
                if field == "email":
                    errors.append("Invalid email format")
                elif field == "password" and form_type == "registration":
                    errors.append("Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character")
                elif field == "username":
                    errors.append("Username can only contain letters, numbers, dots, underscores, and hyphens")
                elif field == "two_factor_code":
                    errors.append("Two-factor code must be 6 digits")
                else:
                    errors.append(f"{field} format is invalid")
        
        # Enum validation
        if "enum" in field_rules and value not in field_rules["enum"]:
            errors.append(f"{field} must be one of: {', '.join(map(str, field_rules['enum']))}")
        
        # Field matching validation (e.g., password confirmation)
        if "match_field" in field_rules:
            match_value = params.get(field_rules["match_field"])
            if value != match_value:
                errors.append(f"{field} must match {field_rules['match_field']}")
    
    # Additional security checks
    username = params.get("username", "")
    password = params.get("password", "")
    
    # Check for common weak passwords (only for registration)
    if password and form_type == "registration":
        weak_patterns = [
            r"^password\d*$",
            r"^123456\d*$",
            r"^qwerty\d*$",
            r"^admin\d*$",
            username.lower() if username else ""
        ]
        
        for pattern in weak_patterns:
            if pattern and re.match(pattern, password.lower()):
                errors.append("Password is too common or weak")
                break
    
    # Check for SQL injection patterns
    dangerous_patterns = [
        r"['\";]",
        r"--",
        r"/\*",
        r"\*/",
        r"union\s+select",
        r"drop\s+table",
        r"insert\s+into",
        r"delete\s+from"
    ]
    
    for field in ["username", "email"]:
        value = params.get(field, "")
        if isinstance(value, str):
            for pattern in dangerous_patterns:
                if re.search(pattern, value.lower()):
                    errors.append(f"{field} contains invalid characters")
                    break
    
    if errors:
        raise ValidationError("; ".join(errors))


def validate_login_form(params: Dict[str, Any]) -> None:
    """Validate login form parameters."""
    validate_form(params, LOGIN_FORM_RULES, "login")


def validate_registration_form(params: Dict[str, Any]) -> None:
    """Validate registration form parameters with stricter rules."""
    validate_form(params, REGISTRATION_FORM_RULES, "registration")


def validate_password_strength(password: str) -> Dict[str, bool]:
    """Validate password strength and return detailed feedback."""
    checks = {
        "min_length": len(password) >= 8,
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_digit": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r"[@$!%*?&]", password)),
        "not_common": not bool(re.search(r"^(password|123456|qwerty|admin)", password.lower()))
    }
    
    return checks


def get_password_strength_score(password: str) -> int:
    """Get password strength score from 0-100."""
    checks = validate_password_strength(password)
    score = sum(checks.values()) * 16  # Each check worth ~16 points
    
    # Bonus points for length
    if len(password) >= 12:
        score += 4
    if len(password) >= 16:
        score += 4
    
    return min(score, 100)
