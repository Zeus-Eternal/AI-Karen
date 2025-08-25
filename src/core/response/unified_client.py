"""Local-first LLM client with optional remote/cloud routing.

This module provides a small utility for favouring local LLM providers
(e.g. TinyLLaMA via llama.cpp or an in-process Ollama model) while still
allowing callers to explicitly opt in to cloud based models.  When both
local and remote providers fail, a trivial fallback client is used to
guarantee a response.

Enhanced with ModelSelector for intelligent local-first routing, warm-up
mechanisms, and performance-based cloud routing decisions.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .protocols import LLMClient

log = logging.getLogger(__name__)


class FallbackLLM:
    """Trivial LLM used when all providers fail."""

    def __init__(self, message: str = "I'm operating in fallback mode. Local models are unavailable.") -> None:
        self.message = message

    def generate(self, messages: List[Dict[str, str]], **_: Any) -> str:  # pragma: no cover - trivial
        return self.message


class TinyLlamaClient:
    """Local TinyLLaMA client using llama-cpp-python."""
    
    def __init__(self, model_path: Optional[str] = None, **kwargs):
        self.model_path = model_path or self._find_tinyllama_model()
        self.model = None
        self._warmed = False
        self.generation_kwargs = {
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "stop": kwargs.get("stop", ["</s>", "<|im_end|>"]),
        }
        
    def _find_tinyllama_model(self) -> str:
        """Find TinyLLaMA model in standard locations."""
        possible_paths = [
            Path("models/llama-cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"),
            Path("models/llama-cpp").glob("*.gguf"),
        ]
        
        for path_or_glob in possible_paths:
            if isinstance(path_or_glob, Path) and path_or_glob.exists():
                return str(path_or_glob)
            elif hasattr(path_or_glob, '__iter__'):
                for path in path_or_glob:
                    if path.exists():
                        return str(path)
        
        raise FileNotFoundError("No TinyLLaMA model found in models/llama-cpp/")
    
    def _load_model(self):
        """Load the llama-cpp model."""
        if self.model is None:
            try:
                from llama_cpp import Llama
                self.model = Llama(
                    model_path=self.model_path,
                    n_ctx=2048,  # Context window
                    n_threads=4,  # CPU threads
                    verbose=False,
                )
                log.info(f"Loaded TinyLLaMA model from {self.model_path}")
            except ImportError:
                raise ImportError("llama-cpp-python not installed. Run: pip install llama-cpp-python")
            except Exception as e:
                raise RuntimeError(f"Failed to load TinyLLaMA model: {e}")
    
    def warmup(self):
        """Warm up the model with a simple generation."""
        if not self._warmed:
            try:
                self._load_model()
                # Simple warmup prompt
                self.model.create_completion(
                    prompt="Hello",
                    max_tokens=1,
                    temperature=0.1,
                )
                self._warmed = True
                log.info("TinyLLaMA model warmed up successfully")
            except Exception as e:
                log.warning(f"TinyLLaMA warmup failed: {e}")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from messages."""
        try:
            self._load_model()
            
            # Convert messages to prompt format
            prompt = self._messages_to_prompt(messages)
            
            # Merge generation parameters
            gen_kwargs = {**self.generation_kwargs, **kwargs}
            gen_kwargs.pop("model", None)  # Remove model param if present
            
            # Generate response
            response = self.model.create_completion(
                prompt=prompt,
                **gen_kwargs
            )
            
            return response["choices"][0]["text"].strip()
            
        except Exception as e:
            log.error(f"TinyLLaMA generation failed: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to TinyLLaMA prompt format."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            elif role == "user":
                prompt_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
            elif role == "assistant":
                prompt_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
        
        # Add assistant start token for generation
        prompt_parts.append("<|im_start|>assistant\n")
        
        return "\n".join(prompt_parts)


class OllamaClient:
    """Local Ollama client."""
    
    def __init__(self, model_name: str = "tinyllama", base_url: str = "http://localhost:11434", **kwargs):
        self.model_name = model_name
        self.base_url = base_url
        self.client = None
        self._warmed = False
        self.generation_kwargs = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "max_tokens": kwargs.get("max_tokens", 512),
        }
    
    def _get_client(self):
        """Get or create Ollama client."""
        if self.client is None:
            try:
                import ollama
                self.client = ollama.Client(host=self.base_url)
                log.info(f"Connected to Ollama at {self.base_url}")
            except ImportError:
                raise ImportError("ollama package not installed. Run: pip install ollama")
            except Exception as e:
                raise RuntimeError(f"Failed to connect to Ollama: {e}")
        return self.client
    
    def warmup(self):
        """Warm up the model with a simple generation."""
        if not self._warmed:
            try:
                client = self._get_client()
                # Simple warmup
                client.generate(
                    model=self.model_name,
                    prompt="Hello",
                    options={"num_predict": 1}
                )
                self._warmed = True
                log.info(f"Ollama model {self.model_name} warmed up successfully")
            except Exception as e:
                log.warning(f"Ollama warmup failed: {e}")
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response from messages."""
        try:
            client = self._get_client()
            
            # Merge generation parameters
            gen_kwargs = {**self.generation_kwargs, **kwargs}
            model = gen_kwargs.pop("model", self.model_name)
            
            # Convert to Ollama options format
            options = {
                "temperature": gen_kwargs.get("temperature", 0.7),
                "top_p": gen_kwargs.get("top_p", 0.9),
                "num_predict": gen_kwargs.get("max_tokens", 512),
            }
            
            # Use chat API if available, otherwise convert to prompt
            try:
                response = client.chat(
                    model=model,
                    messages=messages,
                    options=options
                )
                return response["message"]["content"]
            except Exception:
                # Fallback to generate API
                prompt = self._messages_to_prompt(messages)
                response = client.generate(
                    model=model,
                    prompt=prompt,
                    options=options
                )
                return response["response"]
                
        except Exception as e:
            log.error(f"Ollama generation failed: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to prompt format."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)


class ModelSelector:
    """Enhanced model selector with local-first routing logic.

    Implements intelligent routing decisions based on:
    - Local-first principle (always prefer local models)
    - Context size and complexity hints
    - Performance requirements
    - Explicit cloud enablement
    """

    def __init__(
        self, 
        local_clients: List[LLMClient], 
        remote_client: Optional[LLMClient] = None,
        local_only: bool = True
    ) -> None:
        self.local_clients = local_clients
        self.remote_client = remote_client
        self.local_only = local_only
        self._performance_history: Dict[str, List[float]] = {}
    
    def select_client(
        self, 
        intent: str = "general", 
        context_size: int = 0, 
        cloud_hint: bool = False,
        **kwargs
    ) -> LLMClient:
        """Select the best client for the request.
        
        Args:
            intent: User intent (optimize_code, general_assist, etc.)
            context_size: Size of context in tokens
            cloud_hint: Performance hint suggesting cloud might be beneficial
            **kwargs: Additional selection criteria
            
        Returns:
            Selected LLM client
        """
        # Always prefer local unless explicitly overridden
        if self.local_only or not cloud_hint:
            return self._select_local_client(intent, context_size)
        
        # Cloud routing only when explicitly enabled and justified
        if (cloud_hint and 
            self.remote_client is not None and 
            self._should_use_cloud(intent, context_size)):
            return self.remote_client
        
        # Default to local
        return self._select_local_client(intent, context_size)
    
    def _select_local_client(self, intent: str, context_size: int) -> LLMClient:
        """Select best local client based on intent and context."""
        if not self.local_clients:
            raise RuntimeError("No local clients available")
        
        # For now, return first available local client
        # Future enhancement: implement client selection based on capabilities
        return self.local_clients[0]
    
    def _should_use_cloud(self, intent: str, context_size: int) -> bool:
        """Determine if cloud routing is justified.
        
        Cloud routing criteria:
        - Large context size (>4096 tokens)
        - Complex intents (code_optimization, complex_analysis)
        - Performance hints from upstream components
        """
        # Large context suggests cloud might be better
        if context_size > 4096:
            return True
        
        # Complex intents that might benefit from larger models
        complex_intents = {
            "code_optimization", "complex_analysis", "research", 
            "creative_writing", "technical_documentation"
        }
        if intent in complex_intents:
            return True
        
        return False
    
    def ordered(self, cloud_enabled: bool = False, **kwargs) -> List[LLMClient]:
        """Return clients in the order they should be attempted.
        
        Maintains backward compatibility while adding enhanced routing.
        """
        clients = list(self.local_clients)
        
        if (cloud_enabled and 
            not self.local_only and 
            self.remote_client is not None):
            clients.append(self.remote_client)
        
        return clients
    
    def record_performance(self, client_id: str, latency: float):
        """Record performance metrics for future routing decisions."""
        if client_id not in self._performance_history:
            self._performance_history[client_id] = []
        
        history = self._performance_history[client_id]
        history.append(latency)
        
        # Keep only recent samples
        if len(history) > 50:
            history.pop(0)


class UnifiedLLMClient:
    """Enhanced local-first LLM client with intelligent routing."""

    def __init__(
        self,
        local_clients: Optional[List[LLMClient]] = None,
        remote_client: Optional[LLMClient] = None,
        *,
        local_only: bool = True,
        fallback_client: Optional[LLMClient] = None,
        auto_warmup: bool = True,
    ) -> None:
        # Initialize local clients if not provided
        if local_clients is None:
            local_clients = self._create_default_local_clients()
        
        self.selector = ModelSelector(
            local_clients=local_clients,
            remote_client=remote_client,
            local_only=local_only
        )
        self.fallback_client = fallback_client or FallbackLLM()
        self.local_only = local_only
        self._warmed = False
        
        if auto_warmup:
            self.warmup()

    def _create_default_local_clients(self) -> List[LLMClient]:
        """Create default local clients (TinyLLaMA and Ollama)."""
        clients = []
        
        # Try TinyLLaMA first
        try:
            tinyllama = TinyLlamaClient()
            clients.append(tinyllama)
            log.info("TinyLLaMA client initialized")
        except Exception as e:
            log.warning(f"TinyLLaMA client initialization failed: {e}")
        
        # Try Ollama as backup
        try:
            ollama = OllamaClient()
            clients.append(ollama)
            log.info("Ollama client initialized")
        except Exception as e:
            log.warning(f"Ollama client initialization failed: {e}")
        
        if not clients:
            log.warning("No local clients available, using fallback only")
        
        return clients

    def warmup(self) -> None:
        """Warm up all local models."""
        if not self._warmed:
            for client in self.selector.local_clients:
                try:
                    if hasattr(client, 'warmup'):
                        client.warmup()
                except Exception as e:
                    log.warning(f"Client warmup failed: {e}")
            self._warmed = True
            log.info("Local models warmed up")

    def generate(
        self, 
        messages: List[Dict[str, str]], 
        *,
        intent: str = "general",
        context_size: int = 0,
        cloud_hint: bool = False,
        **kwargs: Any
    ) -> str:
        """Generate a response using local-first routing.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            intent: User intent for routing decisions
            context_size: Size of context in tokens
            cloud_hint: Performance hint suggesting cloud might be beneficial
            **kwargs: Additional generation parameters
        """
        start_time = time.time()
        
        # Select client based on local-first routing
        try:
            client = self.selector.select_client(
                intent=intent,
                context_size=context_size,
                cloud_hint=cloud_hint and not self.local_only,
                **kwargs
            )
            
            response = client.generate(messages, **kwargs)
            
            # Record performance
            latency = time.time() - start_time
            client_id = getattr(client, '__class__', type(client)).__name__
            self.selector.record_performance(client_id, latency)
            
            log.info(f"Generated response using {client_id} in {latency:.2f}s")
            return response
            
        except Exception as e:
            log.error(f"Primary client failed: {e}")
            
            # Try fallback clients
            for client in self.selector.ordered(cloud_enabled=cloud_hint and not self.local_only):
                client_id = getattr(client, '__class__', type(client)).__name__
                try:
                    response = client.generate(messages, **kwargs)
                    latency = time.time() - start_time
                    log.info(f"Fallback to {client_id} succeeded in {latency:.2f}s")
                    return response
                except Exception as fallback_error:
                    log.warning(f"Fallback client {client_id} failed: {fallback_error}")
                    continue
            
            # Final fallback
            log.warning("All clients failed; using fallback response")
            return self.fallback_client.generate(messages, **kwargs)

    # Backward compatibility method
    def generate_legacy(self, prompt: str, *, cloud: Optional[bool] = None, **kwargs: Any) -> str:
        """Legacy generate method for backward compatibility."""
        # Convert prompt to messages format
        messages = [{"role": "user", "content": prompt}]
        
        return self.generate(
            messages=messages,
            cloud_hint=cloud or False,
            **kwargs
        )

    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models."""
        models = {
            "local": [],
            "remote": None,
            "fallback": True
        }
        
        for client in self.selector.local_clients:
            client_info = {
                "type": client.__class__.__name__,
                "warmed": getattr(client, '_warmed', False),
                "available": True
            }
            
            if hasattr(client, 'model_path'):
                client_info["model_path"] = client.model_path
            elif hasattr(client, 'model_name'):
                client_info["model_name"] = client.model_name
                
            models["local"].append(client_info)
        
        if self.selector.remote_client:
            models["remote"] = {
                "type": self.selector.remote_client.__class__.__name__,
                "available": not self.local_only
            }
        
        return models


def create_local_first_client(
    remote_client: Optional[LLMClient] = None,
    local_only: bool = True,
    tinyllama_path: Optional[str] = None,
    ollama_model: str = "tinyllama",
    ollama_url: str = "http://localhost:11434",
    **kwargs
) -> UnifiedLLMClient:
    """Factory function to create a local-first LLM client.
    
    Args:
        remote_client: Optional cloud/remote client
        local_only: If True, never use cloud clients
        tinyllama_path: Path to TinyLLaMA model file
        ollama_model: Ollama model name
        ollama_url: Ollama server URL
        **kwargs: Additional client configuration
        
    Returns:
        Configured UnifiedLLMClient
    """
    local_clients = []
    
    # Try to create TinyLLaMA client
    try:
        tinyllama = TinyLlamaClient(model_path=tinyllama_path, **kwargs)
        local_clients.append(tinyllama)
        log.info("TinyLLaMA client created successfully")
    except Exception as e:
        log.warning(f"Failed to create TinyLLaMA client: {e}")
    
    # Try to create Ollama client
    try:
        ollama = OllamaClient(
            model_name=ollama_model,
            base_url=ollama_url,
            **kwargs
        )
        local_clients.append(ollama)
        log.info("Ollama client created successfully")
    except Exception as e:
        log.warning(f"Failed to create Ollama client: {e}")
    
    return UnifiedLLMClient(
        local_clients=local_clients,
        remote_client=remote_client,
        local_only=local_only,
        **kwargs
    )


# Convenience function for creating a basic local-only client
def create_local_only_client(**kwargs) -> UnifiedLLMClient:
    """Create a local-only LLM client with default settings."""
    return create_local_first_client(local_only=True, **kwargs)