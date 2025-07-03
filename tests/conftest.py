"""Shared pytest configuration."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
for p in (ROOT, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
