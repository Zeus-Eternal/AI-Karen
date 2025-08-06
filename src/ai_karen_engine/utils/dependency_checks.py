"""Utilities for optional dependency imports.

These helpers centralize the import and validation of optional runtime
dependencies such as FastAPI and Pydantic. They return the requested
attributes from those packages or raise informative errors when the
packages are not installed.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Tuple


def _import_package(package: str, message: str) -> Any:
    try:  # pragma: no cover - runtime dependency
        return import_module(package)
    except ImportError as e:  # pragma: no cover - runtime dependency
        raise ImportError(message) from e


def import_fastapi(*names: str) -> Tuple[Any, ...] | Any:
    """Import components from ``fastapi`` with a helpful error message."""

    module = _import_package(
        "fastapi",
        "FastAPI is required for API routes. Install via `pip install fastapi`.",
    )
    return _resolve_names(module, names)


def import_pydantic(*names: str) -> Tuple[Any, ...] | Any:
    """Import components from ``pydantic`` with a helpful error message."""

    module = _import_package(
        "pydantic",
        "Pydantic is required for API routes. Install via `pip install pydantic`.",
    )
    return _resolve_names(module, names)


def _resolve_names(module: Any, names: Tuple[str, ...]) -> Tuple[Any, ...] | Any:
    if not names:
        return module
    resolved = tuple(getattr(module, name) for name in names)
    return resolved[0] if len(resolved) == 1 else resolved


__all__ = ["import_fastapi", "import_pydantic"]
