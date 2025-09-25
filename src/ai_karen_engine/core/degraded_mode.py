from __future__ import annotations

"""Enhanced degraded mode system with core helper models (TinyLLaMA + DistilBERT + spaCy)."""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ai_karen_engine.clients.embedding_manager import EmbeddingManager
from ai_karen_engine.clients.nlp_service import NLPService
from ai_karen_engine.core.response_envelope import build_response_envelope
from ai_karen_engine.services.distilbert_service import DistilBertService
from ai_karen_engine.services.spacy_service import SpacyService
from ai_karen_engine.services.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)


class DegradedModeReason(Enum):
    """Reasons for entering degraded mode."""
    ALL_PROVIDERS_FAILED = "all_providers_failed"
    NETWORK_ISSUES = "network_issues"
    API_RATE_LIMITS = "api_rate_limits"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MANUAL_ACTIVATION = "manual_activation"


@dataclass
class DegradedModeStatus:
    """Status information for degraded mode."""
    is_active: bool
    reason: Optional[DegradedModeReason]
    activated_at: Optional[datetime]
    failed_providers: List[str]
    recovery_attempts: int
    last_recovery_attempt: Optional[datetime]
    core_helpers_available: Dict[str, bool]


class TinyLlamaHelper:
    """Enhanced TinyLlama helper with better text processing capabilities."""

    def __init__(self):
        self.templates = {
            "greeting": "Hello! I'm operating in degraded mode with limited capabilities.",
            "question": "I understand you're asking about: {topic}. Let me provide basic information.",
            "task": "I can help with basic tasks. Here's what I understand: {content}",
            "error": "I'm currently in degraded mode. My responses may be limited.",
            "general": "Based on your input: {content}, here's a basic response."
        }

    def generate_scaffold(self, text: str, max_tokens: int = 200) -> str:
        """Generate a basic response scaffold using simple heuristics."""
        text = text.strip()
        if not text:
            return self.templates["error"]
        
        # Simple intent detection - check in order of specificity
        if text.endswith("?") or any(word in text.lower() for word in ["what", "how", "why", "when", "where"]):
            topic = self._extract_topic(text)
            return self.templates["question"].format(topic=topic)
        elif any(word in text.lower() for word in ["help", "do", "create", "make", "build"]):
            content = text[:max_tokens//2]
            return self.templates["task"].format(content=content)
        elif any(f" {word} " in f" {text.lower()} " or text.lower().startswith(f"{word} ") or text.lower().endswith(f" {word}") or text.lower() == word for word in ["hello", "hi", "hey", "greetings"]):
            return self.templates["greeting"]
        else:
            content = text[:max_tokens//2]
            return self.templates["general"].format(content=content)

    def _extract_topic(self, text: str) -> str:
        """Extract main topic from text using simple keyword extraction."""
        # Remove question words and common words
        stop_words = {"what", "how", "why", "when", "where", "is", "are", "the", "a", "an", "and", "or", "but"}
        words = [word.lower().strip(".,!?") for word in text.split() if word.lower() not in stop_words]
        return " ".join(words[:3]) if words else "your question"


class DegradedModeManager:
    """Manages degraded mode state and core helper models."""

    def __init__(self):
        self.status = DegradedModeStatus(
            is_active=False,
            reason=None,
            activated_at=None,
            failed_providers=[],
            recovery_attempts=0,
            last_recovery_attempt=None,
            core_helpers_available={}
        )
        
        # Initialize core helpers
        self.tiny_llama = TinyLlamaHelper()
        self.distilbert_service = None
        self.spacy_service = None
        self.embedding_manager = None
        self.nlp_service = None
        self.metrics_service = get_metrics_service()
        
        # Initialize services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize core helper services with fallback handling."""

        # Heavy helpers (DistilBERT, spaCy, sentence transformers) attempt to
        # download large models when they are not cached locally. In restricted
        # or offline environments this blocks degraded-mode activation for tens
        # of seconds while the libraries retry network requests.  To keep the
        # platform responsive we default to a "minimal" degraded mode that only
        # uses the lightweight TinyLlama heuristics unless explicitly enabled.
        enable_heavy_helpers = (
            os.getenv("KARI_ENABLE_DEGRADED_HELPERS", "").lower()
            in {"1", "true", "yes"}
        )

        if not enable_heavy_helpers:
            # Ensure downstream libraries remain in offline/fallback mode so
            # they do not attempt network downloads later in the workflow.
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
            os.environ.setdefault("HF_HUB_OFFLINE", "1")

            logger.info(
                "Heavy degraded-mode helpers are disabled. Set "
                "KARI_ENABLE_DEGRADED_HELPERS=1 to load DistilBERT, spaCy, "
                "and embedding models when available."
            )
            self.status.core_helpers_available.update(
                {
                    "distilbert": False,
                    "spacy": False,
                    "embeddings": False,
                    "nlp": False,
                }
            )
        else:
            try:
                self.distilbert_service = DistilBertService()
                self.status.core_helpers_available["distilbert"] = True
                logger.info("DistilBERT service initialized for degraded mode")
            except Exception as e:
                logger.warning(f"Failed to initialize DistilBERT service: {e}")
                self.status.core_helpers_available["distilbert"] = False

            try:
                self.spacy_service = SpacyService()
                self.status.core_helpers_available["spacy"] = True
                logger.info("spaCy service initialized for degraded mode")
            except Exception as e:
                logger.warning(f"Failed to initialize spaCy service: {e}")
                self.status.core_helpers_available["spacy"] = False

            try:
                self.embedding_manager = EmbeddingManager()
                self.status.core_helpers_available["embeddings"] = True
                logger.info("Embedding manager initialized for degraded mode")
            except Exception as e:
                logger.warning(f"Failed to initialize embedding manager: {e}")
                self.status.core_helpers_available["embeddings"] = False

            try:
                self.nlp_service = NLPService()
                self.status.core_helpers_available["nlp"] = True
                logger.info("NLP service initialized for degraded mode")
            except Exception as e:
                logger.warning(f"Failed to initialize NLP service: {e}")
                self.status.core_helpers_available["nlp"] = False

        # TinyLlama is always available as it's a simple fallback
        self.status.core_helpers_available["tiny_llama"] = True

    def activate_degraded_mode(self, reason: DegradedModeReason, failed_providers: List[str] = None):
        """Activate degraded mode with specified reason."""
        if not self.status.is_active:
            self.status.is_active = True
            self.status.reason = reason
            self.status.activated_at = datetime.utcnow()
            self.status.failed_providers = failed_providers or []
            
            logger.warning(f"Degraded mode activated: {reason.value}, failed providers: {failed_providers}")
            
            # Record metrics
            self.metrics_service.record_copilot_request("degraded_mode_activated")
            
            # Send admin alert
            self._send_admin_alert("activated", reason, failed_providers)

    def deactivate_degraded_mode(self):
        """Deactivate degraded mode and return to normal operation."""
        if self.status.is_active:
            duration = (datetime.utcnow() - self.status.activated_at).total_seconds() if self.status.activated_at else 0
            
            self.status.is_active = False
            self.status.reason = None
            self.status.activated_at = None
            self.status.failed_providers = []
            self.status.recovery_attempts = 0
            self.status.last_recovery_attempt = None
            
            logger.info(f"Degraded mode deactivated after {duration:.1f} seconds")
            
            # Record metrics
            self.metrics_service.record_copilot_request("degraded_mode_deactivated")
            
            # Send admin alert
            self._send_admin_alert("deactivated", None, [])

    def attempt_recovery(self) -> bool:
        """Attempt to recover from degraded mode."""
        if not self.status.is_active:
            return True
        
        self.status.recovery_attempts += 1
        self.status.last_recovery_attempt = datetime.utcnow()
        
        logger.info(f"Attempting degraded mode recovery (attempt {self.status.recovery_attempts})")
        
        # Check if failed providers are now available
        # This would typically involve checking provider health
        # For now, we'll implement a simple recovery mechanism
        
        # Record recovery attempt
        self.metrics_service.record_copilot_request("degraded_mode_recovery_attempt")
        
        return False  # Recovery logic would be implemented here

    async def generate_degraded_response(self, user_input: str, **kwargs: Any) -> Dict[str, Any]:
        """Generate response using core helper models."""
        start_time = time.time()
        
        try:
            # Use TinyLlama for basic response scaffolding
            scaffold = self.tiny_llama.generate_scaffold(user_input)
            
            # Enhance with available services
            entities = []
            sentiment = "neutral"
            intent = "general"
            embeddings_used = False
            
            # Try to use spaCy for entity extraction and parsing
            if self.spacy_service and self.status.core_helpers_available.get("spacy", False):
                try:
                    parsed = await self.spacy_service.parse_message(user_input)
                    entities = [f"{text}({label})" for text, label in parsed.entities]
                    if parsed.dependencies:
                        # Simple intent detection from dependencies
                        verbs = [dep["text"] for dep in parsed.dependencies if dep["pos"] in ["VERB", "AUX"]]
                        if verbs:
                            intent = f"action_{verbs[0].lower()}"
                except Exception as e:
                    logger.debug(f"spaCy processing failed in degraded mode: {e}")
            
            # Try to use DistilBERT for embeddings and sentiment
            if self.distilbert_service and self.status.core_helpers_available.get("distilbert", False):
                try:
                    embeddings = await self.distilbert_service.get_embeddings(user_input)
                    if embeddings:
                        embeddings_used = True
                        # Simple sentiment based on embedding patterns (very basic)
                        avg_embedding = sum(embeddings) / len(embeddings)
                        sentiment = "positive" if avg_embedding > 0.1 else "negative" if avg_embedding < -0.1 else "neutral"
                except Exception as e:
                    logger.debug(f"DistilBERT processing failed in degraded mode: {e}")
            
            # Fallback to basic NLP service if available
            if not entities and self.nlp_service and self.status.core_helpers_available.get("nlp", False):
                try:
                    entities = self.nlp_service.extract_entities(user_input)
                except Exception as e:
                    logger.debug(f"NLP service failed in degraded mode: {e}")
            
            # Construct enhanced response
            response_parts = [scaffold]
            
            if entities:
                response_parts.append(f"\nDetected entities: {', '.join(entities)}")
            
            response_parts.append(f"\nIntent: {intent}")
            response_parts.append(f"Sentiment: {sentiment}")
            
            if embeddings_used:
                response_parts.append("Enhanced with semantic understanding.")
            
            response_parts.append("\n\n⚠️ Note: I'm currently operating in degraded mode with limited capabilities. Some features may not be available.")
            
            combined_response = "".join(response_parts)
            
            # Build metadata
            metadata = {
                "annotations": ["Degraded Mode", f"Reason: {self.status.reason.value if self.status.reason else 'unknown'}"],
                "confidence": 0.4,  # Lower confidence in degraded mode
                "provider": "CoreHelpers",
                "helpers_used": [name for name, available in self.status.core_helpers_available.items() if available],
                "processing_time": time.time() - start_time,
                "degraded_mode_active": True,
                "recovery_attempts": self.status.recovery_attempts
            }
            
            # Record metrics
            self.metrics_service.record_llm_latency(
                time.time() - start_time,
                provider="degraded_mode",
                model="core_helpers",
                status="success"
            )
            
            return build_response_envelope(combined_response, "CoreHelpers", "degraded", metadata=metadata)
            
        except Exception as e:
            logger.error(f"Degraded mode response generation failed: {e}")
            
            # Ultra-fallback response
            fallback_response = f"I apologize, but I'm experiencing technical difficulties. Your input was: {user_input[:100]}..."
            metadata = {
                "annotations": ["Degraded Mode - Ultra Fallback"],
                "confidence": 0.1,
                "provider": "UltraFallback",
                "error": str(e),
                "processing_time": time.time() - start_time
            }
            
            self.metrics_service.record_llm_latency(
                time.time() - start_time,
                provider="degraded_mode",
                model="ultra_fallback",
                status="error"
            )
            
            return build_response_envelope(fallback_response, "UltraFallback", "error", metadata=metadata)

    def _send_admin_alert(self, event_type: str, reason: Optional[DegradedModeReason], failed_providers: List[str]):
        """Send admin alert for degraded mode events."""
        try:
            alert_data = {
                "event": f"degraded_mode_{event_type}",
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason.value if reason else None,
                "failed_providers": failed_providers,
                "core_helpers_status": self.status.core_helpers_available,
                "recovery_attempts": self.status.recovery_attempts
            }
            
            # Log structured alert for monitoring systems
            logger.warning(
                f"ADMIN_ALERT: Degraded mode {event_type}",
                extra={
                    "alert_type": "degraded_mode",
                    "event_type": event_type,
                    "alert_data": alert_data
                }
            )
            
            # Record in metrics for alerting systems
            self.metrics_service.record_copilot_request(
                f"admin_alert_degraded_mode_{event_type}",
                correlation_id=f"degraded_mode_{int(time.time())}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send admin alert: {e}")

    def get_status(self) -> DegradedModeStatus:
        """Get current degraded mode status."""
        return self.status

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of core helpers."""
        health_summary = {
            "degraded_mode_active": self.status.is_active,
            "core_helpers": {}
        }
        
        if self.distilbert_service:
            try:
                health_summary["core_helpers"]["distilbert"] = self.distilbert_service.get_health_status().__dict__
            except Exception:
                health_summary["core_helpers"]["distilbert"] = {"error": "health_check_failed"}
        
        if self.spacy_service:
            try:
                health_summary["core_helpers"]["spacy"] = self.spacy_service.get_health_status().__dict__
            except Exception:
                health_summary["core_helpers"]["spacy"] = {"error": "health_check_failed"}
        
        health_summary["core_helpers"]["tiny_llama"] = {"is_healthy": True, "fallback_mode": False}
        
        return health_summary


# Global degraded mode manager instance
_degraded_mode_manager: Optional[DegradedModeManager] = None


def get_degraded_mode_manager() -> DegradedModeManager:
    """Get global degraded mode manager instance."""
    global _degraded_mode_manager
    if _degraded_mode_manager is None:
        _degraded_mode_manager = DegradedModeManager()
    return _degraded_mode_manager


# Legacy function for backward compatibility
def generate_degraded_mode_response(user_input: str, **kwargs: Any) -> Dict[str, Any]:
    """Generate a response using helper models only (legacy function)."""
    manager = get_degraded_mode_manager()
    
    # Run async function in sync context
    loop = None
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If we're already in an async context, create a new task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, manager.generate_degraded_response(user_input, **kwargs))
            return future.result()
    else:
        return loop.run_until_complete(manager.generate_degraded_response(user_input, **kwargs))
