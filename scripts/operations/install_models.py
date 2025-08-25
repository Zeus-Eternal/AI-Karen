#!/usr/bin/env python
"""Download base NLP models if missing."""

from pathlib import Path
import sys
import subprocess


def ensure_distilbert() -> None:
    try:
        from huggingface_hub import snapshot_download
    except Exception:
        print("huggingface_hub is required to download DistilBERT", file=sys.stderr)
        return
    target = Path("models/distilbert-base-uncased")
    if target.exists():
        return
    snapshot_download(
        repo_id="distilbert-base-uncased",
        local_dir=target,
        local_dir_use_symlinks=False,
    )


def ensure_spacy() -> None:
    try:
        import spacy
    except Exception:
        print("spaCy not installed", file=sys.stderr)
        return
    model = "en_core_web_trf"
    try:
        spacy.load(model)
    except OSError:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", model])


def ensure_basic_classifier() -> None:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.feature_extraction.text import TfidfVectorizer
        import joblib
    except Exception:
        print("scikit-learn not installed", file=sys.stderr)
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


def main() -> None:
    ensure_distilbert()
    ensure_spacy()
    ensure_basic_classifier()


if __name__ == "__main__":
    main()
