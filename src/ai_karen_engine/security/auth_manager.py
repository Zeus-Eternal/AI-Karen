from __future__ import annotations

import json
import os
import secrets
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List

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
    """Create default admin credentials if store missing."""
    username = os.getenv("KARI_ADMIN_USERNAME", "admin")
    password = os.getenv("KARI_ADMIN_PASSWORD", "admin")
    return {
        username: {
            "password": _hash_password(password),
            "roles": ["admin", "dev", "user"],
        }
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


__all__ = [
    "authenticate",
    "update_credentials",
    "create_user",
    "save_users",
    "_USERS",
]
