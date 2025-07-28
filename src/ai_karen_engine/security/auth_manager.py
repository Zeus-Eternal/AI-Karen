from __future__ import annotations

import json
import os
import secrets
import hashlib
from pathlib import Path
import time
from typing import Dict, Any, Optional, List
import pyotp

# Path to persistent user store
USER_STORE_PATH = Path(__file__).resolve().parents[3] / "data" / "users.json"


def _hash_password(password: str, *, salt: Optional[str] = None) -> str:
    """Return a salted PBKDF2 hash."""
    salt = salt or secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{pwd_hash.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, hex_hash = stored.split(":")
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return check.hex() == hex_hash


def _init_default_admin() -> Dict[str, Dict[str, Any]]:
    """Create default credentials if the store is missing."""
    admin_email = os.getenv("KARI_ADMIN_EMAIL", "admin@kari.ai")
    admin_password = os.getenv("KARI_ADMIN_PASSWORD", "pswd123")
    user_email = os.getenv("KARI_USER_EMAIL", "user@kari.ai")
    user_password = os.getenv("KARI_USER_PASSWORD", "pswd123")

    return {
        admin_email: {
            "password": _hash_password(admin_password),
            "roles": ["admin", "dev", "user"],
            "is_verified": True,
            "two_factor_enabled": False,
            "totp_secret": None,
        },
        user_email: {
            "password": _hash_password(user_password),
            "roles": ["user"],
            "is_verified": True,
            "two_factor_enabled": False,
            "totp_secret": None,
        },
    }


def _convert_legacy_users(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    converted: Dict[str, Dict[str, Any]] = {}
    for entry in data:
        username = entry.get("username") or entry.get("email")
        if not username:
            continue
        converted[username] = {
            "password": entry.get("password_hash") or entry.get("password", ""),
            "roles": entry.get("roles") or [entry.get("role", "user")],
            "tenant_id": entry.get("tenant_id", "default"),
            "preferences": entry.get("preferences", {}),
        }
    return converted


def load_users() -> Dict[str, Dict[str, Any]]:
    if USER_STORE_PATH.exists():
        try:
            data = json.loads(USER_STORE_PATH.read_text())
            if isinstance(data, list):
                users = _convert_legacy_users(data)
                if users:
                    USER_STORE_PATH.write_text(json.dumps(users, indent=2))
                    return users
            elif isinstance(data, dict):
                return data
        except Exception:
            pass
    users = _init_default_admin()
    USER_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    USER_STORE_PATH.write_text(json.dumps(users, indent=2))
    return users


_USERS: Dict[str, Dict[str, Any]] = load_users()

# --- Verification & Password Reset Tokens ---
# token -> email mapping
EMAIL_VERIFICATION_TOKENS: Dict[str, str] = {}
PASSWORD_RESET_TOKENS: Dict[str, Dict[str, Any]] = {}
PASSWORD_RESET_TOKEN_TTL = 3600  # seconds


def save_users() -> None:
    USER_STORE_PATH.write_text(json.dumps(_USERS, indent=2))

def create_user(
    username: str,
    password: str,
    roles: Optional[List[str]] = None,
    *,
    tenant_id: str = "default",
    preferences: Optional[Dict[str, Any]] = None,
) -> None:
    """Create a new user in the persistent store."""
    if username in _USERS:
        raise KeyError("User already exists")
    _USERS[username] = {
        "password": _hash_password(password),
        "roles": roles or ["user"],
        "tenant_id": tenant_id,
        "preferences": preferences or {},
        "is_verified": False,
        "two_factor_enabled": False,
        "totp_secret": None,
    }
    save_users()


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = _USERS.get(username)
    if not user:
        return None
    if _verify_password(password, user.get("password", "")):
        return user
    return None


def update_credentials(
    current_username: str,
    new_username: Optional[str] = None,
    new_password: Optional[str] = None,
) -> str:
    if current_username not in _USERS:
        raise KeyError("User not found")
    data = _USERS.pop(current_username)
    username = new_username or current_username
    if username in _USERS and username != current_username:
        raise KeyError("Username already exists")
    if new_password:
        data["password"] = _hash_password(new_password)
    _USERS[username] = data
    save_users()
    return username


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def create_email_verification_token(email: str) -> str:
    token = generate_token()
    EMAIL_VERIFICATION_TOKENS[token] = email
    return token


def verify_email_token(token: str) -> Optional[str]:
    return EMAIL_VERIFICATION_TOKENS.pop(token, None)


def mark_user_verified(email: str) -> None:
    if email in _USERS:
        _USERS[email]["is_verified"] = True
        save_users()


def create_password_reset_token(email: str) -> str:
    token = generate_token()
    PASSWORD_RESET_TOKENS[token] = {
        "email": email,
        "expires": time.time() + PASSWORD_RESET_TOKEN_TTL,
    }
    return token


def verify_password_reset_token(token: str) -> Optional[str]:
    data = PASSWORD_RESET_TOKENS.get(token)
    if not data:
        return None
    if data["expires"] < time.time():
        PASSWORD_RESET_TOKENS.pop(token, None)
        return None
    PASSWORD_RESET_TOKENS.pop(token, None)
    return data["email"]


def update_password(email: str, new_password: str) -> None:
    if email in _USERS:
        _USERS[email]["password"] = _hash_password(new_password)
        save_users()


def generate_totp_secret() -> str:
    """Return a new TOTP secret."""
    return pyotp.random_base32()


def get_totp_provisioning_uri(username: str, secret: str, issuer: str = "Kari AI") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def verify_totp(username: str, code: str) -> bool:
    user = _USERS.get(username)
    if not user or not user.get("totp_secret"):
        return False
    totp = pyotp.TOTP(user["totp_secret"])
    return totp.verify(code)


def enable_two_factor(username: str, secret: str) -> None:
    if username in _USERS:
        _USERS[username]["totp_secret"] = secret
        _USERS[username]["two_factor_enabled"] = True
        save_users()


__all__ = [
    "authenticate",
    "update_credentials",
    "create_user",
    "save_users",
    "_USERS",
    "create_email_verification_token",
    "verify_email_token",
    "mark_user_verified",
    "create_password_reset_token",
    "verify_password_reset_token",
    "update_password",
    "generate_totp_secret",
    "get_totp_provisioning_uri",
    "verify_totp",
    "enable_two_factor",
]
