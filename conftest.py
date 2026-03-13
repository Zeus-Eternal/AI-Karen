import os
import sys

# Ensure `src` is on sys.path so tests can import packages under `src/`.
# This is useful for local development and CI where editable install isn't used.
ROOT = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT, "src")
if os.path.isdir(SRC_DIR) and SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
