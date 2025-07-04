"""
Kari Calendar Page
- Exposes calendar operations via calendar_panel component
"""

from components.scheduling.calendar_panel import (
    get_calendar,
    add_event,
    remove_event,
    update_event,
    get_calendar_audit_trail,
)


def calendar_page(user_ctx=None):
    """Return calendar data for the UI layer."""
    return {
        "events": get_calendar(user_ctx),
        "audit": get_calendar_audit_trail(user_ctx),
    }
