import ast
from pathlib import Path
import types

import pytest
from ai_karen_engine.pydantic_stub import Field, ValidationError
from tests.stubs.pydantic_settings import BaseSettings, SettingsConfigDict


def test_missing_database_url_fails_fast(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    source = Path("main.py").read_text()
    tree = ast.parse(source)
    class_node = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Settings"
    )
    module = types.ModuleType("tmp_settings")
    module.BaseSettings = BaseSettings
    module.SettingsConfigDict = SettingsConfigDict
    module.Field = Field
    module.ValidationError = ValidationError
    exec(
        compile(ast.Module(body=[class_node], type_ignores=[]), "main.py", "exec"),
        module.__dict__,
    )
    Settings = module.Settings
    with pytest.raises(ValidationError):
        Settings()
