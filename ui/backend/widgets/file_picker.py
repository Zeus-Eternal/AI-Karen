"""Simple file picker stub."""

from pathlib import Path


def select_file(prompt: str = "Choose a file") -> Path:
    """Return a dummy file path for demo purposes."""
    return Path("/tmp/dummy.txt")
