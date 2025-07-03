from .automation_manager import AutomationManager
from .nanda_client import NANDAClient

try:  # optional dependency
    from .local_rpa_client import LocalRPAClient
except Exception:  # pragma: no cover - optional
    LocalRPAClient = None

__all__ = ["AutomationManager", "NANDAClient", "LocalRPAClient"]
