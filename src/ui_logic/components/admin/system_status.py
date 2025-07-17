"""
Kari System Status Logic
- Reports real-time status, errors, incidents, and system version
- For admin dashboard health/alert panels
"""

from typing import Dict
from ui_logic.utils.api import fetch_system_status

def get_system_status() -> Dict:
    return fetch_system_status()


def render_system_status() -> None:
    """Render a minimal system status panel."""
    status = get_system_status()
    st = __import__("streamlit")
    st.markdown("### System Health")
    for key, val in status.items():
        st.write(f"**{key}**: {val}")
