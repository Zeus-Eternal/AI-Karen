"""scikit-learn intent classifier."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

try:
    import joblib
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
except Exception:  # pragma: no cover - optional dep
    joblib = np = TfidfVectorizer = LogisticRegression = None

MODEL_FILE = "classifier.joblib"
VECT_FILE = "vectorizer.joblib"


class BasicClassifier:
    """Tiny TF-IDF + LogisticRegression model."""

    def __init__(self, model_dir: Path, auto_init: bool = True) -> None:
        if any(dep is None for dep in (joblib, np, TfidfVectorizer, LogisticRegression)):
            raise RuntimeError("scikit-learn is required for BasicClassifier")
        self.model_path = model_dir / MODEL_FILE
        self.vector_path = model_dir / VECT_FILE
        if self.model_path.exists():
            self.clf = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vector_path)
        else:
            self.clf = None
            self.vectorizer = None
            if auto_init:
                self._train_default()

    def fit(self, texts: List[str], labels: List[str]) -> None:
        self.vectorizer = TfidfVectorizer(max_features=25_000, ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(texts)
        self.clf = LogisticRegression(max_iter=1_000).fit(X, labels)
        self._save()

    def predict(self, text: str) -> Tuple[str, float]:
        X = self.vectorizer.transform([text])
        proba = self.clf.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        return self.clf.classes_[idx], float(proba[idx])

    def _save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.clf, self.model_path)
        joblib.dump(self.vectorizer, self.vector_path)

    def _train_default(self) -> None:
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
        self.fit(texts, labels)
