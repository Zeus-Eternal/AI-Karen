import importlib
import pathlib
import sys
import types
import pytest

# Prepare minimal package structure to import core module
repo_root = pathlib.Path(__file__).resolve().parents[2]
engine_path = repo_root / "src" / "ai_karen_engine"
auth_path = engine_path / "auth"

engine_pkg = types.ModuleType("ai_karen_engine")
engine_pkg.__path__ = [str(engine_path)]
auth_pkg = types.ModuleType("ai_karen_engine.auth")
auth_pkg.__path__ = [str(auth_path)]

sys.modules.setdefault("ai_karen_engine", engine_pkg)
sys.modules.setdefault("ai_karen_engine.auth", auth_pkg)

core = importlib.import_module("ai_karen_engine.auth.core")
PasswordValidator = core.PasswordValidator


def test_validate_strong_password():
    validator = PasswordValidator(min_length=8, require_complexity=True)
    is_valid, errors = validator.validate_password("StrongPass123!")
    assert is_valid is True
    assert errors == []


def test_validate_weak_password():
    validator = PasswordValidator(min_length=8, require_complexity=True)
    is_valid, errors = validator.validate_password("weak")
    assert is_valid is False
    assert any("at least 8 characters" in e for e in errors)


def test_complexity_requirements():
    validator = PasswordValidator(min_length=8, require_complexity=True)

    is_valid, errors = validator.validate_password("lowercase123!")
    assert not is_valid
    assert any("uppercase" in e for e in errors)

    is_valid, errors = validator.validate_password("UPPERCASE123!")
    assert not is_valid
    assert any("lowercase" in e for e in errors)

    is_valid, errors = validator.validate_password("NoDigits!")
    assert not is_valid
    assert any("digit" in e for e in errors)

    is_valid, errors = validator.validate_password("NoSpecial123")
    assert not is_valid
    assert any("special character" in e for e in errors)
