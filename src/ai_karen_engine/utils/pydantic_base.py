from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ISO8601Model(BaseModel):
    """Base model with automatic ISO 8601 datetime serialization."""

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


__all__ = ["ISO8601Model"]
