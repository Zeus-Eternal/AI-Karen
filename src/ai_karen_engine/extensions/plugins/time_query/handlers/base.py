import datetime
import zoneinfo
from typing import Dict, Any, Optional

LOCATION_TIMEZONE_ALIASES = {
    "zambia": "Africa/Lusaka",
    "lusaka": "Africa/Lusaka",
    "new york": "America/New_York",
    "ny": "America/New_York",
    "london": "Europe/London",
    "tokyo": "Asia/Tokyo",
    "uk": "Europe/London",
    "united kingdom": "Europe/London"
}

AMBIGUOUS_LOCATION_DEFAULTS = {
    "usa": "America/New_York",
    "us": "America/New_York",
    "united states": "America/New_York",
    "canada": "America/Toronto",
    "australia": "Australia/Sydney",
    "brazil": "America/Sao_Paulo",
}

class TimeHandlerBase:
    """Base class providing shared logic for time handlers."""
    
    @classmethod
    def get_system_now(cls) -> datetime.datetime:
        """Returns the current local system datetime."""
        return datetime.datetime.now(datetime.timezone.utc).astimezone()

    @classmethod
    def resolve_timezone(cls, query: str) -> Dict[str, Any]:
        """Resolves a query string to a timezone with disambiguation metadata."""
        if not query:
            return {"success": False, "error": "Empty timezone query"}
            
        clean_query = query.strip().lower()
        
        # 1. Check direct aliases
        if clean_query in LOCATION_TIMEZONE_ALIASES:
            tz_str = LOCATION_TIMEZONE_ALIASES[clean_query]
            return {
                "success": True,
                "timezone": tz_str,
                "query": query,
                "is_ambiguous_default": False,
                "resolution_type": "alias"
            }
            
        # 2. Check ambiguous country defaults
        if clean_query in AMBIGUOUS_LOCATION_DEFAULTS:
            tz_str = AMBIGUOUS_LOCATION_DEFAULTS[clean_query]
            return {
                "success": True,
                "timezone": tz_str,
                "query": query,
                "is_ambiguous_default": True,
                "resolution_type": "country_default"
            }
            
        # 3. Direct timezone database name check (case sensitive-ish, we try to ensure casing if possible)
        # We will attempt the exact query, and if it fails, maybe a title case version
        try:
            zoneinfo.ZoneInfo(query)
            return {
                "success": True,
                "timezone": query,
                "query": query,
                "is_ambiguous_default": False,
                "resolution_type": "direct_timezone"
            }
        except zoneinfo.ZoneInfoNotFoundError:
            try:
                # Try title casing generic inputs e.g. america/new_york -> America/New_York
                parts = query.split('/')
                title_query = '/'.join(p.title() for p in parts)
                zoneinfo.ZoneInfo(title_query)
                return {
                    "success": True,
                    "timezone": title_query,
                    "query": query,
                    "is_ambiguous_default": False,
                    "resolution_type": "direct_timezone"
                }
            except zoneinfo.ZoneInfoNotFoundError:
                return {
                    "success": False,
                    "error": f"Unknown timezone or location '{query}'"
                }

    @classmethod
    def format_base_payload(cls, now: datetime.datetime, source: str = "system_clock", resolution_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Returns the standard payload fields."""
        utc_now = now.astimezone(datetime.timezone.utc)
        payload = {
            "source": source,
            "timestamp": now.timestamp(),
            "iso": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "timezone": now.tzname(),
            "utc_timestamp": utc_now.isoformat(),
            "utc_offset": now.utcoffset().total_seconds() if now.utcoffset() else 0
        }
        if resolution_meta:
            payload["resolution_meta"] = resolution_meta
        return payload
