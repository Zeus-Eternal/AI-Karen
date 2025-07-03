import streamlit as st
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

