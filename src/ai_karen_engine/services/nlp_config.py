"""
Configuration models for NLP services (spaCy and DistilBERT).
"""

from __future__ import annotations

import os
from typing import List, Optional
try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field


class SpacyConfig(BaseModel):
    """Configuration for spaCy service."""
    
    def __init__(self, **data):
        # Get model name from configuration manager or fallback to environment/default
        model_name = "en_core_web_sm"
        try:
            from ai_karen_engine.core.config_manager import get_config
            config = get_config()
            model_name = config.spacy_model
        except Exception:
            # Fallback to environment variable or default
            model_name = os.getenv("SPACY_MODEL", "en_core_web_sm")
        
        # Set defaults - enable parser for dependency parsing as required by task 3.2
        defaults = {
            "model_name": model_name,
            "disabled_components": ["textcat"],  # Keep parser enabled for dependency parsing
            "enable_fallback": True,
            "cache_size": 1000,
            "cache_ttl": 3600,
            "download_missing": True
        }
        defaults.update(data)
        super().__init__(**defaults)
    
    model_name: str = "en_core_web_sm"
    disabled_components: List[str] = ["textcat"]  # Keep parser enabled for dependency parsing
    enable_fallback: bool = True
    cache_size: int = 1000
    cache_ttl: int = 3600
    download_missing: bool = True


class DistilBertConfig(BaseModel):
    """Configuration for DistilBERT service."""
    
    def __init__(self, **data):
        # Set defaults
        defaults = {
            "model_name": os.getenv("TRANSFORMER_MODEL", "distilbert-base-uncased"),
            "max_length": 512,
            "batch_size": 32,
            "enable_gpu": True,
            "enable_fallback": True,
            "cache_size": 5000,
            "cache_ttl": 7200,
            "embedding_dimension": 768,
            "pooling_strategy": "mean"
        }
        defaults.update(data)
        super().__init__(**defaults)
    
    model_name: str = "distilbert-base-uncased"
    max_length: int = 512
    batch_size: int = 32
    enable_gpu: bool = True
    enable_fallback: bool = True
    cache_size: int = 5000
    cache_ttl: int = 7200
    embedding_dimension: int = 768
    pooling_strategy: str = "mean"


class NLPConfig(BaseModel):
    """Combined NLP configuration."""
    
    def __init__(self, **data):
        # Set defaults
        defaults = {
            "spacy": SpacyConfig(),
            "distilbert": DistilBertConfig(),
            "enable_monitoring": True,
            "health_check_interval": 60,
            "retry_attempts": 3,
            "retry_backoff_factor": 2.0
        }
        
        # Handle nested config objects
        for key, value in data.items():
            if key == "spacy" and isinstance(value, dict):
                defaults[key] = SpacyConfig(**value)
            elif key == "distilbert" and isinstance(value, dict):
                defaults[key] = DistilBertConfig(**value)
            else:
                defaults[key] = value
        
        super().__init__(**defaults)
    
    spacy: SpacyConfig = None
    distilbert: DistilBertConfig = None
    enable_monitoring: bool = True
    health_check_interval: int = 60
    retry_attempts: int = 3
    retry_backoff_factor: float = 2.0