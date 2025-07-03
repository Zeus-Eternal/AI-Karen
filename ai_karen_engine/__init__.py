from importlib import import_module
from pathlib import Path

package_path = Path(__file__).resolve().parent.parent / 'src' / 'ai_karen_engine'
__path__ = [str(package_path)]

_module = import_module('src.ai_karen_engine')
globals().update(_module.__dict__)
