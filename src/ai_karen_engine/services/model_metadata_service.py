"""
Model Metadata Service

Provides comprehensive model metadata management including:
- Caching mechanism for remote metadata
- Predefined model configurations with TinyLlama examples
- Technical specifications and capabilities management
- Performance metrics and compatibility information

This service integrates with the Enhanced Model Registry to provide
detailed model information for the Model Library feature.
"""

import json
import logging
import os
import time
import hashlib
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .model_registry import ModelMetadata, ModelEntry, Repository

logger = logging.getLogger("kari.model_metadata_service")

@dataclass
class CachedMetadata:
    """Cached metadata with expiration."""
    metadata: ModelMetadata
    cached_at: float
    expires_at: float
    source: str  # 'predefined', 'remote', 'local'

@dataclass
class ModelCapabilities:
    """Detailed model capabilities information."""
    primary_tasks: List[str]
    supported_formats: List[str]
    languages: List[str]
    domains: List[str]
    performance_tier: str  # 'low', 'medium', 'high', 'enterprise'
    hardware_requirements: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Model performance metrics."""
    inference_speed: str  # 'very_slow', 'slow', 'medium', 'fast', 'very_fast'
    memory_efficiency: str  # 'low', 'medium', 'high', 'very_high'
    quality_score: Optional[float] = None  # 0.0 to 1.0
    benchmark_scores: Optional[Dict[str, float]] = None
    tokens_per_second: Optional[float] = None
    memory_usage_mb: Optional[int] = None

class ModelMetadataService:
    """Enhanced service for managing model metadata and capabilities."""
    
    def __init__(self, cache_dir: str = "models/metadata_cache", cache_ttl: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl  # Cache TTL in seconds (default: 24 hours)
        
        # In-memory cache
        self.metadata_cache: Dict[str, CachedMetadata] = {}
        self.capabilities_cache: Dict[str, ModelCapabilities] = {}
        self.performance_cache: Dict[str, PerformanceMetrics] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="metadata_worker")
        
        # Initialize predefined models
        self.predefined_models = self._initialize_predefined_models()
        
        # Load cached data
        self._load_cache()
    
    def _initialize_predefined_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predefined model configurations with comprehensive metadata."""
        return {
            "tinyllama-1.1b-chat-q4": {
                "id": "tinyllama-1.1b-chat-q4",
                "name": "TinyLlama 1.1B Chat Q4_K_M",
                "provider": "llama-cpp",
                "size": 669000000,
                "description": "A compact 1.1B parameter language model optimized for chat applications with Q4_K_M quantization for efficient inference.",
                "capabilities": ["text-generation", "chat", "local-inference", "low-memory"],
                "metadata": ModelMetadata(
                    parameters="1.1B",
                    quantization="Q4_K_M",
                    memory_requirement="~1GB",
                    context_length=2048,
                    license="Apache 2.0",
                    tags=["chat", "small", "efficient", "quantized"],
                    architecture="Llama",
                    training_data="SlimPajama, Starcoderdata",
                    performance_metrics={
                        "inference_speed": "fast",
                        "memory_efficiency": "high",
                        "quality_score": 0.75,
                        "tokens_per_second": 25.0,
                        "memory_usage_mb": 1024
                    }
                ),
                "capabilities_detailed": ModelCapabilities(
                    primary_tasks=["conversational-ai", "text-generation", "question-answering"],
                    supported_formats=["gguf"],
                    languages=["en"],
                    domains=["general", "chat", "assistant"],
                    performance_tier="medium",
                    hardware_requirements={
                        "min_ram_gb": 1,
                        "recommended_ram_gb": 2,
                        "gpu_required": False,
                        "cpu_cores": 2
                    }
                ),
                "performance_metrics": PerformanceMetrics(
                    inference_speed="fast",
                    memory_efficiency="high",
                    quality_score=0.75,
                    benchmark_scores={
                        "hellaswag": 0.59,
                        "arc_challenge": 0.32,
                        "truthfulqa": 0.37
                    },
                    tokens_per_second=25.0,
                    memory_usage_mb=1024
                ),
                "download_info": {
                    "url": "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                    "filename": "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            "tinyllama-1.1b-instruct-q4": {
                "id": "tinyllama-1.1b-instruct-q4",
                "name": "TinyLlama 1.1B Instruct Q4_K_M",
                "provider": "llama-cpp",
                "size": 669000000,
                "description": "TinyLlama model fine-tuned for instruction following with Q4_K_M quantization.",
                "capabilities": ["text-generation", "instruction-following", "local-inference", "low-memory"],
                "metadata": ModelMetadata(
                    parameters="1.1B",
                    quantization="Q4_K_M",
                    memory_requirement="~1GB",
                    context_length=2048,
                    license="Apache 2.0",
                    tags=["instruct", "small", "efficient", "quantized"],
                    architecture="Llama",
                    training_data="SlimPajama, Starcoderdata + Instruction tuning",
                    performance_metrics={
                        "inference_speed": "fast",
                        "memory_efficiency": "high",
                        "instruction_following": "good",
                        "quality_score": 0.78,
                        "tokens_per_second": 25.0,
                        "memory_usage_mb": 1024
                    }
                ),
                "capabilities_detailed": ModelCapabilities(
                    primary_tasks=["instruction-following", "text-generation", "task-completion"],
                    supported_formats=["gguf"],
                    languages=["en"],
                    domains=["general", "instruction", "assistant"],
                    performance_tier="medium",
                    hardware_requirements={
                        "min_ram_gb": 1,
                        "recommended_ram_gb": 2,
                        "gpu_required": False,
                        "cpu_cores": 2
                    }
                ),
                "performance_metrics": PerformanceMetrics(
                    inference_speed="fast",
                    memory_efficiency="high",
                    quality_score=0.78,
                    benchmark_scores={
                        "hellaswag": 0.61,
                        "arc_challenge": 0.34,
                        "truthfulqa": 0.39,
                        "instruction_following": 0.72
                    },
                    tokens_per_second=25.0,
                    memory_usage_mb=1024
                ),
                "download_info": {
                    "url": "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Instruct-v0.1-GGUF/resolve/main/tinyllama-1.1b-instruct-v0.1.Q4_K_M.gguf",
                    "filename": "tinyllama-1.1b-instruct-v0.1.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            # Additional predefined models can be added here
            "phi-2-q4": {
                "id": "phi-2-q4",
                "name": "Microsoft Phi-2 Q4_K_M",
                "provider": "llama-cpp",
                "size": 1600000000,
                "description": "Microsoft's Phi-2 model with 2.7B parameters, optimized for reasoning and code generation.",
                "capabilities": ["text-generation", "code-generation", "reasoning", "local-inference"],
                "metadata": ModelMetadata(
                    parameters="2.7B",
                    quantization="Q4_K_M",
                    memory_requirement="~2GB",
                    context_length=2048,
                    license="MIT",
                    tags=["reasoning", "code", "efficient", "quantized"],
                    architecture="Phi",
                    training_data="Filtered web data, synthetic data",
                    performance_metrics={
                        "inference_speed": "medium",
                        "memory_efficiency": "high",
                        "reasoning_score": "very_good",
                        "quality_score": 0.82,
                        "tokens_per_second": 18.0,
                        "memory_usage_mb": 2048
                    }
                ),
                "capabilities_detailed": ModelCapabilities(
                    primary_tasks=["code-generation", "reasoning", "text-generation", "problem-solving"],
                    supported_formats=["gguf"],
                    languages=["en", "code"],
                    domains=["general", "code", "reasoning", "math"],
                    performance_tier="high",
                    hardware_requirements={
                        "min_ram_gb": 2,
                        "recommended_ram_gb": 4,
                        "gpu_required": False,
                        "cpu_cores": 4
                    }
                ),
                "performance_metrics": PerformanceMetrics(
                    inference_speed="medium",
                    memory_efficiency="high",
                    quality_score=0.82,
                    benchmark_scores={
                        "hellaswag": 0.75,
                        "arc_challenge": 0.61,
                        "humaneval": 0.47,
                        "gsm8k": 0.57
                    },
                    tokens_per_second=18.0,
                    memory_usage_mb=2048
                ),
                "download_info": {
                    "url": "https://huggingface.co/microsoft/phi-2-gguf/resolve/main/phi-2.Q4_K_M.gguf",
                    "filename": "phi-2.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            # Additional popular models
            "llama-2-7b-chat-q4": {
                "id": "llama-2-7b-chat-q4",
                "name": "Llama 2 7B Chat Q4_K_M",
                "provider": "llama-cpp",
                "size": 4000000000,
                "description": "Meta's Llama 2 7B model fine-tuned for chat applications with Q4_K_M quantization.",
                "capabilities": ["text-generation", "chat", "instruction-following", "local-inference"],
                "metadata": ModelMetadata(
                    parameters="7B",
                    quantization="Q4_K_M",
                    memory_requirement="~4GB",
                    context_length=4096,
                    license="Custom (Llama 2)",
                    tags=["chat", "large", "high-quality", "quantized"],
                    architecture="Llama",
                    training_data="Custom mix of publicly available online data",
                    performance_metrics={
                        "inference_speed": "medium",
                        "memory_efficiency": "medium",
                        "quality_score": 0.85,
                        "tokens_per_second": 15.0,
                        "memory_usage_mb": 4096
                    }
                ),
                "download_info": {
                    "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf",
                    "filename": "llama-2-7b-chat.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            "mistral-7b-instruct-q4": {
                "id": "mistral-7b-instruct-q4",
                "name": "Mistral 7B Instruct Q4_K_M",
                "provider": "llama-cpp",
                "size": 4100000000,
                "description": "Mistral AI's 7B parameter model optimized for instruction following.",
                "capabilities": ["text-generation", "instruction-following", "chat", "local-inference"],
                "metadata": ModelMetadata(
                    parameters="7B",
                    quantization="Q4_K_M",
                    memory_requirement="~4GB",
                    context_length=8192,
                    license="Apache 2.0",
                    tags=["instruct", "large", "efficient", "quantized"],
                    architecture="Mistral",
                    training_data="High-quality web data",
                    performance_metrics={
                        "inference_speed": "fast",
                        "memory_efficiency": "high",
                        "quality_score": 0.87,
                        "tokens_per_second": 18.0,
                        "memory_usage_mb": 4096
                    }
                ),
                "download_info": {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
                    "filename": "mistral-7b-instruct-v0.1.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            "codellama-7b-instruct-q4": {
                "id": "codellama-7b-instruct-q4",
                "name": "Code Llama 7B Instruct Q4_K_M",
                "provider": "llama-cpp",
                "size": 4000000000,
                "description": "Meta's Code Llama 7B model fine-tuned for code generation and instruction following.",
                "capabilities": ["code-generation", "text-generation", "instruction-following", "local-inference"],
                "metadata": ModelMetadata(
                    parameters="7B",
                    quantization="Q4_K_M",
                    memory_requirement="~4GB",
                    context_length=16384,
                    license="Custom (Llama 2)",
                    tags=["code", "instruct", "large", "quantized"],
                    architecture="Llama",
                    training_data="Code datasets + instruction tuning",
                    performance_metrics={
                        "inference_speed": "medium",
                        "memory_efficiency": "medium",
                        "code_quality": "high",
                        "quality_score": 0.83,
                        "tokens_per_second": 14.0,
                        "memory_usage_mb": 4096
                    }
                ),
                "download_info": {
                    "url": "https://huggingface.co/TheBloke/CodeLlama-7B-Instruct-GGUF/resolve/main/codellama-7b-instruct.Q4_K_M.gguf",
                    "filename": "codellama-7b-instruct.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            # Transformers models
            "bert-base-uncased": {
                "id": "bert-base-uncased",
                "name": "BERT Base Uncased",
                "provider": "transformers",
                "size": 440000000,
                "description": "Google's BERT model for text understanding and classification tasks.",
                "capabilities": ["text-classification", "token-classification", "question-answering", "feature-extraction"],
                "metadata": ModelMetadata(
                    parameters="110M",
                    quantization="None",
                    memory_requirement="~1GB",
                    context_length=512,
                    license="Apache 2.0",
                    tags=["bert", "classification", "understanding"],
                    architecture="BERT",
                    training_data="BooksCorpus + English Wikipedia",
                    performance_metrics={
                        "inference_speed": "fast",
                        "memory_efficiency": "high",
                        "quality_score": 0.80,
                        "tokens_per_second": 100.0,
                        "memory_usage_mb": 1024
                    }
                ),
                "download_info": {
                    "url": "https://huggingface.co/bert-base-uncased",
                    "filename": "pytorch_model.bin",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            "distilbert-base-uncased": {
                "id": "distilbert-base-uncased",
                "name": "DistilBERT Base Uncased",
                "provider": "transformers",
                "size": 260000000,
                "description": "A distilled version of BERT that is smaller, faster, and lighter while retaining 97% of BERT's performance.",
                "capabilities": ["text-classification", "token-classification", "question-answering", "feature-extraction"],
                "metadata": ModelMetadata(
                    parameters="66M",
                    quantization="None",
                    memory_requirement="~512MB",
                    context_length=512,
                    license="Apache 2.0",
                    tags=["distilbert", "classification", "efficient"],
                    architecture="DistilBERT",
                    training_data="Same as BERT (distilled)",
                    performance_metrics={
                        "inference_speed": "very_fast",
                        "memory_efficiency": "very_high",
                        "quality_score": 0.77,
                        "tokens_per_second": 200.0,
                        "memory_usage_mb": 512
                    }
                ),
                "download_info": {
                    "url": "https://huggingface.co/distilbert-base-uncased",
                    "filename": "pytorch_model.bin",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            }
        }
    
    def _load_cache(self):
        """Load cached metadata from disk."""
        try:
            cache_file = self.cache_dir / "metadata_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                current_time = time.time()
                for model_id, cached_data in cache_data.items():
                    if cached_data.get("expires_at", 0) > current_time:
                        # Cache is still valid
                        metadata_dict = cached_data.get("metadata", {})
                        if metadata_dict:
                            metadata = ModelMetadata(**metadata_dict)
                            self.metadata_cache[model_id] = CachedMetadata(
                                metadata=metadata,
                                cached_at=cached_data.get("cached_at", current_time),
                                expires_at=cached_data.get("expires_at", current_time + self.cache_ttl),
                                source=cached_data.get("source", "unknown")
                            )
                
                logger.info(f"Loaded {len(self.metadata_cache)} cached metadata entries")
                
        except Exception as e:
            logger.warning(f"Failed to load metadata cache: {e}")
    
    def _save_cache(self):
        """Save metadata cache to disk."""
        try:
            cache_data = {}
            for model_id, cached_metadata in self.metadata_cache.items():
                cache_data[model_id] = {
                    "metadata": asdict(cached_metadata.metadata),
                    "cached_at": cached_metadata.cached_at,
                    "expires_at": cached_metadata.expires_at,
                    "source": cached_metadata.source
                }
            
            cache_file = self.cache_dir / "metadata_cache.json"
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metadata cache: {e}")
    
    def get_model_metadata(self, model_id: str, force_refresh: bool = False) -> Optional[ModelMetadata]:
        """Get comprehensive model metadata with caching."""
        with self._lock:
            current_time = time.time()
            
            # Check cache first (unless force refresh)
            if not force_refresh and model_id in self.metadata_cache:
                cached = self.metadata_cache[model_id]
                if cached.expires_at > current_time:
                    logger.debug(f"Returning cached metadata for {model_id}")
                    return cached.metadata
                else:
                    # Cache expired, remove it
                    del self.metadata_cache[model_id]
            
            # Check predefined models
            if model_id in self.predefined_models:
                metadata = self.predefined_models[model_id]["metadata"]
                
                # Cache the predefined metadata
                self.metadata_cache[model_id] = CachedMetadata(
                    metadata=metadata,
                    cached_at=current_time,
                    expires_at=current_time + (self.cache_ttl * 7),  # Predefined models cache longer
                    source="predefined"
                )
                
                return metadata
            
            # Try to fetch from remote sources (placeholder for future implementation)
            # For now, return None for unknown models
            logger.debug(f"No metadata found for model {model_id}")
            return None
    
    def get_model_capabilities(self, model_id: str) -> Optional[ModelCapabilities]:
        """Get detailed model capabilities."""
        if model_id in self.predefined_models:
            return self.predefined_models[model_id].get("capabilities_detailed")
        
        # Check cache
        if model_id in self.capabilities_cache:
            return self.capabilities_cache[model_id]
        
        return None
    
    def get_performance_metrics(self, model_id: str) -> Optional[PerformanceMetrics]:
        """Get model performance metrics."""
        if model_id in self.predefined_models:
            return self.predefined_models[model_id].get("performance_metrics")
        
        # Check cache
        if model_id in self.performance_cache:
            return self.performance_cache[model_id]
        
        return None
    
    def update_metadata_cache(self, model_id: str, metadata: ModelMetadata, source: str = "manual"):
        """Update metadata cache with new information."""
        with self._lock:
            current_time = time.time()
            
            self.metadata_cache[model_id] = CachedMetadata(
                metadata=metadata,
                cached_at=current_time,
                expires_at=current_time + self.cache_ttl,
                source=source
            )
            
            # Save to disk
            self._save_cache()
            
            logger.info(f"Updated metadata cache for {model_id}")
    
    def get_predefined_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all predefined model configurations."""
        return self.predefined_models.copy()
    
    def search_models_by_capability(self, capability: str) -> List[str]:
        """Search for models that support a specific capability."""
        matching_models = []
        
        for model_id, model_data in self.predefined_models.items():
            capabilities = model_data.get("capabilities", [])
            if capability.lower() in [cap.lower() for cap in capabilities]:
                matching_models.append(model_id)
        
        return matching_models
    
    def get_models_by_performance_tier(self, tier: str) -> List[str]:
        """Get models by performance tier (low, medium, high, enterprise)."""
        matching_models = []
        
        for model_id, model_data in self.predefined_models.items():
            capabilities = model_data.get("capabilities_detailed")
            if capabilities and capabilities.performance_tier == tier:
                matching_models.append(model_id)
        
        return matching_models
    
    def get_models_by_size_range(self, min_size: int = 0, max_size: int = float('inf')) -> List[str]:
        """Get models within a specific size range (in bytes)."""
        matching_models = []
        
        for model_id, model_data in self.predefined_models.items():
            size = model_data.get("size", 0)
            if min_size <= size <= max_size:
                matching_models.append(model_id)
        
        return matching_models
    
    def get_compatible_models(self, hardware_constraints: Dict[str, Any]) -> List[str]:
        """Get models compatible with given hardware constraints."""
        matching_models = []
        
        for model_id, model_data in self.predefined_models.items():
            capabilities = model_data.get("capabilities_detailed")
            if not capabilities:
                continue
            
            hw_req = capabilities.hardware_requirements
            
            # Check RAM requirement
            available_ram = hardware_constraints.get("ram_gb", 0)
            required_ram = hw_req.get("min_ram_gb", 0)
            if available_ram < required_ram:
                continue
            
            # Check GPU requirement
            has_gpu = hardware_constraints.get("has_gpu", False)
            gpu_required = hw_req.get("gpu_required", False)
            if gpu_required and not has_gpu:
                continue
            
            # Check CPU cores
            available_cores = hardware_constraints.get("cpu_cores", 1)
            required_cores = hw_req.get("cpu_cores", 1)
            if available_cores < required_cores:
                continue
            
            matching_models.append(model_id)
        
        return matching_models
    
    def get_model_comparison(self, model_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get comparison data for multiple models."""
        comparison = {}
        
        for model_id in model_ids:
            model_data = {}
            
            # Basic metadata
            metadata = self.get_model_metadata(model_id)
            if metadata:
                model_data["metadata"] = asdict(metadata)
            
            # Capabilities
            capabilities = self.get_model_capabilities(model_id)
            if capabilities:
                model_data["capabilities"] = asdict(capabilities)
            
            # Performance metrics
            performance = self.get_performance_metrics(model_id)
            if performance:
                model_data["performance"] = asdict(performance)
            
            # Basic info from predefined models
            if model_id in self.predefined_models:
                predefined = self.predefined_models[model_id]
                model_data.update({
                    "name": predefined.get("name"),
                    "size": predefined.get("size"),
                    "description": predefined.get("description"),
                    "provider": predefined.get("provider")
                })
            
            comparison[model_id] = model_data
        
        return comparison
    
    def refresh_all_cache(self):
        """Refresh all cached metadata (placeholder for future remote fetching)."""
        logger.info("Refreshing metadata cache...")
        
        # For now, just clear expired entries
        current_time = time.time()
        expired_keys = [
            model_id for model_id, cached in self.metadata_cache.items()
            if cached.expires_at <= current_time
        ]
        
        for key in expired_keys:
            del self.metadata_cache[key]
        
        self._save_cache()
        logger.info(f"Removed {len(expired_keys)} expired cache entries")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        
        total_entries = len(self.metadata_cache)
        expired_entries = sum(
            1 for cached in self.metadata_cache.values()
            if cached.expires_at <= current_time
        )
        
        sources = {}
        for cached in self.metadata_cache.values():
            source = cached.source
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "sources": sources,
            "predefined_models": len(self.predefined_models),
            "cache_ttl_hours": self.cache_ttl / 3600
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self._save_cache()
        self.executor.shutdown(wait=True)
        logger.info("ModelMetadataService cleanup completed")