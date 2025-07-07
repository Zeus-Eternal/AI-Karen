"""
Kari Organization Admin Logic
- Manages users, teams, invites, org-wide roles
- CRUD for users/org settings, RBAC enforced
"""

from typing import Dict, List
from ui_logic.utils.api import (
    fetch_org_users, add_org_user, update_org_user, remove_org_user, 
    fetch_org_settings, update_org_settings
)

def get_org_users(org_id: str) -> List[Dict]:
    return fetch_org_users(org_id)

def create_org_user(org_id: str, user_data: Dict):
    return add_org_user(org_id, user_data)

def update_user(org_id: str, user_id: str, data: Dict):
    return update_org_user(org_id, user_id, data)

def delete_org_user(org_id: str, user_id: str):
    return remove_org_user(org_id, user_id)

def get_org_settings(org_id: str) -> Dict:
    return fetch_org_settings(org_id)

def set_org_settings(org_id: str, data: Dict):
    return update_org_settings(org_id, data)
