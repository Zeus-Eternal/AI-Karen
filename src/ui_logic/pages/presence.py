"""
Kari Presence Page
- Shows live sessions and device status
"""

from components.presence.session_table import get_active_sessions
from components.presence.status_monitor import get_device_status
from components.presence.device_sync import sync_devices


def presence_page(user_ctx=None):
    sessions = get_active_sessions(user_ctx)
    status = get_device_status(user_ctx)
    return {
        "sessions": sessions,
        "status": status,
    }

__all__ = ["presence_page",]
