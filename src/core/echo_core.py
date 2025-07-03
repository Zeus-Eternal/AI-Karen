"""Fine-tune DistilBERT models on interaction logs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

try:
    import torch
except Exception:  # pragma: no cover - optional dep
    torch = None
try:
    from datasets import Dataset
except Exception:  # pragma: no cover - optional dep
    Dataset = None
try:
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        Trainer,
        TrainingArguments,
    )
except Exception:  # pragma: no cover - optional dep
    AutoTokenizer = AutoModelForSequenceClassification = Trainer = TrainingArguments = None

from .model_manager import ModelManager


class EchoCore:
    """Personalized fine-tuning engine."""

    def __init__(self, user_id: str, model_name: str = "distilbert-base-uncased") -> None:
        self.user_id = user_id
        self.model_name = model_name
        self.mm = ModelManager()
        if AutoTokenizer is None:
            raise RuntimeError("transformers is required for EchoCore")
        self.model_path = self.mm.download_model(model_name, user_id)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        if torch:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = "cpu"

    # Fine-tuning --------------------------------------------------------
    def fine_tune(self, interactions_path: Path, epochs: int = 3) -> None:
        """Fine-tune on a JSON list of {text, intent}."""
        if torch is None:
            raise RuntimeError("PyTorch is required for fine-tuning")
        data = self._load_interactions(interactions_path)
        dataset = self._build_dataset(data)
        num_labels = len(dataset.features["label"].names)
        if AutoModelForSequenceClassification is None:
            raise RuntimeError("transformers is required for fine-tuning")
        model = AutoModelForSequenceClassification.from_pretrained(
            self.model_path, num_labels=num_labels
        )
        if torch:
            model = model.to(self.device)

        if TrainingArguments is None or Trainer is None:
            raise RuntimeError("transformers training utilities are required")
        args = TrainingArguments(
            output_dir=str(self.model_path / "checkpoints"),
            per_device_train_batch_size=16,
            num_train_epochs=epochs,
            learning_rate=5e-5,
            save_total_limit=2,
            logging_steps=50,
            report_to="none",
            remove_unused_columns=True,
        )
        trainer = Trainer(model=model, args=args, train_dataset=dataset)
        trainer.train()

        model.save_pretrained(self.model_path)
        self.tokenizer.save_pretrained(self.model_path)

    # Helpers ------------------------------------------------------------
    def _load_interactions(self, path: Path) -> List[Dict[str, str]]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_dataset(self, data: List[Dict[str, str]]) -> Dataset:
        if Dataset is None:
            raise RuntimeError("datasets library is required for fine-tuning")
        texts, labels = [], []
        label_set = sorted({item["intent"] for item in data})
        label_map = {lbl: idx for idx, lbl in enumerate(label_set)}

        for item in data:
            texts.append(item["text"])
            labels.append(label_map[item["intent"]])

        enc = self.tokenizer(texts, truncation=True, padding=True)
        enc["label"] = labels
        return Dataset.from_dict(enc).cast_column("label", "int64")
