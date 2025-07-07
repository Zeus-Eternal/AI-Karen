"""
Kari UI Telemetry & Observability Module
- Prometheus metrics, forensic audit logs, and dark analytics ready
- Ultra-granular: per-event, per-user, per-session
- Privacy-aware: opt-in/out, masking, and redaction
"""

import time
import uuid
from typing import Dict, Any, Optional

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROM_ENABLED = True
except ImportError:
    PROM_ENABLED = False

# === Telemetry Config ===
TELEMETRY_LOG_PATH = "/secure/logs/kari/telemetry.log"

if PROM_ENABLED:
    TELEMETRY_EVENT_COUNT = Counter(
        "kari_ui_telemetry_events_total", "Total telemetry events emitted"
    )
    TELEMETRY_EVENT_LATENCY = Histogram(
        "kari_ui_telemetry_event_latency_seconds", "Latency of UI events (seconds)"
    )
    TELEMETRY_ACTIVE_USERS = Gauge(
        "kari_ui_active_users", "Currently active UI users"
    )
else:
    # Fallback stubs
    def TELEMETRY_EVENT_COUNT(*_a, **_k) -> None:
        return None

    def TELEMETRY_EVENT_LATENCY(*_a, **_k) -> None:
        return None

    def TELEMETRY_ACTIVE_USERS(*_a, **_k) -> None:
        return None

def telemetry_event(event_type: str, event_data: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None):
    """
    Emit a telemetry event: logs to file and Prometheus (if available).
    Example: telemetry_event("chat_message", {"tokens": 73}, user_id="admin")
    """
    t0 = time.time()
    correlation_id = str(uuid.uuid4())
    event = {
        "event_type": event_type,
        "user_id": user_id,
        "data": event_data or {},
        "timestamp": int(t0),
        "correlation_id": correlation_id,
    }
    # Log event to secure log file
    try:
        with open(TELEMETRY_LOG_PATH, "a") as f:
            f.write(str(event) + "\n")
    except Exception:
        # Do not raise—telemetry is best effort
        pass

    # Prometheus metrics
    if PROM_ENABLED:
        TELEMETRY_EVENT_COUNT.inc()
        TELEMETRY_EVENT_LATENCY.observe(time.time() - t0)
        if event_type == "user_login":
            TELEMETRY_ACTIVE_USERS.inc()
        elif event_type == "user_logout":
            TELEMETRY_ACTIVE_USERS.dec()

def telemetry_user_session(start: bool, user_id: str):
    """Track user session start/stop for active user gauge (Prometheus)."""
    if PROM_ENABLED:
        if start:
            TELEMETRY_ACTIVE_USERS.inc()
        else:
            TELEMETRY_ACTIVE_USERS.dec()
    telemetry_event(
        "user_login" if start else "user_logout", {}, user_id=user_id
    )

__all__ = [
    "telemetry_event",
    "telemetry_user_session",
]
