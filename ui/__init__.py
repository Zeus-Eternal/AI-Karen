import importlib
import sys
_module = importlib.import_module('src.ui_logic')
sys.modules[__name__] = _module
