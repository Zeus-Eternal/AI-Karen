"""
Transformers Runtime Implementation

This module provides the TransformersRuntime class for executing safetensors models
using HuggingFace Transformers with support for FP16, BitsAndBytes quantization, and LoRA.
"""

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TextIteratorStreamer,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers not available. TransformersRuntime will be disabled.")
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None
    TextIteratorStreamer = None
    pipeline = None

try:
    from peft import PeftModel
    PEFT_AVAILABLE = True
except ImportError:
    logger.debug("peft not available. LoRA support will be disabled.")
    PEFT_AVAILABLE = False
    PeftModel = None


class TransformersRuntime:
    """
    Runtime for executing safetensors models using HuggingFace Transformers.
    
    This runtime provides flexible model execution with support for various
    quantization methods, LoRA adapters, and both CPU and GPU inference.
    
    Key Features:
    - Safetensors model support with automatic format detection
    - FP16, BF16, INT8, and INT4 quantization support
    - LoRA adapter loading and merging
    - CPU and GPU inference with automatic device selection
    - Streaming and batch inference modes
    - Memory optimization techniques
    - Health monitoring and resource tracking
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        torch_dtype: Optional[str] = None,
        quantization: Optional[str] = None,
        use_flash_attention: bool = False,
        max_memory: Optional[Dict[str, str]] = None,
        trust_remote_code: bool = False,
        **kwargs
    ):
        """
        Initialize Transformers runtime.
        
        Args:
            model_path: Path to model directory or HuggingFace model ID
            device: Device to use ('cpu', 'cuda', 'auto')
            torch_dtype: Torch data type ('float16', 'bfloat16', 'float32')
            quantization: Quantization method ('int8', 'int4', 'fp16', 'bf16')
            use_flash_attention: Use Flash Attention 2 if available
            max_memory: Maximum memory per device
            trust_remote_code: Trust remote code execution
            **kwargs: Additional model parameters
        """
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers is not available. Please install it to use TransformersRuntime.")
        
        self.model_path = model_path
        self.device = device or self._auto_select_device()
        self.torch_dtype = self._parse_torch_dtype(torch_dtype)
        self.quantization = quantization
        self.use_flash_attention = use_flash_attention
        self.max_memory = max_memory
        self.trust_remote_code = trust_remote_code
        self.kwargs = kwargs
        
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._pipeline: Optional[Any] = None
        self._lock = threading.RLock()
        self._loaded = False
        self._load_time: Optional[float] = None
        self._memory_usage: Optional[int] = None
        
        # Load model if path provided
        if model_path:
            self.load_model(model_path)
    
    def _auto_select_device(self) -> str:
        """Automatically select the best available device."""
        if torch and torch.cuda.is_available():
            return "cuda"
        elif torch and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _parse_torch_dtype(self, dtype_str: Optional[str]) -> Optional[Any]:
        """Parse torch dtype string to torch dtype."""
        if not dtype_str or not torch:
            return None
        
        dtype_map = {
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float32": torch.float32,
            "fp32": torch.float32,
        }
        
        return dtype_map.get(dtype_str.lower())
    
    def _create_quantization_config(self) -> Optional[Any]:
        """Create quantization configuration."""
        if not self.quantization:
            return None
        
        if self.quantization.lower() in ["int8", "8bit"]:
            return BitsAndBytesConfig(load_in_8bit=True)
        elif self.quantization.lower() in ["int4", "4bit"]:
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=self.torch_dtype or torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        
        return None
    
    def load_model(self, model_path: str, **override_kwargs) -> bool:
        """
        Load a model from path or HuggingFace Hub.
        
        Args:
            model_path: Path to model directory or HuggingFace model ID
            **override_kwargs: Override initialization parameters
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        with self._lock:
            try:
                start_time = time.time()
                
                # Validate model path
                if Path(model_path).exists():
                    logger.info(f"Loading local model: {model_path}")
                else:
                    logger.info(f"Loading model from HuggingFace Hub: {model_path}")
                
                # Merge override parameters
                load_params = {
                    "device_map": "auto" if self.device == "auto" else None,
                    "torch_dtype": self.torch_dtype,
                    "trust_remote_code": self.trust_remote_code,
                    "use_flash_attention_2": self.use_flash_attention,
                    "max_memory": self.max_memory,
                    **self.kwargs,
                    **override_kwargs
                }
                
                # Add quantization config
                quantization_config = self._create_quantization_config()
                if quantization_config:
                    load_params["quantization_config"] = quantization_config
                
                logger.debug(f"Loading model with params: {load_params}")
                
                # Load tokenizer
                logger.info("Loading tokenizer...")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_path,
                    trust_remote_code=self.trust_remote_code
                )
                
                # Set pad token if not present
                if self._tokenizer.pad_token is None:
                    self._tokenizer.pad_token = self._tokenizer.eos_token
                
                # Load model
                logger.info("Loading model...")
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    **load_params
                )
                
                # Move to device if not using device_map
                if load_params.get("device_map") is None and self.device != "auto":
                    self._model = self._model.to(self.device)
                
                # Create text generation pipeline
                self._pipeline = pipeline(
                    "text-generation",
                    model=self._model,
                    tokenizer=self._tokenizer,
                    device=0 if self.device == "cuda" else -1
                )
                
                self.model_path = model_path
                self._loaded = True
                self._load_time = time.time() - start_time
                
                # Estimate memory usage
                if hasattr(self._model, "get_memory_footprint"):
                    self._memory_usage = self._model.get_memory_footprint()
                else:
                    # Rough estimation based on parameters
                    num_params = sum(p.numel() for p in self._model.parameters())
                    bytes_per_param = 2 if self.torch_dtype == torch.float16 else 4
                    self._memory_usage = num_params * bytes_per_param
                
                logger.info(f"Model loaded successfully in {self._load_time:.2f}s")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model {model_path}: {e}")
                self._model = None
                self._tokenizer = None
                self._pipeline = None
                self._loaded = False
                return False
    
    def load_lora_adapter(self, adapter_path: str, adapter_name: str = "default") -> bool:
        """
        Load a LoRA adapter.
        
        Args:
            adapter_path: Path to LoRA adapter
            adapter_name: Name for the adapter
            
        Returns:
            True if adapter loaded successfully, False otherwise
        """
        if not PEFT_AVAILABLE:
            logger.error("PEFT not available. Cannot load LoRA adapter.")
            return False
        
        if not self.is_loaded():
            logger.error("No base model loaded. Load a model first.")
            return False
        
        with self._lock:
            try:
                logger.info(f"Loading LoRA adapter: {adapter_path}")
                
                # Load adapter
                self._model = PeftModel.from_pretrained(
                    self._model,
                    adapter_path,
                    adapter_name=adapter_name
                )
                
                logger.info(f"LoRA adapter '{adapter_name}' loaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load LoRA adapter {adapter_path}: {e}")
                return False
    
    def unload_model(self) -> None:
        """Unload the current model and free memory."""
        with self._lock:
            if self._model:
                del self._model
                self._model = None
            
            if self._tokenizer:
                del self._tokenizer
                self._tokenizer = None
            
            if self._pipeline:
                del self._pipeline
                self._pipeline = None
            
            self._loaded = False
            self._load_time = None
            self._memory_usage = None
            
            # Clear GPU cache if using CUDA
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Model unloaded")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
        stop_sequences: Optional[List[str]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repetition_penalty: Repetition penalty
            stop_sequences: Stop sequences
            stream: Whether to stream tokens
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text (string) or token iterator if streaming
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        with self._lock:
            try:
                generation_params = {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "repetition_penalty": repetition_penalty,
                    "do_sample": temperature > 0,
                    "pad_token_id": self._tokenizer.eos_token_id,
                    **kwargs
                }
                
                if stop_sequences:
                    generation_params["stop_sequence"] = stop_sequences
                
                logger.debug(f"Generating with params: {generation_params}")
                
                if stream:
                    return self._stream_generate(prompt, **generation_params)
                else:
                    return self._complete_generate(prompt, **generation_params)
                    
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                raise
    
    def _complete_generate(self, prompt: str, **params) -> str:
        """Generate complete response (non-streaming)."""
        # Use pipeline for simple generation
        result = self._pipeline(
            prompt,
            return_full_text=False,
            **params
        )
        
        if isinstance(result, list) and len(result) > 0:
            return result[0]["generated_text"]
        else:
            return ""
    
    def _stream_generate(self, prompt: str, **params) -> Iterator[str]:
        """Generate streaming response."""
        # Tokenize input
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        
        # Create streamer
        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        
        # Add streamer to generation params
        params["streamer"] = streamer
        
        # Start generation in a separate thread
        import threading
        generation_thread = threading.Thread(
            target=self._model.generate,
            args=(inputs.input_ids,),
            kwargs=params
        )
        generation_thread.start()
        
        # Yield tokens as they're generated
        for token in streamer:
            yield token
        
        generation_thread.join()
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Note: This requires a model that supports embeddings.
        For general language models, this will use the last hidden state.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        with self._lock:
            try:
                # Tokenize input
                inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)
                
                # Get model outputs
                with torch.no_grad():
                    outputs = self._model(**inputs, output_hidden_states=True)
                
                # Use last hidden state as embedding (mean pooling)
                last_hidden_state = outputs.hidden_states[-1]
                embedding = torch.mean(last_hidden_state, dim=1).squeeze()
                
                return embedding.cpu().numpy().tolist()
                
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                raise
    
    def tokenize(self, text: str) -> List[int]:
        """
        Tokenize text.
        
        Args:
            text: Input text
            
        Returns:
            List of token IDs
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        try:
            tokens = self._tokenizer.encode(text)
            return tokens
        except Exception as e:
            logger.error(f"Tokenization failed: {e}")
            raise
    
    def detokenize(self, tokens: List[int]) -> str:
        """
        Detokenize token IDs to text.
        
        Args:
            tokens: List of token IDs
            
        Returns:
            Decoded text
        """
        if not self.is_loaded():
            raise RuntimeError("No model loaded. Call load_model() first.")
        
        try:
            text = self._tokenizer.decode(tokens, skip_special_tokens=True)
            return text
        except Exception as e:
            logger.error(f"Detokenization failed: {e}")
            raise
    
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._loaded and self._model is not None and self._tokenizer is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        with self._lock:
            info = {
                "runtime": "transformers",
                "loaded": self._loaded,
                "model_path": self.model_path,
                "load_time": self._load_time,
                "memory_usage": self._memory_usage,
                "device": self.device,
                "torch_dtype": str(self.torch_dtype) if self.torch_dtype else None,
                "quantization": self.quantization,
                "flash_attention": self.use_flash_attention,
            }
            
            if self._model:
                try:
                    info["num_parameters"] = sum(p.numel() for p in self._model.parameters())
                    info["config"] = self._model.config.to_dict() if hasattr(self._model, "config") else {}
                except:
                    pass
            
            return info
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the runtime.
        
        Returns:
            Health status information
        """
        try:
            start_time = time.time()
            
            # Check if transformers is available
            if not TRANSFORMERS_AVAILABLE:
                return {
                    "status": "unhealthy",
                    "error": "transformers not available",
                    "response_time": time.time() - start_time
                }
            
            # Check if model is loaded
            if not self.is_loaded():
                return {
                    "status": "healthy",
                    "message": "Runtime available, no model loaded",
                    "response_time": time.time() - start_time,
                    "capabilities": {
                        "model_loading": True,
                        "text_generation": False,
                        "embeddings": False,
                        "streaming": True,
                        "lora_adapters": PEFT_AVAILABLE
                    }
                }
            
            # Test basic functionality with loaded model
            try:
                # Simple tokenization test
                tokens = self.tokenize("Hello")
                if not tokens:
                    raise RuntimeError("Tokenization returned empty result")
                
                # Test detokenization
                text = self.detokenize(tokens)
                if not text:
                    raise RuntimeError("Detokenization returned empty result")
                
                capabilities = {
                    "model_loading": True,
                    "text_generation": True,
                    "embeddings": True,
                    "streaming": True,
                    "tokenization": True,
                    "lora_adapters": PEFT_AVAILABLE,
                    "quantization": self.quantization is not None
                }
                
                return {
                    "status": "healthy",
                    "message": "All systems operational",
                    "response_time": time.time() - start_time,
                    "model_info": self.get_model_info(),
                    "capabilities": capabilities
                }
                
            except Exception as e:
                return {
                    "status": "degraded",
                    "error": f"Model functionality test failed: {e}",
                    "response_time": time.time() - start_time,
                    "model_info": self.get_model_info()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": time.time() - start_time if 'start_time' in locals() else None
            }
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        usage = {
            "memory_usage": self._memory_usage,
            "model_loaded": self.is_loaded(),
            "device": self.device,
            "quantization": self.quantization,
        }
        
        # Add GPU memory usage if available
        if torch and torch.cuda.is_available() and self.device == "cuda":
            usage["gpu_memory_allocated"] = torch.cuda.memory_allocated()
            usage["gpu_memory_reserved"] = torch.cuda.memory_reserved()
        
        return usage
    
    def shutdown(self) -> None:
        """Shutdown the runtime and cleanup resources."""
        logger.info("Shutting down Transformers runtime")
        self.unload_model()
    
    @staticmethod
    def is_available() -> bool:
        """Check if Transformers runtime is available."""
        return TRANSFORMERS_AVAILABLE
    
    @staticmethod
    def supports_format(format_name: str) -> bool:
        """Check if runtime supports a specific model format."""
        supported_formats = ["safetensors", "fp16", "bf16", "int8", "int4"]
        return format_name.lower() in supported_formats
    
    @staticmethod
    def supports_family(family_name: str) -> bool:
        """Check if runtime supports a specific model family."""
        # Transformers supports most model families
        supported_families = [
            "llama", "mistral", "qwen", "phi", "gemma", "bert", "gpt",
            "codellama", "vicuna", "alpaca", "orca", "falcon", "mpt"
        ]
        return family_name.lower() in supported_families


__all__ = ["TransformersRuntime"]