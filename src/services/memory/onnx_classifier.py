"""
ONNX Runtime Classifier Service
A lightweight, lightning-fast text classification engine designed to replace
heavy HuggingFace transformers pipelines.

Usage:
Requires an exported `model.onnx` and `tokenizer.json` to be placed in the model directory.
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional

try:
    import onnxruntime as ort
    from tokenizers import Tokenizer
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = Any
    Tokenizer = Any

logger = logging.getLogger(__name__)

class ONNXClassifier:
    """Wrapper for fast distilbert ONNX sequence classification."""
    
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.session: Optional['ort.InferenceSession'] = None
        self.tokenizer: Optional['Tokenizer'] = None
        
        self.model_path = os.path.join(model_dir, "model.onnx")
        self.tokenizer_path = os.path.join(model_dir, "tokenizer.json")

    def load(self) -> bool:
        """Lazily load the ONNX session and Rust tokenizer."""
        if not ONNX_AVAILABLE:
            logger.error("onnxruntime or tokenizers not installed.")
            return False
            
        if not os.path.exists(self.model_path) or not os.path.exists(self.tokenizer_path):
            logger.warning(f"ONNX files missing in {self.model_dir}. Need model.onnx and tokenizer.json.")
            return False

        if self.session is None:
            try:
                # Use CPUExecutionProvider by default for max compatibility on classifiers
                self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                self.tokenizer = Tokenizer.from_file(self.tokenizer_path)
                logger.info(f"Successfully loaded ONNX classifier from {self.model_dir}")
            except Exception as e:
                logger.error(f"Failed to load ONNX model: {e}")
                return False
                
        return True

    def predict(self, text: str) -> Dict[str, Any]:
        """Run classification inference purely in C++/Rust."""
        if not self.load():
            return {"error": "Model not loaded"}
            
        t0 = time.time()
        
        # Fast Rust-based tokenization
        encoded = self.tokenizer.encode(text)
        
        # ONNX inputs expect numpy arrays
        import numpy as np
        inputs = {
            "input_ids": np.array([encoded.ids], dtype=np.int64),
            "attention_mask": np.array([encoded.attention_mask], dtype=np.int64)
        }
        
        # Run inference loop
        try:
            outputs = self.session.run(None, inputs)
            logits = outputs[0][0]
            
            # Simple softmax for confidence
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()
            
            prediction = int(np.argmax(probs))
            confidence = float(probs[prediction])
            
            return {
                "prediction": prediction,
                "confidence": confidence,
                "latency_ms": (time.time() - t0) * 1000
            }
        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")
            return {"error": str(e)}
