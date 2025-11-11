"""Role-based access helpers for UI launchers without framework dependencies."""

from __future__ import annotations

from typing import Any, Callable, Dict


class _UIContext:
    """Minimal context object that mimics the subset of UI helpers used in tests."""

    def __init__(self) -> None:
        self.session_state: Dict[str, Any] = {}

    def error(self, *_: Any, **__: Any) -> None:
        """Placeholder error handler for non-interactive environments."""
        return None


st = _UIContext()


def has_role(role: str) -> bool:
    """Return True if the current user has ``role``."""
    return role in st.session_state.get("roles", [])


def require_role(role: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to gate page rendering by role."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not has_role(role):
                st.error("Access denied")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = ["has_role", "require_role", "st"]
