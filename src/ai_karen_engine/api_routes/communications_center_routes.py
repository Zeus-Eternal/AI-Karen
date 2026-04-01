from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.service_registry import get_service_registry
from ai_karen_engine.services.audit_logging import get_audit_logger
from services.memory.internal.training_audit_logger import get_training_audit_logger

router = APIRouter(tags=["communications-center"])


get_current_user = get_current_user_context


@router.get("/observability")
async def get_communications_center_observability(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Backend-derived observability summary for the Communications Center UI."""
    generated_at = datetime.now(timezone.utc).isoformat()
    user_id = str(current_user.get("user_id") or "")

    audit_logger = get_audit_logger()
    training_audit_logger = get_training_audit_logger()

    audit_events = audit_logger.get_recent_events(limit=25)
    audit_event_counts = audit_logger.get_event_counts()
    training_event_counts = training_audit_logger.get_event_counts(hours=24)
    training_security_events = [
        event.to_dict() for event in training_audit_logger.get_security_events(hours=24)
    ]

    memory_observability: Dict[str, Any] = {
        "available": False,
        "pending_writebacks": 0,
        "active_shard_links": 0,
        "feedback_metrics": {},
        "service_metrics": {},
    }
    alerts: List[Dict[str, Any]] = []

    try:
        registry = get_service_registry()
        memory_service = await registry.get_service("memory_service")
        if memory_service is not None:
            service_metrics = (
                memory_service.get_service_metrics()
                if hasattr(memory_service, "get_service_metrics")
                else {}
            )
            feedback_metrics = (
                await memory_service.get_writeback_feedback_metrics(
                    user_id=user_id or None,
                    org_id=str(current_user.get("tenant_id") or "") or None,
                    time_window_hours=24,
                )
                if hasattr(memory_service, "get_writeback_feedback_metrics")
                else {}
            )
            writeback_metrics = service_metrics.get("writeback_system", {}) if isinstance(service_metrics, dict) else {}
            pending_writebacks = int(writeback_metrics.get("pending_writebacks", 0) or 0)
            active_shard_links = int(writeback_metrics.get("active_shard_links", 0) or 0)

            memory_observability = {
                "available": True,
                "pending_writebacks": pending_writebacks,
                "active_shard_links": active_shard_links,
                "feedback_metrics": feedback_metrics,
                "service_metrics": service_metrics,
            }

            if pending_writebacks > 0:
                alerts.append(
                    {
                        "id": "memory-writeback-backlog",
                        "title": "Memory writeback backlog detected",
                        "description": f"{pending_writebacks} response writebacks are still pending processing.",
                        "type": "warning",
                        "timestamp": generated_at,
                    }
                )
    except Exception as exc:
        alerts.append(
            {
                "id": "memory-observability-unavailable",
                "title": "Memory observability unavailable",
                "description": f"Unable to resolve memory service metrics: {exc}",
                "type": "warning",
                "timestamp": generated_at,
            }
        )

    if training_security_events:
        alerts.append(
            {
                "id": "training-security-events",
                "title": "Training security events present",
                "description": f"{len(training_security_events)} training security event(s) were recorded in the last 24 hours.",
                "type": "warning",
                "timestamp": generated_at,
            }
        )

    if not alerts:
        alerts.append(
            {
                "id": "observability-healthy",
                "title": "Observability pipeline healthy",
                "description": "Audit, training, and memory writeback surfaces are responding normally.",
                "type": "info",
                "timestamp": generated_at,
            }
        )

    return {
        "generated_at": generated_at,
        "audit": {
            "recent_events": audit_events,
            "event_counts": audit_event_counts,
        },
        "training": {
            "event_counts": training_event_counts,
            "security_events": training_security_events,
        },
        "memory": memory_observability,
        "alerts": alerts,
    }
