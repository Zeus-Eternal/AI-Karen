from typing import Dict, Any
from .base import TimeHandlerBase

async def handle_current_time(mode: str, params: Dict[str, Any]) -> Dict[str, Any]:
    now = TimeHandlerBase.get_system_now()
    payload = TimeHandlerBase.format_base_payload(now)
    
    # Optionally shape output based on mode, but generally all modes get base + specific if requested
    if mode == "date":
        payload = {"source": payload["source"], "date": payload["date"]}
    elif mode == "time":
        payload = {"source": payload["source"], "time": payload["time"]}
    elif mode == "timestamp":
        payload = {"source": payload["source"], "timestamp": payload["timestamp"]}
    elif mode == "timezone":
        payload = {"source": payload["source"], "timezone": payload["timezone"], "utc_offset": payload["utc_offset"]}
    elif mode == "iso":
        payload = {"source": payload["source"], "iso": payload["iso"]}
    elif mode == "utc":
        payload = {"source": payload["source"], "utc": payload["utc_timestamp"]}
        
    return payload
