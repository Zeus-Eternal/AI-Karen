"""Utility helpers used by the mobile UI to ensure optional ML libraries.

This module is unrelated to ``LLMUtils``; it simply verifies that small
dependencies like spaCy models or scikit-learn are installed so the
Streamlit interface works out of the box.
"""

import importlib.util
import subprocess
from pathlib import Path


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


def ensure_distilbert() -> None:
    """Download DistilBERT base model if missing."""
    try:
        from huggingface_hub import snapshot_download
    except Exception:
        return
    target = Path("models/distilbert-base-uncased")
    if target.exists():
        return
    snapshot_download(
        repo_id="distilbert-base-uncased",
        local_dir=target,
        local_dir_use_symlinks=False,
    )


def ensure_basic_classifier() -> None:
    """Train a tiny intent classifier if none is present."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.feature_extraction.text import TfidfVectorizer
        import joblib
    except Exception:
        return
    model_dir = Path("models/basic_cls")
    model_path = model_dir / "classifier.joblib"
    if model_path.exists():
        return
    texts = [
        "hello",
        "hi",
        "goodbye",
        "bye",
        "thanks",
        "thank you",
    ]
    labels = [
        "greet",
        "greet",
        "farewell",
        "farewell",
        "thanks",
        "thanks",
    ]
    vect = TfidfVectorizer(max_features=1000)
    X = vect.fit_transform(texts)
    clf = LogisticRegression(max_iter=1000).fit(X, labels)
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_dir / "classifier.joblib")
    joblib.dump(vect, model_dir / "vectorizer.joblib")
