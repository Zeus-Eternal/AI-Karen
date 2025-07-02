import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]  # AI-Karen root
SRC_PATH = PROJECT_ROOT / "src"

# Ensure both the project root and ``src`` directory are importable before any
# submodules within ``ui.mobile_ui`` are loaded. Streamlit eagerly imports
# components, so ``sys.path`` must be patched at package import time.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
