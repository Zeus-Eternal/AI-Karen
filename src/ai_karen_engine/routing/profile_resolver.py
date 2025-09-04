"""
ProfileResolver bridges user profiles to task-specific model assignments
used by the KIRE router.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ai_karen_engine.routing.types import (
    ModelAssignment,
    UserProfile,
)

_PROFILE_SRC = ""
get_profile_manager = None
ServiceProfileManager = None
UserProfilesManager = None
try:
    # Preferred: new user profiles manager (config.json)
    from ai_karen_engine.config.user_profiles import get_user_profiles_manager as _get_upm
    UserProfilesManager = _get_upm  # type: ignore
    _PROFILE_SRC = "user_profiles"
except Exception:
    pass
if not _PROFILE_SRC:
    try:
        # YAML-based profile manager
        from ai_karen_engine.config.profile_manager import get_profile_manager as _get_pm
        get_profile_manager = _get_pm  # type: ignore
        _PROFILE_SRC = "config"
    except Exception:
        pass
if not _PROFILE_SRC:
    try:
        # Legacy JSON-based service profile manager
        from ai_karen_engine.services.profile_manager import ProfileManager as _ServicePM
        ServiceProfileManager = _ServicePM  # type: ignore
        _PROFILE_SRC = "service"
    except Exception:
        _PROFILE_SRC = "none"


DEFAULT_ASSIGNMENTS: Dict[str, ModelAssignment] = {
    "chat": ModelAssignment(task_type="chat", provider="openai", model="gpt-4o-mini"),
    "code": ModelAssignment(task_type="code", provider="deepseek", model="deepseek-coder"),
    "reasoning": ModelAssignment(task_type="reasoning", provider="openai", model="gpt-4o"),
    "summarization": ModelAssignment(task_type="summarization", provider="llamacpp", model="tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"),
}


class ProfileResolver:
    """Resolves user profiles and task assignments for KIRE."""

    def __init__(self) -> None:
        self._mode = _PROFILE_SRC
        self._pm = None

    def _get_config_profile(self) -> Optional[UserProfile]:
        if not get_profile_manager:
            return None
        pm = self._pm or get_profile_manager()
        self._pm = pm
        active = pm.get_active_profile()
        if not active:
            return None

        # Map config profile models into KIRE assignments by task types if present
        assignments: Dict[str, ModelAssignment] = {}
        for m in (active.models or []):
            # If the profile defines task_types, apply them; otherwise, skip
            for tt in (m.task_types or []):
                assignments[tt] = ModelAssignment(task_type=tt, provider=m.provider, model=m.model)

        # Fallback to defaults if not provided
        for tt, ma in DEFAULT_ASSIGNMENTS.items():
            assignments.setdefault(tt, ma)

        chain = ["openai", "deepseek", "llamacpp", "huggingface", "gemini"]
        return UserProfile(
            profile_id=active.id,
            name=active.label,
            assignments=assignments,
            fallback_chain=chain,
            khrp_config={},
        )

    def _get_service_profile(self) -> Optional[UserProfile]:
        if ServiceProfileManager is None:
            return None
        spm = self._pm or ServiceProfileManager()
        self._pm = spm
        try:
            active_name = spm._active_profile  # type: ignore[attr-defined]
        except Exception:
            active_name = "default"
        assignments = dict(DEFAULT_ASSIGNMENTS)
        chain = ["openai", "deepseek", "llamacpp", "huggingface", "gemini"]
        return UserProfile(profile_id=active_name, name=active_name, assignments=assignments, fallback_chain=chain, khrp_config={})

    def _get_user_profiles(self) -> Optional[UserProfile]:
        if UserProfilesManager is None:
            return None
        upm = UserProfilesManager()
        prof = upm.get_active_profile() or upm.ensure_default_profile()
        if not prof:
            return None
        assignments: Dict[str, ModelAssignment] = {}
        for tt, ma in prof.assignments.items():
            assignments[tt] = ModelAssignment(task_type=tt, provider=ma.provider, model=ma.model, parameters=ma.parameters)
        chain = prof.fallback_chain or ["openai", "deepseek", "llamacpp", "huggingface", "gemini"]
        return UserProfile(profile_id=prof.id, name=prof.name, assignments=assignments, fallback_chain=chain, khrp_config={})

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        if self._mode == "user_profiles":
            return self._get_user_profiles()
        if self._mode == "config":
            return self._get_config_profile()
        if self._mode == "service":
            return self._get_service_profile()
        return None

    def get_model_assignment(
        self,
        profile: Optional[UserProfile],
        task_type: str,
        khrp_step: Optional[str] = None,
    ) -> Optional[ModelAssignment]:
        if not profile:
            return DEFAULT_ASSIGNMENTS.get(task_type)
        # KHRP step overrides could slot here in the future
        return profile.assignments.get(task_type) or DEFAULT_ASSIGNMENTS.get(task_type)

    def validate_profile(self, profile: UserProfile) -> list[str]:
        # Minimal validation placeholder – can be extended later
        errs: list[str] = []
        for tt, ma in profile.assignments.items():
            if not ma.provider or not ma.model:
                errs.append(f"Assignment for {tt} incomplete")
        return errs
