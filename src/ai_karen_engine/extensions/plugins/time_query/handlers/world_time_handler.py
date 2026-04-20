import datetime
import zoneinfo
from typing import Dict, Any
from .base import TimeHandlerBase

async def handle_world_time(params: Dict[str, Any]) -> Dict[str, Any]:
    query = params.get("query", "")
    tz_input = params.get("timezone", query)
    
    if not tz_input:
        return {"error": "Missing timezone or location query"}
        
    resolved = TimeHandlerBase.resolve_timezone(tz_input)
    
    if not resolved["success"]:
        return resolved
        
    tz_name = resolved["timezone"]
    
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except zoneinfo.ZoneInfoNotFoundError:
        return {"error": f"Unknown timezone '{tz_name}' after resolution computation"}
        
    now_in_tz = datetime.datetime.now(tz)
    payload = TimeHandlerBase.format_base_payload(
        now=now_in_tz, 
        source="world_clock", 
        resolution_meta={
            "query": resolved["query"],
            "resolvedTimezone": tz_name,
            "isAmbiguousDefault": resolved.get("is_ambiguous_default", False),
            "resolutionType": resolved.get("resolution_type", "direct")
        }
    )
    return payload
