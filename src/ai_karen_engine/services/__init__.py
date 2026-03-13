"""
Compatibility shim for legacy imports.

Historically modules were imported from ai_karen_engine.services.*, but the
implementations now live under the top-level services package. This module
aliases ai_karen_engine.services to services so existing import paths continue
to work without touching all call sites.
"""

import importlib
import sys

# Re-export the concrete services package
_services = importlib.import_module("services")

# Register alias so submodules resolve (e.g., ai_karen_engine.services.foo)
sys.modules[__name__] = _services
