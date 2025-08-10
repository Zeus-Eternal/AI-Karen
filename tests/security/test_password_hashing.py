import importlib
import pathlib
import types
import sys

import pytest

# Create stub packages to import core without executing package __init__
repo_root = pathlib.Path(__file__).resolve().parents[2]
engine_path = repo_root / 'src' / 'ai_karen_engine'
auth_path = engine_path / 'auth'

engine_pkg = types.ModuleType('ai_karen_engine')
engine_pkg.__path__ = [str(engine_path)]
auth_pkg = types.ModuleType('ai_karen_engine.auth')
auth_pkg.__path__ = [str(auth_path)]

sys.modules.setdefault('ai_karen_engine', engine_pkg)
sys.modules.setdefault('ai_karen_engine.auth', auth_pkg)

core = importlib.import_module('ai_karen_engine.auth.core')
PasswordHasher = core.PasswordHasher


@pytest.mark.parametrize("algorithm", ["bcrypt", "argon2"])
def test_password_hashing_algorithms(algorithm):
    hasher = PasswordHasher(rounds=6, algorithm=algorithm)
    password = "StrongPassw0rd!"
    hashed = hasher.hash_password(password)
    assert hasher.verify_password(password, hashed)
    assert not hasher.verify_password("wrong", hashed)
