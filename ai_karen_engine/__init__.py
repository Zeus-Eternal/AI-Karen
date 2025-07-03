from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

src_path = Path(__file__).resolve().parent.parent / 'src' / 'ai_karen_engine'
if src_path.exists():
    spec = spec_from_file_location('src.ai_karen_engine', src_path / '__init__.py')
    module = module_from_spec(spec)
    sys.modules['src.ai_karen_engine'] = module
    spec.loader.exec_module(module)
    globals().update(module.__dict__)
    __path__ = [str(src_path)]


