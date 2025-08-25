from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class ISO8601Model(BaseModel):
    """Base model with automatic ISO 8601 datetime serialization."""

    model_config = ConfigDict()
    
    @field_serializer('*', when_used='json')
    def serialize_datetime(self, value: Any) -> Any:
        """Serialize datetime objects to ISO 8601 format."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


__all__ = ["ISO8601Model"]
