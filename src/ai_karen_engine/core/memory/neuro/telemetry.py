from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger("kari.memory.neuro")


def emit_memory_event(event: str, payload: Dict[str, Any]) -> None:
    logger.info(event, extra=payload)
