# mypy: ignore-errors
"""
Debug and development endpoints for Kari FastAPI Server.
Handles debug, dev warnings, service initialization, and reasoning endpoints.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI
from .config import Settings

logger = logging.getLogger("kari")


def register_debug_endpoints(app: FastAPI, settings: Settings) -> None:
    """Register all debug and development endpoints"""
    
    @app.get("/api/system/dev-warnings", tags=["system"])
    async def get_dev_warnings():
        """Report missing optional dev dependencies/integrations and fixes."""
        results: Dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat()}

        # RBAC
        try:
            import ai_karen_engine.core.rbac as rbac  # type: ignore
            ok = hasattr(rbac, "check_scopes") or hasattr(rbac, "check_rbac_scope")
            results["rbac"] = {"available": bool(ok)}
        except Exception as e:
            results["rbac"] = {"available": False, "reason": str(e), "resolution": "pip install rbac component or enable production auth"}

        # Correlation / enhanced logger presence (best-effort)
        try:
            import ai_karen_engine.server.middleware as mw  # type: ignore
            configured = bool(getattr(mw, "_enhanced_logger", None))
            results["correlation_logging"] = {"configured": configured}
        except Exception as e:
            results["correlation_logging"] = {"configured": False, "reason": str(e)}

        # OpenTelemetry
        try:
            import opentelemetry  # type: ignore
            from opentelemetry import trace  # type: ignore
            results["opentelemetry"] = {"installed": True}
        except Exception as e:
            results["opentelemetry"] = {"installed": False, "reason": str(e), "resolution": "pip install opentelemetry-sdk opentelemetry-api"}

        # watchdog
        try:
            import watchdog  # type: ignore
            results["watchdog"] = {"installed": True}
        except Exception as e:
            results["watchdog"] = {"installed": False, "reason": str(e), "resolution": "pip install watchdog"}

        # jsonschema
        try:
            import jsonschema  # type: ignore
            results["jsonschema"] = {"installed": True}
        except Exception as e:
            results["jsonschema"] = {"installed": False, "reason": str(e), "resolution": "pip install jsonschema"}

        # Redis connectivity/auth
        redis_url = os.getenv("REDIS_URL")
        redis_status: Dict[str, Any] = {"configured": bool(redis_url)}
        try:
            if redis_url:
                try:
                    import redis  # type: ignore
                    client = redis.Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
                    pong = client.ping()
                    redis_status.update({"reachable": bool(pong), "auth_ok": True})
                except Exception as re:
                    msg = str(re)
                    auth_ok = not ("AUTH" in msg or "Authentication" in msg)
                    redis_status.update({"reachable": False, "auth_ok": auth_ok, "error": msg, "resolution": "Set REDIS_URL with password e.g. redis://:pass@host:6379/0"})
            else:
                redis_status.update({"reachable": False, "auth_ok": None, "resolution": "Set REDIS_URL to enable Redis-backed caching"})
        except Exception as e:
            redis_status.update({"error": str(e)})
        results["redis"] = redis_status

        # Silencing flag
        _silence_dev = os.getenv("KAREN_SILENCE_DEV_WARNINGS", "false").lower() in ("1", "true", "yes")
        results["silence_dev_warnings"] = {"enabled": _silence_dev, "env": "KAREN_SILENCE_DEV_WARNINGS"}

        return results
    
    @app.get("/api/debug/services", tags=["debug"])
    async def debug_services():
        """Debug endpoint to check service registry status"""
        try:
            from ai_karen_engine.core.service_registry import get_service_registry
            registry = get_service_registry()
            services = registry.list_services()
            
            return {
                "services": services,
                "total_services": len(services),
                "ready_services": len([s for s in services.values() if s.get("status") == "ready"]),
                "registry_type": str(type(registry))
            }
        except Exception as e:
            return {"error": str(e), "services": {}}
    
    @app.post("/api/debug/initialize-services", tags=["debug"])
    async def initialize_services_endpoint():
        """Manually initialize services"""
        try:
            from ai_karen_engine.core.service_registry import initialize_services, get_service_registry
            
            logger.info("Manual service initialization requested")
            await initialize_services()
            
            registry = get_service_registry()
            services = registry.list_services()
            report = registry.get_initialization_report()
            
            return {
                "success": True,
                "message": "Services initialized successfully",
                "services": services,
                "report": report
            }
        except Exception as e:
            logger.error(f"Manual service initialization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @app.post("/api/reasoning/analyze", tags=["reasoning"])
    async def analyze_with_reasoning(request: dict):
        """Analyze user input using the reasoning system with fallbacks"""
        try:
            user_input = request.get("input", "")
            context = request.get("context", {})
            
            # Try AI-powered reasoning first
            try:
                from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
                from ai_karen_engine.core.service_registry import ServiceRegistry, get_service_registry
                
                # Use the global service registry and ensure it's initialized
                registry = get_service_registry()
                
                # Check if services are initialized, if not initialize them
                services = registry.list_services()
                logger.info(f"Available services: {list(services.keys())}")
                
                if "ai_orchestrator" not in services or not services:
                    logger.info("Initializing services for reasoning endpoint...")
                    from ai_karen_engine.core.service_registry import initialize_services
                    await initialize_services()
                    logger.info("Services initialized successfully")
                    # Refresh services list after initialization
                    services = registry.list_services()
                
                # Verify ai_orchestrator is available and ready
                if "ai_orchestrator" not in services:
                    raise Exception("ai_orchestrator service not available after initialization")
                
                service_info = services["ai_orchestrator"]
                if service_info.get("status") != "ready":
                    raise Exception(f"ai_orchestrator service not ready: {service_info.get('status')}")
                
                ai_orchestrator = await registry.get_service("ai_orchestrator")
                logger.info("AI orchestrator retrieved successfully")
                
                # Use AI orchestrator for reasoning
                from ai_karen_engine.models.shared_types import FlowInput
                
                flow_input = FlowInput(
                    prompt=user_input,
                    context=context,
                    user_id=context.get("user_id", "anonymous"),
                    conversation_history=context.get("conversation_history", []),
                    user_settings=context.get("user_settings", {})
                )
                
                flow_output = await ai_orchestrator.conversation_processing_flow(flow_input)
                response = flow_output.response if hasattr(flow_output, 'response') else str(flow_output)
                
                return {
                    "success": True,
                    "response": response,
                    "reasoning_method": "ai_orchestrator",
                    "fallback_used": False
                }
                
            except Exception as ai_error:
                logger.warning(f"AI reasoning failed, using fallback: {ai_error}")
                
                # Fallback to local reasoning
                try:
                    from ai_karen_engine.core.degraded_mode import generate_degraded_mode_response
                    
                    # Call the sync function properly
                    fallback_response = generate_degraded_mode_response(
                        user_input=user_input,
                        context=context
                    )
                    
                    return {
                        "success": True,
                        "response": fallback_response,
                        "reasoning_method": "local_fallback",
                        "fallback_used": True,
                        "ai_error": str(ai_error)
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback reasoning failed: {fallback_error}")
                    
                    # Ultimate fallback - enhanced simple response
                    def generate_simple_response(text: str) -> str:
                        """Generate a more helpful simple response."""
                        text = text.strip().lower()
                        
                        # Coding questions
                        if any(word in text for word in ["function", "code", "python", "javascript", "programming", "algorithm"]):
                            return f"I can help with coding questions! You asked about: {user_input}\n\nWhile I'm in fallback mode, I can still provide basic guidance. For coding tasks, I recommend:\n1. Breaking down the problem into smaller steps\n2. Using clear variable names\n3. Adding comments to explain your logic\n4. Testing your code incrementally\n\nWhat specific aspect would you like help with?"
                        
                        # Questions
                        elif text.endswith("?") or any(word in text for word in ["what", "how", "why", "when", "where", "help"]):
                            return f"I understand you're asking: {user_input}\n\nI'm currently in fallback mode with limited capabilities, but I'll do my best to help. Could you provide more specific details about what you need assistance with?"
                        
                        # Greetings
                        elif any(word in text for word in ["hello", "hi", "hey", "greetings"]):
                            return "Hello! I'm Karen, your AI assistant. I'm currently running in fallback mode, which means some advanced features aren't available, but I'm still here to help with basic questions and tasks. What can I assist you with today?"
                        
                        # Tasks/requests
                        elif any(word in text for word in ["create", "make", "build", "write", "generate"]):
                            return f"I'd be happy to help you with: {user_input}\n\nI'm currently in fallback mode, so my responses may be more basic than usual. Could you break down what you need into specific steps? This will help me provide better assistance."
                        
                        # Default
                        else:
                            return f"I received your message: {user_input}\n\nI'm currently operating in fallback mode with limited capabilities. While I may not be able to provide my full range of assistance, I'm still here to help as best I can. Could you rephrase your request or ask a more specific question?"
                    
                    simple_content = generate_simple_response(user_input)
                    
                    return {
                        "success": True,
                        "response": {
                            "content": simple_content,
                            "type": "text",
                            "metadata": {
                                "fallback_mode": True,
                                "local_processing": True,
                                "enhanced_simple_response": True
                            }
                        },
                        "reasoning_method": "enhanced_simple_fallback",
                        "fallback_used": True,
                        "errors": {
                            "ai_error": str(ai_error),
                            "fallback_error": str(fallback_error)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Reasoning endpoint error: {e}")
            return {
                "success": False,
                "error": str(e),
                "reasoning_method": "error",
                "fallback_used": True
            }