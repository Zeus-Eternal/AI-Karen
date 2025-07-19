"""scikit-learn intent classifier."""

from pathlib import Path
from typing import List, Tuple
import logging

try:
    import joblib
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:  # pragma: no cover - optional dep
    joblib = np = LogisticRegression = TfidfVectorizer = None
import json


logger = logging.getLogger(__name__)


class BasicClassifier:
    def __init__(self, model_dir: Path):
        if any(
            dep is None for dep in (joblib, np, LogisticRegression, TfidfVectorizer)
        ):
            raise RuntimeError("scikit-learn is required for BasicClassifier")
        self.model_path = model_dir / "classifier.joblib"
        self.vector_path = model_dir / "vectorizer.joblib"
        model_dir.mkdir(parents=True, exist_ok=True)

        if self.model_path.exists() and self.vector_path.exists():
            self.clf = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vector_path)
        else:
            logger.warning(
                "[BasicClassifier] ⚠️ No model found. Attempting to train from default data."
            )
            default_data = self._load_bootstrap_data()
            if default_data:
                texts = [d["text"] for d in default_data]
                labels = [d["intent"] for d in default_data]
                self.fit(texts, labels)
            else:
                self.clf, self.vectorizer = None, None

    def fit(self, texts: List[str], labels: List[str]):
        self.vectorizer = TfidfVectorizer(max_features=25000, ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(texts)
        self.clf = LogisticRegression(max_iter=1000).fit(X, labels)
        joblib.dump(self.clf, self.model_path)
        joblib.dump(self.vectorizer, self.vector_path)

    def predict(self, text: str) -> Tuple[str, float]:
        X = self.vectorizer.transform([text])
        proba = self.clf.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        return self.clf.classes_[idx], float(proba[idx])

    def _load_bootstrap_data(self):
        # fallback training if user data is missing
        try:
            with open("data/bootstrap/classifier_seed.json") as f:
                return json.load(f)
        except Exception:
            logger.warning("[BasicClassifier] ❌ No bootstrap data found.")
            return []
