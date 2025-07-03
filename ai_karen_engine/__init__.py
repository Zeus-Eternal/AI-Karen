import importlib.util
import pathlib
import types
import sys

_pkg_path = pathlib.Path(__file__).resolve().parent.parent / 'src' / 'ai_karen_engine'
_spec = importlib.util.spec_from_file_location('src.ai_karen_engine', _pkg_path / '__init__.py')
module = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(module)  # type: ignore
sys.modules.setdefault(__name__, module)
for k, v in module.__dict__.items():
    if k not in globals():
        globals()[k] = v
__path__ = [_pkg_path.as_posix()]
