"""
Custom JSON encoder for FastAPI responses.

This module provides a custom JSON encoder that handles datetime objects
and other non-serializable types properly.
"""

import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from enum import Enum
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and other common types."""
    
    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return obj.__dict__
        
        return super().default(obj)


def custom_json_dumps(obj: Any, **kwargs) -> str:
    """Custom JSON dumps function using our encoder."""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


def custom_json_response_encoder(obj: Any) -> Any:
    """Encoder function for FastAPI JSONResponse."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    
    return obj