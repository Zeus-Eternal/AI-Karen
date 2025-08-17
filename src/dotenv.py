"""Minimal stub for python-dotenv used in tests.

Provides the small subset of the ``python-dotenv`` API required by the
codebase. Only ``load_dotenv`` and ``dotenv_values`` are implemented and
they intentionally perform no I/O, returning empty results instead.
"""

from typing import Dict


def load_dotenv(*_args, **_kwargs) -> bool:
    return False


def dotenv_values(*_args, **_kwargs) -> Dict[str, str]:
    """Return an empty mapping of environment variables."""
    return {}
