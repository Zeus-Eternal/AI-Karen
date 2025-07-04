"""System status monitor for presence tracking."""

from typing import Dict


def get_system_status() -> Dict[str, str]:
    """Return a mock system status report."""
    # This would aggregate health metrics in production
    return {"status": "nominal"}
