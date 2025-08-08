import ast
import sys
from pathlib import Path

import pytest
from pydantic_core import ValidationError


def _load_settings_class():
    source = Path("main.py").read_text()
    module = ast.parse(source)
    settings_node = next(
        node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "Settings"
    )
    settings_module = ast.Module(body=[settings_node], type_ignores=[])
    namespace: dict = {}
    sys.modules.pop("pydantic", None)
    sys.modules.pop("pydantic_settings", None)
    exec(
        "from pydantic_settings import BaseSettings, SettingsConfigDict\nfrom pydantic import Field",
        namespace,
    )
    exec(compile(settings_module, "<settings>", "exec"), namespace)
    return namespace["Settings"]


def test_missing_database_url_raises_validation_error(monkeypatch):
    """The server should fail fast if DATABASE_URL is undefined."""
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    Settings = _load_settings_class()
    with pytest.raises(ValidationError):
        Settings()

