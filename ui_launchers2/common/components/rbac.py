try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - fallback for non-UI environments
    class _DummyStreamlit:
        """Minimal stub for Streamlit when the package is unavailable."""

        def __init__(self) -> None:
            self.session_state = {}

        def error(self, *args, **kwargs) -> None:  # noqa: D401
            """Placeholder for ``st.error`` used in tests."""

    st = _DummyStreamlit()
from typing import Callable, Any

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

