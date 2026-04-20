import uuid
from typing import Dict, Any
from .state import TimeQueryStateStore
from .base import TimeHandlerBase

async def handle_alarm(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action", "list")
    store = TimeQueryStateStore()
    alarms = store.get_alarms()
    
    if action == "list":
        return {"alarms": alarms}
        
    if action == "create":
        # Resolve timezone if provided, otherwise default UTC
        tz_input = params.get("timezone", "UTC")
        resolved = TimeHandlerBase.resolve_timezone(tz_input)
        final_tz = resolved["timezone"] if resolved["success"] else "UTC"

        new_alarm = {
            "alarm_id": str(uuid.uuid4()),
            "title": params.get("title", "New Alarm"),
            "alarm_datetime": params.get("alarm_datetime"),
            "timezone": final_tz,
            "enabled": params.get("enabled", True),
            "recurrence": params.get("recurrence", None)
        }
        alarms.append(new_alarm)
        store.save_alarms(alarms)
        return {"alarm": new_alarm}
        
    alarm_id = params.get("alarm_id")
    if not alarm_id:
        return {"error": "alarm_id required"}
        
    target_idx = next((i for i, a in enumerate(alarms) if a["alarm_id"] == alarm_id), None)
    
    if target_idx is None:
        return {"error": "alarm not found"}
        
    if action == "update":
        updates = {k: v for k, v in params.items() if k in ["title", "alarm_datetime", "timezone", "enabled", "recurrence"]}
        
        # Resolve timezone if attempting to update it
        if "timezone" in updates:
            res = TimeHandlerBase.resolve_timezone(updates["timezone"])
            if res["success"]:
                updates["timezone"] = res["timezone"]
            else:
                return {"error": f"Invalid timezone update: {res.get('error')}"}
                
        alarms[target_idx].update(updates)
        store.save_alarms(alarms)
        return {"alarm": alarms[target_idx]}
        
    if action == "delete":
        deleted = alarms.pop(target_idx)
        store.save_alarms(alarms)
        return {"deleted": deleted}
        
    if action == "enable":
        alarms[target_idx]["enabled"] = True
        store.save_alarms(alarms)
        return {"alarm": alarms[target_idx]}
        
    if action == "disable":
        alarms[target_idx]["enabled"] = False
        store.save_alarms(alarms)
        return {"alarm": alarms[target_idx]}
        
    return {"error": f"Unknown action: {action}"}
