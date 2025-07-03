"""Shared pytest configuration for unit tests."""

import os
import sys
import types

# Ensure src/ and ui/ are importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for path in [BASE_DIR, os.path.join(BASE_DIR, "src")]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Provide a minimal streamlit stub for UI tests
if "streamlit" not in sys.modules:
    stub = types.SimpleNamespace(session_state={}, error=lambda *a, **k: None)
    sys.modules["streamlit"] = stub

if "duckdb" not in sys.modules:
    class _Conn:
        def execute(self, *_args, **_kwargs):
            return self

        def fetchone(self):
            return (1,)

        def fetchall(self):
            return []

        def close(self):
            pass

    class _DuckDB:
        def connect(self, *_args, **_kwargs):
            return _Conn()

    sys.modules["duckdb"] = _DuckDB()

if "pymilvus" not in sys.modules:
    class _Connections:
        def connect(self, **_kwargs):
            pass

        def get_connection(self, *_args, **_kwargs):
            return self

        def list_collections(self):
            return []

        def disconnect(self, *_args, **_kwargs):
            pass

    sys.modules["pymilvus"] = types.SimpleNamespace(connections=_Connections())

# FastAPI and Pydantic stubs
import src.fastapi_stub as fastapi_stub
import src.pydantic_stub as pydantic_stub
sys.modules.setdefault("fastapi", fastapi_stub)
sys.modules.setdefault("fastapi.responses", fastapi_stub.responses)
sys.modules.setdefault("fastapi.testclient", fastapi_stub)
sys.modules.setdefault("pydantic", pydantic_stub)

if "cryptography" not in sys.modules:
    class _Fernet:
        @staticmethod
        def generate_key() -> bytes:
            return b"0" * 32

        def __init__(self, *_a, **_k):
            pass

        def encrypt(self, b: bytes) -> bytes:
            return b

        def decrypt(self, b: bytes) -> bytes:
            return b

    fernet_mod = types.ModuleType("cryptography.fernet")
    fernet_mod.Fernet = _Fernet
    crypto_mod = types.ModuleType("cryptography")
    crypto_mod.fernet = fernet_mod
    sys.modules["cryptography"] = crypto_mod
    sys.modules["cryptography.fernet"] = fernet_mod

