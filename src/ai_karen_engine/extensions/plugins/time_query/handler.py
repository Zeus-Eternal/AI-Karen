import logging
from datetime import datetime
from typing import Any, Dict, Optional
from ai_karen_engine.extensions.platform.core.host.base import ExtensionBase, ExtensionContext

logger = logging.getLogger(__name__)

class TimeQueryExtension(ExtensionBase):
    """Extension for date and time queries."""
    
    def __init__(self, manifest, context: ExtensionContext):
        super().__init__(manifest, context)

    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Provide current date and time."""
        now = datetime.now()
        return {
            "timestamp": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": now.astimezone().tzname(),
            "status": "success"
        }

class MainExtension(TimeQueryExtension):
    """Entry point for ExtensionLoader."""
    pass

async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy entrypoint (optional)."""
    # This is still here for backward compatibility if needed
    now = datetime.now()
    return {"formatted": now.strftime("%Y-%m-%d %H:%M:%S")}
