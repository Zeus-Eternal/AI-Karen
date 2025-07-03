"""Download and manage per-user models via HuggingFace."""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List

try:
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover - optional dep
    snapshot_download = None

DEFAULT_CACHE = Path(os.getenv("KARI_MODEL_CACHE", "data/users"))


class ModelManager:
    """Simple registry for user-scoped models."""

    def __init__(self, base_dir: Path = DEFAULT_CACHE) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # Public API ---------------------------------------------------------
    def download_model(self, model_name: str, user_id: str, revision: str = "main") -> Path:
        """Download a model from HuggingFace or return cached path."""
        dest = self._user_model_dir(user_id, model_name)
        if dest.exists():
            return dest
        if snapshot_download is None:
            raise RuntimeError("huggingface_hub is required for model download")
        snapshot_download(repo_id=model_name, revision=revision, local_dir=dest, local_dir_use_symlinks=False)
        return dest

    def list_models(self, user_id: str) -> List[str]:
        """List cached models for ``user_id``."""
        user_root = self.base_dir / user_id / "model"
        if not user_root.exists():
            return []
        return [p.name for p in user_root.iterdir() if p.is_dir()]

    def delete_model(self, user_id: str, model_name: str) -> None:
        """Remove a cached model."""
        target = self._user_model_dir(user_id, model_name)
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)

    # Helpers ------------------------------------------------------------
    def _user_model_dir(self, user_id: str, model_name: str) -> Path:
        return self.base_dir / user_id / "model" / model_name
