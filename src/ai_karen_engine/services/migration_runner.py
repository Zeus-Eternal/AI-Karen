"""
Migration runner with support for Milvus collections and SQL migrations.
Provides unified migration management for AI-Karen's multi-database architecture.
"""

import logging
import importlib.util
from pathlib import Path
from typing import Dict, Callable

logger = logging.getLogger(__name__)

# Registered Milvus migrations
MILVUS_MIGRATIONS = {
    "001_init": "data/migrations/milvus/001_init.py",
    "002_memory_vectors": "data/migrations/milvus/002_memory_vectors.py", 
    "003_embeddings_index": "data/migrations/milvus/003_embeddings_index.py",
    # New Case-Memory vector collection (task/plan/outcome embeddings)
    "004_case_memory_collection": "data/migrations/milvus/004_case_memory_collection.py",
}

def _load_module(path: str):
    """Load a Python module from file path."""
    spec = importlib.util.spec_from_file_location("migration", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load migration module from {path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_milvus_migrations(direction: str = "up"):
    """
    Iterate through registered Milvus migrations in order and execute
    their up()/down() functions.
    """
    for name, path in MILVUS_MIGRATIONS.items():
        try:
            mod = _load_module(path)
            fn = getattr(mod, direction, None)
            if callable(fn):
                logger.info("Running Milvus migration %s.%s", name, direction)
                fn()
        except Exception as e:
            logger.error("Milvus migration %s failed: %s", name, e, exc_info=True)
            if direction == "up":
                raise

def get_milvus_migrations() -> Dict[str, str]:
    """Get the registry of Milvus migrations."""
    return MILVUS_MIGRATIONS.copy()

__all__ = ["run_milvus_migrations", "get_milvus_migrations", "MILVUS_MIGRATIONS"]
