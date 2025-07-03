"""Multi-tenant model manager with license enforcement."""
from __future__ import annotations
import json
import os
import shutil
from pathlib import Path
from typing import List

LICENSE_PATH = Path("contracts/license.json")
DEFAULT_CACHE = Path(os.getenv("KARI_MODEL_CACHE", "data/tenants"))


class LicenseError(Exception):
    """Raised when the license file is missing or invalid."""


class ModelManager:
    """Handle per-tenant model downloads and local caching."""

    DEFAULT_TENANT = "default"

    def __init__(self, base_dir: Path = DEFAULT_CACHE) -> None:
        self.base_dir = Path(base_dir)
        self._check_license()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # Tenant -----------------------------------------------------------------
    def create_tenant(self, tenant_id: str) -> Path:
        path = self.base_dir / tenant_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def delete_tenant(self, tenant_id: str) -> None:
        path = self.base_dir / tenant_id
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def list_tenants(self) -> List[str]:
        if not self.base_dir.exists():
            return []
        return [p.name for p in self.base_dir.iterdir() if p.is_dir()]

    # Public API -------------------------------------------------------------
    def download_model(
        self,
        model_name: str,
        user_id: str,
        tenant_id: str | None = None,
        revision: str = "main",
    ) -> Path:
        """Download a model or return cached path."""
        tenant = tenant_id or self.DEFAULT_TENANT
        dest = self._user_model_dir(tenant, user_id, model_name)
        if dest.exists():
            return dest
        try:
            from huggingface_hub import snapshot_download
        except Exception as exc:  # pragma: no cover - optional dep
            raise RuntimeError("huggingface_hub is required for model download") from exc
        snapshot_download(repo_id=model_name, revision=revision, local_dir=dest, local_dir_use_symlinks=False)
        return dest

    def list_models(self, user_id: str, tenant_id: str | None = None) -> List[str]:
        tenant = tenant_id or self.DEFAULT_TENANT
        user_root = self.base_dir / tenant / user_id / "model"
        
        if not user_root.exists():
            return []
        return [p.name for p in user_root.iterdir() if p.is_dir()]
    
    def delete_model(self, user_id: str, model_name: str, tenant_id: str | None = None) -> None:
        tenant = tenant_id or self.DEFAULT_TENANT
        target = self._user_model_dir(tenant, user_id, model_name)
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)

    # Helpers ----------------------------------------------------------------
    def _user_model_dir(self, tenant: str, user_id: str, model_name: str) -> Path:
        return self.base_dir / tenant / user_id / "model" / model_name

    def _check_license(self) -> None:
        if not LICENSE_PATH.exists():
            raise LicenseError("Valid license file not found")
        try:
            data = json.loads(LICENSE_PATH.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - unlikely
            raise LicenseError("Malformed license file") from exc
        if not data.get("valid"):
            raise LicenseError("License is no longer valid")
            
