"""
Kari RBAC Panel Logic
- Views/edits user roles, role-based policies
- Only accessible to super-admin or org-admin
"""

from typing import Dict, List
from ui.utils.api import (
    fetch_user_roles, update_user_roles, fetch_role_policies, update_role_policies
)

def get_user_roles(user_id: str) -> List[str]:
    return fetch_user_roles(user_id)

def set_user_roles(user_id: str, roles: List[str]):
    return update_user_roles(user_id, roles)

def get_role_policies(role: str) -> Dict:
    return fetch_role_policies(role)

def set_role_policies(role: str, policies: Dict):
    return update_role_policies(role, policies)
