"""
Mock Provider Routes for Development
Provides fast mock responses for provider endpoints to avoid timeouts during development.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["mock-providers"])

# Mock data for different providers
MOCK_PROVIDER_SUGGESTIONS = {
    "openai": {
        "provider": "openai",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion", "embedding"],
            "required_capabilities": ["api_key"],
            "optional_capabilities": ["organization"],
            "performance_type": "cloud",
            "quantization_support": "none"
        },
        "recommendations": {
            "excellent": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "good": ["text-davinci-003", "text-embedding-ada-002"],
            "acceptable": ["gpt-3.5-turbo-instruct"]
        },
        "total_compatible_models": 6,
        "compatibility_details": {
            "gpt-4": {"compatibility_score": 0.95, "performance_rating": "excellent"},
            "gpt-3.5-turbo": {"compatibility_score": 0.90, "performance_rating": "excellent"}
        }
    },
    "anthropic": {
        "provider": "anthropic",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion"],
            "required_capabilities": ["api_key"],
            "optional_capabilities": [],
            "performance_type": "cloud",
            "quantization_support": "none"
        },
        "recommendations": {
            "excellent": ["claude-3-opus", "claude-3-sonnet"],
            "good": ["claude-3-haiku", "claude-2.1"],
            "acceptable": ["claude-2.0"]
        },
        "total_compatible_models": 5,
        "compatibility_details": {
            "claude-3-opus": {"compatibility_score": 0.93, "performance_rating": "excellent"},
            "claude-3-sonnet": {"compatibility_score": 0.91, "performance_rating": "excellent"}
        }
    },
    "gemini": {
        "provider": "gemini",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion", "embedding"],
            "required_capabilities": ["api_key"],
            "optional_capabilities": [],
            "performance_type": "cloud",
            "quantization_support": "none"
        },
        "recommendations": {
            "excellent": ["gemini-pro", "gemini-pro-vision"],
            "good": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "acceptable": ["gemini-nano"]
        },
        "total_compatible_models": 5,
        "compatibility_details": {
            "gemini-pro": {"compatibility_score": 0.89, "performance_rating": "excellent"},
            "gemini-pro-vision": {"compatibility_score": 0.87, "performance_rating": "good"}
        }
    },
    "mistral": {
        "provider": "mistral",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion"],
            "required_capabilities": ["api_key"],
            "optional_capabilities": [],
            "performance_type": "cloud",
            "quantization_support": "none"
        },
        "recommendations": {
            "excellent": ["mistral-large", "mistral-medium"],
            "good": ["mistral-small", "mistral-tiny"],
            "acceptable": []
        },
        "total_compatible_models": 4,
        "compatibility_details": {
            "mistral-large": {"compatibility_score": 0.88, "performance_rating": "excellent"},
            "mistral-medium": {"compatibility_score": 0.85, "performance_rating": "good"}
        }
    },
    "groq": {
        "provider": "groq",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion"],
            "required_capabilities": ["api_key"],
            "optional_capabilities": [],
            "performance_type": "cloud",
            "quantization_support": "none"
        },
        "recommendations": {
            "excellent": ["llama2-70b-4096", "mixtral-8x7b-32768"],
            "good": ["llama2-7b-2048", "gemma-7b-it"],
            "acceptable": []
        },
        "total_compatible_models": 4,
        "compatibility_details": {
            "llama2-70b-4096": {"compatibility_score": 0.86, "performance_rating": "excellent"},
            "mixtral-8x7b-32768": {"compatibility_score": 0.84, "performance_rating": "good"}
        }
    },
    "llama-cpp": {
        "provider": "llama-cpp",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion"],
            "required_capabilities": ["model_path"],
            "optional_capabilities": ["gpu_layers", "context_length"],
            "performance_type": "local",
            "quantization_support": "gguf"
        },
        "recommendations": {
            "excellent": ["llama-2-7b-chat.Q4_K_M.gguf", "llama-2-13b-chat.Q4_K_M.gguf"],
            "good": ["codellama-7b-instruct.Q4_K_M.gguf", "mistral-7b-instruct.Q4_K_M.gguf"],
            "acceptable": ["tinyllama-1.1b-chat.Q4_K_M.gguf"]
        },
        "total_compatible_models": 5,
        "compatibility_details": {
            "llama-2-7b-chat.Q4_K_M.gguf": {"compatibility_score": 0.92, "performance_rating": "excellent"},
            "llama-2-13b-chat.Q4_K_M.gguf": {"compatibility_score": 0.90, "performance_rating": "excellent"}
        }
    },
    "transformers-local": {
        "provider": "transformers-local",
        "provider_capabilities": {
            "supported_formats": ["chat", "completion", "embedding"],
            "required_capabilities": ["model_name"],
            "optional_capabilities": ["device", "torch_dtype"],
            "performance_type": "local",
            "quantization_support": "int8"
        },
        "recommendations": {
            "excellent": ["microsoft/DialoGPT-medium", "microsoft/DialoGPT-large"],
            "good": ["distilbert-base-uncased", "bert-base-uncased"],
            "acceptable": ["gpt2", "distilgpt2"]
        },
        "total_compatible_models": 6,
        "compatibility_details": {
            "microsoft/DialoGPT-medium": {"compatibility_score": 0.88, "performance_rating": "excellent"},
            "distilbert-base-uncased": {"compatibility_score": 0.85, "performance_rating": "good"}
        }
    },
    "spacy": {
        "provider": "spacy",
        "provider_capabilities": {
            "supported_formats": ["nlp", "embedding"],
            "required_capabilities": ["model_name"],
            "optional_capabilities": ["disable_components"],
            "performance_type": "local",
            "quantization_support": "none"
        },
        "recommendations": {
            "excellent": ["en_core_web_sm", "en_core_web_md"],
            "good": ["en_core_web_lg", "en_core_web_trf"],
            "acceptable": []
        },
        "total_compatible_models": 4,
        "compatibility_details": {
            "en_core_web_sm": {"compatibility_score": 0.90, "performance_rating": "excellent"},
            "en_core_web_md": {"compatibility_score": 0.88, "performance_rating": "excellent"}
        }
    }
}

@router.get("/{provider_name}/suggestions")
async def get_provider_model_suggestions_mock(provider_name: str) -> Dict[str, Any]:
    """
    Mock endpoint for provider model suggestions.
    Returns fast mock data to avoid timeouts during development.
    """
    try:
        logger.info(f"Mock: Getting model suggestions for provider: {provider_name}")
        
        # Return mock data if available
        if provider_name in MOCK_PROVIDER_SUGGESTIONS:
            return MOCK_PROVIDER_SUGGESTIONS[provider_name]
        
        # Return generic mock data for unknown providers
        return {
            "provider": provider_name,
            "provider_capabilities": {
                "supported_formats": ["unknown"],
                "required_capabilities": ["api_key"],
                "optional_capabilities": [],
                "performance_type": "unknown",
                "quantization_support": "unknown"
            },
            "recommendations": {
                "excellent": [],
                "good": [f"{provider_name}-model-1", f"{provider_name}-model-2"],
                "acceptable": [f"{provider_name}-model-3"]
            },
            "total_compatible_models": 3,
            "compatibility_details": {
                f"{provider_name}-model-1": {"compatibility_score": 0.80, "performance_rating": "good"},
                f"{provider_name}-model-2": {"compatibility_score": 0.75, "performance_rating": "good"}
            }
        }
        
    except Exception as e:
        logger.error(f"Mock: Error getting suggestions for {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions for {provider_name}")

@router.get("/integration/status")
async def get_integration_status_mock() -> Dict[str, Any]:
    """
    Mock endpoint for integration status.
    Returns fast mock data to avoid timeouts during development.
    """
    try:
        logger.info("Mock: Getting integration status")
        
        return {
            "status": "healthy",
            "total_providers": len(MOCK_PROVIDER_SUGGESTIONS),
            "active_providers": len(MOCK_PROVIDER_SUGGESTIONS),
            "integration_health": {
                provider: {
                    "status": "connected",
                    "last_check": "2025-09-01T12:00:00Z",
                    "response_time_ms": 150,
                    "error_count": 0
                }
                for provider in MOCK_PROVIDER_SUGGESTIONS.keys()
            },
            "last_sync": "2025-09-01T12:00:00Z",
            "degraded_mode": False
        }
        
    except Exception as e:
        logger.error(f"Mock: Error getting integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration status")