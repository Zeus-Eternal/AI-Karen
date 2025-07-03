"""Utility helpers used by the mobile UI to ensure optional ML libraries.

This module is unrelated to ``LLMUtils``; it simply verifies that small
dependencies like spaCy models or scikit-learn are installed so the
Streamlit interface works out of the box.
"""

import importlib.util
import subprocess


def ensure_spacy_models() -> None:
    """Ensure the small English spaCy model is installed."""
    try:
        import spacy
        spacy.load("en_core_web_sm")
    except (OSError, ImportError):
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)


def ensure_sklearn_installed() -> None:
    """Ensure scikit-learn is available."""
    if importlib.util.find_spec("sklearn") is None:
        subprocess.run(["pip", "install", "scikit-learn"], check=True)
