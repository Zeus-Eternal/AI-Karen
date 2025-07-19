from __future__ import annotations
from typing import Any


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
