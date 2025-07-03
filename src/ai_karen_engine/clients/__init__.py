"""Client utilities and adapters."""

import importlib
import sys

for _sub in ["transformers", "nlp"]:
    try:
        sys.modules[f"ai_karen_engine.clients.{_sub}"] = importlib.import_module(f"src.clients.{_sub}")
    except ModuleNotFoundError:
        pass
