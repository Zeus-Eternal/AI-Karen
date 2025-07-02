import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]  # AI-Karen root
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
