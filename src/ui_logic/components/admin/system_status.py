"""
Kari System Status Logic
- Reports real-time status, errors, incidents, and system version
- For admin dashboard health/alert panels
"""

from typing import Dict
from ui.utils.api import fetch_system_status

def get_system_status() -> Dict:
    return fetch_system_status()
