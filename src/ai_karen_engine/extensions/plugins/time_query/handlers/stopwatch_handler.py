import time
from typing import Dict, Any
from .state import TimeQueryStateStore

async def handle_stopwatch(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action", "status")
    stopwatch_id = params.get("stopwatch_id", "default")
    
    store = TimeQueryStateStore()
    state = store.get_stopwatch()
    
    sw = state.get(stopwatch_id, {
        "stopwatch_id": stopwatch_id,
        "running": False,
        "paused": False,
        "elapsed_ms": 0,
        "started_at": None,
        "last_updated_at": int(time.time() * 1000)
    })
    
    now_ms = int(time.time() * 1000)
    
    if action == "start":
        if not sw["running"]:
            sw["running"] = True
            sw["paused"] = False
            sw["started_at"] = now_ms
            sw["last_updated_at"] = now_ms
    elif action == "pause":
        if sw["running"] and not sw["paused"]:
            sw["paused"] = True
            sw["elapsed_ms"] += (now_ms - sw["last_updated_at"])
            sw["last_updated_at"] = now_ms
    elif action == "resume":
        if sw["running"] and sw["paused"]:
            sw["paused"] = False
            sw["last_updated_at"] = now_ms
    elif action == "stop":
        if sw["running"]:
            if not sw["paused"]:
                sw["elapsed_ms"] += (now_ms - sw["last_updated_at"])
            sw["running"] = False
            sw["paused"] = False
            sw["last_updated_at"] = now_ms
    elif action == "reset":
        sw["running"] = False
        sw["paused"] = False
        sw["elapsed_ms"] = 0
        sw["started_at"] = None
        sw["last_updated_at"] = now_ms
    elif action == "status":
        if sw["running"] and not sw["paused"]:
            sw["elapsed_ms"] += (now_ms - sw["last_updated_at"])
            sw["last_updated_at"] = now_ms

    state[stopwatch_id] = sw
    store.save_stopwatch(state)
    return sw
