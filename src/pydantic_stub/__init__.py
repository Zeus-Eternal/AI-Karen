"""Tiny Pydantic ``BaseModel`` stub for optional dependency use."""

from typing import Any


class BaseModel:
    def __init__(self, **data: Any) -> None:
        for k, v in data.items():
            setattr(self, k, v)
