import datetime
import zoneinfo
from typing import Dict, Any
from .base import TimeHandlerBase

async def handle_timezone_conversion(params: Dict[str, Any]) -> Dict[str, Any]:
    dt_str = params.get("datetime")
    from_tz_str = params.get("from_timezone")
    to_tz_str = params.get("to_timezone")
    
    if not all([dt_str, from_tz_str, to_tz_str]):
        return {"error": "Missing required conversion fields"}
        
    from_resolved = TimeHandlerBase.resolve_timezone(from_tz_str)
    to_resolved = TimeHandlerBase.resolve_timezone(to_tz_str)
    
    if not from_resolved["success"]: return {"error": f"From TZ Error: {from_resolved['error']}"}
    if not to_resolved["success"]: return {"error": f"To TZ Error: {to_resolved['error']}"}

    from_tz_name = from_resolved["timezone"]
    to_tz_name = to_resolved["timezone"]
        
    try:
        from_tz = zoneinfo.ZoneInfo(from_tz_name)
        to_tz = zoneinfo.ZoneInfo(to_tz_name)
    except zoneinfo.ZoneInfoNotFoundError as e:
        return {"error": f"Invalid timezone post-resolution: {str(e)}"}
        
    try:
        dt = datetime.datetime.fromisoformat(dt_str)
    except ValueError:
        return {"error": f"Invalid datetime format: {dt_str}. Use ISO format."}
        
    if dt.tzinfo is None:
        source_dt = dt.replace(tzinfo=from_tz)
    else:
        source_dt = dt.astimezone(from_tz)
        
    converted_dt = source_dt.astimezone(to_tz)
    
    return {
        "source": {
            "datetime": source_dt.isoformat(),
            "timezone": from_tz_name,
            "utc_offset": source_dt.utcoffset().total_seconds() if source_dt.utcoffset() else 0
        },
        "converted": {
            "datetime": converted_dt.isoformat(),
            "timezone": to_tz_name,
            "utc_offset": converted_dt.utcoffset().total_seconds() if converted_dt.utcoffset() else 0
        }
    }
