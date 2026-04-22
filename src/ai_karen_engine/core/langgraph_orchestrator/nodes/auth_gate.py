from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage

# from ai_karen_engine.auth.auth_service import (
#     get_auth_service,
#     user_account_to_dict,
# )
from ..contracts.orchestration_state import LangGraphOrchestrationState
from ..utils.message_serialization import extract_last_user_content

logger = logging.getLogger(__name__)


def serialize_user_account(user: Any) -> Optional[Dict[str, Any]]:
    """Normalise user objects (dataclasses or dicts) into dictionaries."""
    if user is None:
        return None
    if isinstance(user, dict):
        return user
    try:
        from ai_karen_engine.auth.auth_service import user_account_to_dict

        return user_account_to_dict(user)
    except Exception:
        if hasattr(user, "__dict__"):
            return {k: getattr(user, k) for k in dir(user) if not k.startswith("_")}
    return None


def derive_permissions(user_profile: Dict[str, Any]) -> Dict[str, bool]:
    """Map user roles to orchestrator permissions."""
    roles = {role.lower() for role in user_profile.get("roles", [])}
    is_active = user_profile.get("is_active", True)

    return {
        "chat": is_active,
        "tools": bool(roles.intersection({"admin", "developer", "power_user"})),
        "model_management": "admin" in roles,
        "analytics": bool(roles.intersection({"admin", "analyst"})),
    }


class AuthGateNode:
    """Authentication and authorization gate"""

    def __init__(self, auth_service=None):
        self._auth_service = auth_service
        self._auth_service_lock = None
        self._auth_service_failed = False

    async def _ensure_auth_service(self) -> Optional[Any]:
        """Resolve authentication service on first use."""
        if self._auth_service_failed:
            return None

        if self._auth_service is not None:
            return self._auth_service

        try:
            from ai_karen_engine.auth.auth_service import get_auth_service

            self._auth_service = await get_auth_service()
        except Exception as exc:
            logger.warning("Auth service unavailable: %s", exc)
            self._auth_service_failed = True
            return None

        return self._auth_service

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Process authentication and authorization"""
        logger.info(f"Auth gate processing for user: {state.get('user_id')}")

        try:
            errors = state.setdefault("errors", [])
            warnings = state.setdefault("warnings", [])
            service = await self._ensure_auth_service()
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

            user_profile = serialize_user_account(user)

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
                state["user_permissions"] = derive_permissions(user_profile)
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
                    state["degraded_mode"] = True
                    state.setdefault("degradation_reasons", []).append(
                        "inactive_account"
                    )
            else:
                state["auth_status"] = "failed"
                errors.append("Authentication required")

        except Exception as e:
            logger.error(f"Auth gate error: {e}")
            state["auth_status"] = "failed"
            state.setdefault("errors", []).append(f"Authentication error: {str(e)}")
            state["degraded_mode"] = True
            state.setdefault("degradation_reasons", []).append("auth_error")

        return state


async def auth_gate_node(
    state: LangGraphOrchestrationState,
    auth_service=None,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for AuthGateNode"""
    node = AuthGateNode(auth_service)
    return await node(state)
