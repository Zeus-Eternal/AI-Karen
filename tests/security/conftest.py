import os
import sys
import types

# Provide required environment defaults
os.environ.setdefault("KARI_DUCKDB_PASSWORD", "test")
os.environ.setdefault("KARI_JOB_SIGNING_KEY", "test")

# Stub out GUI-related modules to avoid X server dependencies during tests
pyautogui_stub = types.ModuleType("pyautogui")
pyautogui_stub.FAILSAFE = False
sys.modules.setdefault("pyautogui", pyautogui_stub)

mouseinfo_stub = types.ModuleType("mouseinfo")
sys.modules.setdefault("mouseinfo", mouseinfo_stub)
