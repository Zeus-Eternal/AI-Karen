"""
Pydantic stub file for type checking when pydantic is not available.
This provides minimal BaseModel and Field implementations for Pylance.
"""

from typing import Any, Dict, List, Optional, Union, Callable


class BaseModel:
    """Stub BaseModel class for type checking."""
    
    def __init_subclass__(cls, **kwargs):
        """Initialize subclass to ensure proper inheritance."""
        super().__init_subclass__(**kwargs)
    
    def __init__(self, **data):
        """Initialize with provided data."""
        for key, value in data.items():
            setattr(self, key, value)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_'):
                attr_value = getattr(self, attr_name)
                if not callable(attr_value):
                    result[attr_name] = attr_value
        return result


class Field:
    """Stub Field class for type checking."""
    
    def __init__(
        self,
        default: Any = None,
        default_factory: Optional[Callable[[], Any]] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """Initialize field with default value and factory."""
        self.default = default
        self.default_factory = default_factory
        self.description = description