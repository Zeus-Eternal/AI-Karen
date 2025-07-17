from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Announcement:
    """Simple data container for announcements."""

    id: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    summary: Optional[str] = None
    timestamp: Optional[str] = None
    date: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Announcement":
        """Create an Announcement from raw API data."""
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            message=data.get("message"),
            summary=data.get("summary"),
            timestamp=data.get("timestamp"),
            date=data.get("date"),
        )
