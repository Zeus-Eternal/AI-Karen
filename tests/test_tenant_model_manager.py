from pathlib import Path

import pytest

from ai_karen_engine.core import model_manager
from ai_karen_engine.core.model_manager import ModelManager, LicenseError


def test_tenant_create_and_delete(tmp_path: Path, monkeypatch) -> None:
    license_file = tmp_path / "lic.json"
    license_file.write_text('{"licensee": "x", "valid": true}')
    monkeypatch.setattr(model_manager, "LICENSE_PATH", license_file)
    mm = ModelManager(base_dir=tmp_path / "cache")
    mm.create_tenant("t1")
    mm.create_tenant("t2")
    assert sorted(mm.list_tenants()) == ["t1", "t2"]
    mm.delete_tenant("t1")
    assert mm.list_tenants() == ["t2"]


def test_license_enforced(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(model_manager, "LICENSE_PATH", tmp_path / "missing.json")
    with pytest.raises(LicenseError):
        ModelManager(base_dir=tmp_path / "cache")
