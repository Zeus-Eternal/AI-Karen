import datetime
import zoneinfo
from typing import Dict, Any
from .base import TimeHandlerBase
from .state import TimeQueryStateStore

async def handle_multi_clock(params: Dict[str, Any]) -> Dict[str, Any]:
    clocks = params.get("clocks", [])
    results = []
    
    # We optionally can save state here, but typical read pattern just passes array.
    # In a full flow where frontend asks backend to manage the list, use StateStore.
    
    for query in clocks:
        resolved = TimeHandlerBase.resolve_timezone(query)
        if not resolved["success"]:
            results.append({"error": resolved.get("error", "Failed resolution"), "timezone": query})
            continue
            
        tz_name = resolved["timezone"]
        try:
            tz = zoneinfo.ZoneInfo(tz_name)
            now_in_tz = datetime.datetime.now(tz)
            clock_payload = TimeHandlerBase.format_base_payload(
                now=now_in_tz, 
                source="multi_clock",
                resolution_meta={
                    "query": query,
                    "resolvedTimezone": tz_name,
                    "isAmbiguousDefault": resolved.get("is_ambiguous_default", False),
                    "resolutionType": resolved.get("resolution_type", "direct")
                }
            )
            # Add naive label, could be improved with city extract
            clock_payload["label"] = query.split("/")[-1].replace("_", " ").title()
            results.append(clock_payload)
        except zoneinfo.ZoneInfoNotFoundError:
            results.append({"error": f"Unknown timezone '{tz_name}'", "timezone": tz_name})
            
    return {"clocks": results}
