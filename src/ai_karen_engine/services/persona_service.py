"""Compatibility wrapper for the production persona service implementation."""

from src.services.memory.persona_service import (  # noqa: F401
    PersonaService,
    get_persona_service,
    initialize_persona_service,
)
