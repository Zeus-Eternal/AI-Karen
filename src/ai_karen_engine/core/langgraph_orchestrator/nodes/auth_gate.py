from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone

from ai_karen_engine.auth.auth_service import (
    user_account_to_dict,
)
from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)

async def _ensure_auth_service(self) -> Optional[Any]:
    """Resolve the authentication service on first use."""

    if getattr(self, "_auth_service_failed", False):
        return None

    if getattr(self, "_auth_service", None) is not None:
        return self._auth_service

    async with self._auth_service_lock:
        if self._auth_service is None and not self._auth_service_failed:
            try:
                from ai_karen_engine.auth.auth_service import get_auth_service
                self._auth_service = await get_auth_service()
            except Exception as exc:  # pragma: no cover - depends on environment
                logger.warning("Auth service unavailable: %s", exc)
                self._auth_service_failed = True
                return None

    return self._auth_service

def _serialize_user_account(user: Any) -> Optional[Dict[str, Any]]:
    """Normalise user objects (dataclasses or dicts) into dictionaries."""

    if user is None:
        return None

    if isinstance(user, dict):
        return user

    try:
        return user_account_to_dict(user)
    except Exception:
        if hasattr(user, "__dict__"):
            return {k: getattr(user, k) for k in dir(user) if not k.startswith("_")}
    return None

def _derive_permissions(user_profile: Dict[str, Any]) -> Dict[str, bool]:
    """Map user roles to orchestrator permissions."""

    roles = {role.lower() for role in user_profile.get("roles", [])}
    is_active = user_profile.get("is_active", True)

    return {
        "chat": is_active,
        "tools": bool(roles.intersection({"admin", "developer", "power_user"})),
        "model_management": "admin" in roles,
        "analytics": bool(roles.intersection({"admin", "analyst"})),
    }

async def auth_gate_node(self, state: LangGraphOrchestrationState) -> LangGraphOrchestrationState:
    """Authentication and authorization gate"""
    logger.info(f"Auth gate processing for user: {state.get('user_id')}")

    try:
        errors = state.setdefault("errors", [])
        warnings = state.setdefault("warnings", [])
        service = await _ensure_auth_service(self)
        auth_context = state.get("auth_context") or {}
        token = (
            auth_context.get("access_token")
            or auth_context.get("token")
            or state.get("access_token")
        )

        user: Optional[Any] = None

        if service and token:
            if hasattr(service, "validate_token"):
                user = await service.validate_token(token)
            elif hasattr(service, "verify_token"):
                user = await service.verify_token(token)

        if user is None and service and state.get("user_id"):
            if hasattr(service, "get_user"):
                user = await service.get_user(state["user_id"])

        user_profile = _serialize_user_account(user)

        # Fall back to legacy behaviour when auth service is unavailable
        allow_anonymous = bool(auth_context.get("allow_anonymous"))
        if (
            user_profile is None
            and state.get("user_id")
            and (not service or allow_anonymous)
        ):
            if allow_anonymous:
                warnings.append(
                    "Anonymous copilot access enabled; granting limited chat access"
                )
            else:
                warnings.append(
                    "Auth service unavailable; granting limited chat access"
                )
            user_profile = {
                "user_id": state["user_id"],
                "email": state.get("user_id"),
                "roles": ["user"],
                "is_active": True,
            }

        if user_profile:
            state["user_profile"] = user_profile
            state["auth_status"] = (
                "authenticated" if user_profile.get("is_active", True) else "failed"
            )
            state["user_permissions"] = _derive_permissions(user_profile)
            tenant_id = (
                user_profile.get("tenant_id") or state.get("tenant_id") or "default"
            )
            state["tenant_id"] = tenant_id
            auth_context["last_validated_at"] = datetime.now(
                timezone.utc
            ).isoformat()
            if token:
                auth_context["token_present"] = True
            state["auth_context"] = auth_context

            if state["auth_status"] != "authenticated":
                errors.append("Account is inactive")
        else:
            state["auth_status"] = "failed"
            errors.append("Authentication required")

    except Exception as e:
        logger.error(f"Auth gate error: {e}")
        state["auth_status"] = "failed"
        state.setdefault("errors", []).append(f"Authentication error: {str(e)}")

    return state
