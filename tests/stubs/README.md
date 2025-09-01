# Test Stubs

This package provides minimal stand-ins for optional external
libraries that are either heavyweight or unavailable in the CI
environment. The stubs are automatically injected in
`tests/conftest.py` and should only cover the small surface that the
unit tests exercise.

## Available stubs

- `duckdb.py` – in-memory replacement for DuckDB's `connect` function
  used by memory management tests.
- `pyautogui.py` – prevents import errors when GUI automation packages
  are missing. Only defines the attributes referenced in tests.

If additional behaviour is required in tests, prefer using
`monkeypatch` or fixtures over adding new stub modules.
