from __future__ import annotations
from typing import Any, Optional, Union
from enum import Enum


class ValidationError(Exception):
    """Pydantic validation error stub."""
    pass


def Field(
    default: Any = ...,
    *,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    examples: Optional[list] = None,
    exclude: Optional[bool] = None,
    include: Optional[bool] = None,
    discriminator: Optional[str] = None,
    json_schema_extra: Optional[dict] = None,
    frozen: Optional[bool] = None,
    validate_default: Optional[bool] = None,
    repr: bool = True,
    init_var: Optional[bool] = None,
    kw_only: Optional[bool] = None,
    pattern: Optional[str] = None,
    strict: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    allow_inf_nan: Optional[bool] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    **kwargs: Any,
) -> Any:
    """Pydantic Field stub - returns the default value or ellipsis."""
    return default if default is not ... else None


class BaseModel:
    def __init__(self, **data: Any) -> None:
        for k, v in data.items():
            setattr(self, k, v)

    def dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return self.__dict__.copy()

    # Pydantic v2 compatible name
    def model_dump(self) -> dict[str, Any]:
        return self.dict()

# Simple ConfigDict replacement
class ConfigDict(dict):
    """Pydantic ConfigDict stub."""
    pass

# Simple decorator for validators (no-op)
def validator(*fields, **kwargs):
    def decorator(func):
        return func
    return decorator

# Pydantic v2 field validator (no-op)
def field_validator(*fields, **kwargs):
    def decorator(func):
        return func
    return decorator

# Create model function (stub)
def create_model(model_name: str, **field_definitions: Any) -> type:
    """Create a dynamic model (stub implementation)."""
    class DynamicModel(BaseModel):
        pass
    
    DynamicModel.__name__ = model_name
    return DynamicModel
