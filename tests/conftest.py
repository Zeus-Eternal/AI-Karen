"""Shared pytest configuration."""
import importlib
import sys

# Alias installed-style packages for tests
sys.modules.setdefault("ai_karen_engine", importlib.import_module("src.ai_karen_engine"))
sys.modules.setdefault("ui_logic", importlib.import_module("src.ui_logic"))
sys.modules.setdefault("services", importlib.import_module("ai_karen_engine.services"))