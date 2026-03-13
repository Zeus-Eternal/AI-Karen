"""
Pydantic stub module for fallback imports when pydantic is not available.
This provides minimal implementations to allow the code to run.
"""

from typing import Any, Dict, Optional, Union, Callable, List, Type
import json
from datetime import datetime


class ValidationError(Exception):
    """Stub implementation of pydantic.ValidationError."""
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.errors = errors or []


class _Field:
    """Stub implementation of pydantic.Field."""
    def __init__(
        self,
        default: Any = None,
        default_factory: Optional[Callable] = None,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        self.default = default
        self.default_factory = default_factory
        self.alias = alias
        self.title = title
        self.description = description
        self.kwargs = kwargs
    
    def __repr__(self):
        return f"Field(default={self.default}, default_factory={self.default_factory})"


def Field(
    default: Any = None,
    default_factory: Optional[Callable] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
):
    """Create a field with metadata."""
    return _Field(
        default=default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        **kwargs
    )


class ConfigDict:
    """Stub implementation of pydantic.ConfigDict."""
    def __init__(self, **kwargs):
        self.extra = kwargs.get('extra', 'forbid')
        self.validate_assignment = kwargs.get('validate_assignment', False)
        self.arbitrary_types_allowed = kwargs.get('arbitrary_types_allowed', False)
        self.populate_by_name = kwargs.get('populate_by_name', False)


def field_validator(field_name: str, mode: str = 'after'):
    """Stub implementation of pydantic.field_validator."""
    def decorator(func: Callable):
        return func
    return decorator


def model_validator(mode: str = 'after'):
    """Stub implementation of pydantic.model_validator."""
    def decorator(func: Callable):
        return func
    return decorator


def validator(field_name: str, mode: str = 'after'):
    """Stub implementation of pydantic.validator (v1 style)."""
    def decorator(func: Callable):
        return func
    return decorator


def field_serializer(field_name: str):
    """Stub implementation of pydantic.field_serializer."""
    def decorator(func: Callable):
        return func
    return decorator


class BaseModel:
    """Stub implementation of pydantic.BaseModel."""
    
    model_config = ConfigDict()
    
    def __init_subclass__(cls, **kwargs):
        """Initialize subclass to ensure proper inheritance."""
        super().__init_subclass__(**kwargs)
    
    def __init__(self, **data):
        """Initialize the model with data."""
        # Set provided data
        for key, value in data.items():
            setattr(self, key, value)
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Stub implementation of model_dump."""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if hasattr(value, 'model_dump'):
                    result[key] = value.model_dump(**kwargs)
                elif isinstance(value, (list, dict)):
                    result[key] = value
                else:
                    result[key] = value
        return result
    
    def dict(self, **kwargs) -> Dict[str, Any]:
        """Legacy method for compatibility."""
        return self.model_dump(**kwargs)
    
    def model_dump_json(self, **kwargs) -> str:
        """Stub implementation of model_dump_json."""
        return json.dumps(self.model_dump(**kwargs))
    
    def json(self, **kwargs) -> str:
        """Legacy method for compatibility."""
        return self.model_dump_json(**kwargs)
    
    @classmethod
    def model_validate(cls, data: Dict[str, Any], **kwargs):
        """Stub implementation of model_validate."""
        instance = cls.__new__(cls)
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
    
    @classmethod
    def parse_obj(cls, data: Dict[str, Any]):
        """Legacy method for compatibility."""
        return cls.model_validate(data)
    
    def model_rebuild(self, **kwargs):
        """Stub implementation of model_rebuild."""
        pass


class BaseSettings(BaseModel):
    """Stub implementation of pydantic.BaseSettings."""
    
    def __init__(self, **data):
        super().__init__(**data)


# Version info
__version__ = "2.0.0"