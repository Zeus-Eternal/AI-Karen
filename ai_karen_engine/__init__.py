import importlib
import sys
_module = importlib.import_module('src.ai_karen_engine')
sys.modules[__name__] = _module
