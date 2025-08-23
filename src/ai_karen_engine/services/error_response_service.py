"""
Intelligent Error Response Service

This service provides intelligent analysis and user-friendly responses for errors
that occur in the AI Karen system. It leverages rule-based classification and
AI-powered response generation to provide actionable guidance to users.
"""

import logging
import re
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from pydantic import BaseModel, Field

from ai_karen_engine.models.web_api_error_responses import WebAPIErrorCode
from ai_karen_engine.services.llm_router import ProviderHealth
from ai_karen_engine.services.provider_health_monitor import (
    get_health_monitor, 
    ProviderHealthInfo,
    HealthStatus
)
from ai_karen_engine.core.cache import get_response_cache, get_request_deduplicator
from ai_karen_engine.services.audit_logging import get_audit_logger

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories for error classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    API_KEY_MISSING = "api_key_missing"
    API_KEY_INVALID = "api_key_invalid"
    RATE_LIMIT = "rate_limit"
    PROVIDER_DOWN = "provider_down"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for error analysis"""
    error_message: str
    error_type: Optional[str] = None
    status_code: Optional[int] = None
    provider_name: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    request_path: Optional[str] = None
    timestamp: Optional[datetime] = None
    additional_data: Optional[Dict[str, Any]] = None


class IntelligentErrorResponse(BaseModel):
    """Intelligent error response model"""
    title: str = Field(..., description="Brief, user-friendly error title")
    summary: str = Field(..., description="Clear explanation of what went wrong")
    category: ErrorCategory = Field(..., description="Error category for classification")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    next_steps: List[str] = Field(..., description="Actionable steps to resolve the issue")
    provider_health: Optional[Dict[str, Any]] = Field(None, description="Current provider health status")
    contact_admin: bool = Field(False, description="Whether user should contact admin")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")
    help_url: Optional[str] = Field(None, description="URL to relevant documentation")
    technical_details: Optional[str] = Field(None, description="Technical details for debugging")


class ErrorClassificationRule:
    """Rule for classifying errors"""
    
    def __init__(
        self,
        name: str,
        patterns: List[str],
        category: ErrorCategory,
        severity: ErrorSeverity,
        title_template: str,
        summary_template: str,
        next_steps: List[str],
        contact_admin: bool = False,
        retry_after: Optional[int] = None,
        help_url: Optional[str] = None
    ):
        self.name = name
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        self.category = category
        self.severity = severity
        self.title_template = title_template
        self.summary_template = summary_template
        self.next_steps = next_steps
        self.contact_admin = contact_admin
        self.retry_after = retry_after
        self.help_url = help_url
    
    def matches(self, error_message: str, error_type: Optional[str] = None) -> bool:
        """Check if this rule matches the given error"""
        text_to_check = f"{error_message} {error_type or ''}"
        return any(pattern.search(text_to_check) for pattern in self.patterns)
    
    def format_response(self, context: ErrorContext) -> Dict[str, Any]:
        """Format the response using context data"""
        return {
            "title": self._format_template(self.title_template, context),
            "summary": self._format_template(self.summary_template, context),
            "category": self.category,
            "severity": self.severity,
            "next_steps": [self._format_template(step, context) for step in self.next_steps],
            "contact_admin": self.contact_admin,
            "retry_after": self.retry_after,
            "help_url": self.help_url
        }
    
    def _format_template(self, template: str, context: ErrorContext) -> str:
        """Format template string with context data"""
        replacements = {
            "{provider}": context.provider_name or "the provider",
            "{error_type}": context.error_type or "error",
            "{status_code}": str(context.status_code) if context.status_code else "unknown"
        }
        
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result


class ErrorResponseService:
    """Service for generating intelligent error responses"""
    
    def __init__(self):
        self.classification_rules = self._initialize_classification_rules()
        self._provider_health_cache: Dict[str, ProviderHealth] = {}
        self._cache_ttl = 300  # 5 minutes
        self._ai_orchestrator = None  # Lazy initialization to avoid circular imports
        self._llm_router = None  # Lazy initialization
        self._llm_utils = None  # Lazy initialization
        self._response_cache = get_response_cache()
        self._deduplicator = get_request_deduplicator()
        self.logger = logging.getLogger(__name__)
        self._audit_logger = get_audit_logger()
    
    def _get_ai_orchestrator(self):
        """Lazily initialize AI orchestrator to avoid circular imports."""
        if self._ai_orchestrator is None:
            try:
                from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
                from ai_karen_engine.core.services.base import ServiceConfig
                config = ServiceConfig(name="error_response_ai_orchestrator")
                self._ai_orchestrator = AIOrchestrator(config)
                # Initialize without full startup to avoid dependencies
                self._ai_orchestrator._initialized = True
            except Exception as e:
                self.logger.warning(f"Failed to initialize AI orchestrator: {e}")
                self._ai_orchestrator = None
        return self._ai_orchestrator
    
    def _get_llm_router(self):
        """Lazily initialize LLM router to avoid circular imports."""
        if self._llm_router is None:
            try:
                from ai_karen_engine.integrations.llm_router import LLMProfileRouter
                self._llm_router = LLMProfileRouter()
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM router: {e}")
                self._llm_router = None
        return self._llm_router
    
    def _get_llm_utils(self):
        """Lazily initialize LLM utils to avoid circular imports."""
        if self._llm_utils is None:
            try:
                from ai_karen_engine.integrations.llm_utils import LLMUtils
                self._llm_utils = LLMUtils()
            except Exception as e:
                self.logger.warning(f"Failed to initialize LLM utils: {e}")
                self._llm_utils = None
        return self._llm_utils
    
    def _initialize_classification_rules(self) -> List[ErrorClassificationRule]:
        """Initialize error classification rules"""
        return [
            # Authentication errors
            ErrorClassificationRule(
                name="session_expired",
                patterns=[
                    r"token.*expired",
                    r"session.*expired",
                    r"authentication.*expired"
                ],
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                title_template="Session Expired",
                summary_template="Your session has expired and you need to log in again.",
                next_steps=[
                    "Click the login button to sign in again",
                    "Your work will be saved automatically"
                ]
            ),
            
            ErrorClassificationRule(
                name="invalid_credentials",
                patterns=[
                    r"invalid.*credentials",
                    r"authentication.*failed",
                    r"login.*failed",
                    r"unauthorized"
                ],
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                title_template="Login Failed",
                summary_template="The email or password you entered is incorrect.",
                next_steps=[
                    "Double-check your email address and password",
                    "Use the 'Forgot Password' link if needed",
                    "Contact admin if you continue having issues"
                ]
            ),
            
            # API Key errors
            ErrorClassificationRule(
                name="openai_api_key_missing",
                patterns=[
                    r"openai.*api.*key.*not.*found",
                    r"openai.*api.*key.*missing",
                    r"OPENAI_API_KEY.*not.*set"
                ],
                category=ErrorCategory.API_KEY_MISSING,
                severity=ErrorSeverity.HIGH,
                title_template="OpenAI API Key Missing",
                summary_template="The OpenAI API key is not configured in your environment.",
                next_steps=[
                    "Add OPENAI_API_KEY to your .env file",
                    "Get your API key from https://platform.openai.com/api-keys",
                    "Restart the application after adding the key"
                ],
                help_url="https://platform.openai.com/docs/quickstart"
            ),
            
            ErrorClassificationRule(
                name="anthropic_api_key_missing",
                patterns=[
                    r"anthropic.*api.*key.*not.*found",
                    r"anthropic.*api.*key.*missing",
                    r"ANTHROPIC_API_KEY.*not.*set"
                ],
                category=ErrorCategory.API_KEY_MISSING,
                severity=ErrorSeverity.HIGH,
                title_template="Anthropic API Key Missing",
                summary_template="The Anthropic API key is not configured in your environment.",
                next_steps=[
                    "Add ANTHROPIC_API_KEY to your .env file",
                    "Get your API key from https://console.anthropic.com/",
                    "Restart the application after adding the key"
                ],
                help_url="https://docs.anthropic.com/claude/docs/getting-access"
            ),
            
            ErrorClassificationRule(
                name="api_key_invalid",
                patterns=[
                    r"api.*key.*invalid",
                    r"invalid.*api.*key",
                    r"authentication.*failed.*api.*key",
                    r"401.*unauthorized.*api.*key"
                ],
                category=ErrorCategory.API_KEY_INVALID,
                severity=ErrorSeverity.HIGH,
                title_template="Invalid API Key",
                summary_template="The {provider} API key appears to be invalid or expired.",
                next_steps=[
                    "Verify your {provider} API key is correct",
                    "Check if your API key has expired",
                    "Generate a new API key if needed",
                    "Update your .env file with the new key"
                ]
            ),
            
            # Rate limiting
            ErrorClassificationRule(
                name="rate_limit_exceeded",
                patterns=[
                    r"rate.*limit.*exceeded",
                    r"too.*many.*requests",
                    r"quota.*exceeded",
                    r"429.*too.*many.*requests"
                ],
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                title_template="Rate Limit Exceeded",
                summary_template="You've exceeded the rate limit for {provider}.",
                next_steps=[
                    "Wait a few minutes before trying again",
                    "Consider upgrading your {provider} plan for higher limits",
                    "Try using a different provider if available"
                ],
                retry_after=300  # 5 minutes
            ),
            
            # Database errors (must come before provider errors to avoid conflicts)
            ErrorClassificationRule(
                name="database_connection_error",
                patterns=[
                    r"database.*connection.*failed",
                    r"database.*connection.*refused",
                    r"could.*not.*connect.*database"
                ],
                category=ErrorCategory.DATABASE_ERROR,
                severity=ErrorSeverity.CRITICAL,
                title_template="Database Connection Failed",
                summary_template="Unable to connect to the database.",
                next_steps=[
                    "Contact admin immediately",
                    "Check if database service is running"
                ],
                contact_admin=True
            ),
            
            ErrorClassificationRule(
                name="missing_database_table",
                patterns=[
                    r"relation.*does.*not.*exist",
                    r"table.*does.*not.*exist",
                    r"missing.*table"
                ],
                category=ErrorCategory.DATABASE_ERROR,
                severity=ErrorSeverity.CRITICAL,
                title_template="Database Not Initialized",
                summary_template="Required database tables are missing.",
                next_steps=[
                    "Contact admin to run database migrations",
                    "System needs to be properly initialized"
                ],
                contact_admin=True
            ),
            
            # Provider/Network errors
            ErrorClassificationRule(
                name="provider_unavailable",
                patterns=[
                    r"service.*unavailable",
                    r"provider.*unavailable",
                    r"connection.*refused",
                    r"503.*service.*unavailable"
                ],
                category=ErrorCategory.PROVIDER_DOWN,
                severity=ErrorSeverity.HIGH,
                title_template="Service Temporarily Unavailable",
                summary_template="The {provider} service is currently unavailable.",
                next_steps=[
                    "Try again in a few minutes",
                    "Check {provider} status page for updates",
                    "Use an alternative provider if configured"
                ],
                retry_after=180  # 3 minutes
            ),
            
            ErrorClassificationRule(
                name="network_timeout",
                patterns=[
                    r"timeout",
                    r"connection.*timeout",
                    r"request.*timeout",
                    r"504.*gateway.*timeout"
                ],
                category=ErrorCategory.NETWORK_ERROR,
                severity=ErrorSeverity.MEDIUM,
                title_template="Request Timeout",
                summary_template="The request timed out while waiting for a response.",
                next_steps=[
                    "Check your internet connection",
                    "Try again in a moment",
                    "Contact admin if timeouts persist"
                ],
                retry_after=60  # 1 minute
            ),
            

            
            # Validation errors
            ErrorClassificationRule(
                name="validation_error",
                patterns=[
                    r"validation.*failed",
                    r"invalid.*input",
                    r"required.*field.*missing",
                    r"400.*bad.*request"
                ],
                category=ErrorCategory.VALIDATION_ERROR,
                severity=ErrorSeverity.LOW,
                title_template="Invalid Input",
                summary_template="The information you provided is not valid.",
                next_steps=[
                    "Check that all required fields are filled",
                    "Verify the format of your input",
                    "Try again with corrected information"
                ]
            )
        ]
    
    def analyze_error(
        self,
        error_message: str,
        error_type: Optional[str] = None,
        status_code: Optional[int] = None,
        provider_name: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        use_ai_analysis: bool = True
    ) -> IntelligentErrorResponse:
        """
        Analyze an error and generate an intelligent response with caching
        
        Args:
            error_message: The error message to analyze
            error_type: Optional error type/class name
            status_code: Optional HTTP status code
            provider_name: Optional provider name that caused the error
            additional_context: Optional additional context data
            use_ai_analysis: Whether to use AI-powered analysis for enhanced responses
            
        Returns:
            IntelligentErrorResponse with analysis and guidance
        """
        # Check cache first for common error patterns
        cached_response = self._response_cache.get_cached_response(
            error_message, error_type, provider_name
        )
        if cached_response:
            logger.debug("Serving cached error response")
            
            # Audit log cache hit
            self._audit_logger.log_response_cache_event(
                cache_hit=True,
                error_category=cached_response.get("category"),
                additional_context=additional_context
            )
            
            return IntelligentErrorResponse(**cached_response)

        context = ErrorContext(
            error_message=error_message,
            error_type=error_type,
            status_code=status_code,
            provider_name=provider_name,
            timestamp=datetime.utcnow(),
            additional_data=additional_context
        )
        
        # Try to classify the error using rules
        for rule in self.classification_rules:
            if rule.matches(error_message, error_type):
                logger.info(f"Error classified as: {rule.name}")
                response_data = rule.format_response(context)
                
                # Add provider health information if available
                if provider_name:
                    provider_health = self._get_provider_health(provider_name)
                    if provider_health:
                        response_data["provider_health"] = {
                            "name": provider_health.name,
                            "status": provider_health.status.value,
                            "success_rate": provider_health.success_rate,
                            "response_time": provider_health.response_time,
                            "error_message": provider_health.error_message,
                            "last_check": provider_health.last_check.isoformat() if provider_health.last_check else None
                        }
                        
                        # Add alternative provider suggestions if current provider is unhealthy
                        if provider_health.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
                            health_monitor = get_health_monitor()
                            alternatives = health_monitor.get_alternative_providers(provider_name)
                            if alternatives:
                                response_data["next_steps"].append(
                                    f"Try using {alternatives[0]} as an alternative provider"
                                )
                
                # Enhance with AI analysis if requested and available
                if use_ai_analysis:
                    enhanced_response = self._enhance_response_with_ai(
                        IntelligentErrorResponse(**response_data), context
                    )
                    if enhanced_response:
                        # Audit log AI-enhanced response
                        self._audit_logger.log_error_response_generated(
                            error_category=enhanced_response.category.value,
                            error_severity=enhanced_response.severity.value,
                            provider_name=provider_name,
                            ai_analysis_used=True,
                            response_cached=True,
                            user_id=additional_context.get("user_id") if additional_context else None,
                            tenant_id=additional_context.get("tenant_id") if additional_context else None,
                            correlation_id=additional_context.get("correlation_id") if additional_context else None
                        )
                        
                        # Cache enhanced response
                        self._cache_response_if_cacheable(enhanced_response, error_message, error_type, provider_name)
                        return enhanced_response
                
                response = IntelligentErrorResponse(**response_data)
                
                # Audit log rule-based response
                self._audit_logger.log_error_response_generated(
                    error_category=response.category.value,
                    error_severity=response.severity.value,
                    provider_name=provider_name,
                    ai_analysis_used=False,
                    response_cached=True,
                    user_id=additional_context.get("user_id") if additional_context else None,
                    tenant_id=additional_context.get("tenant_id") if additional_context else None,
                    correlation_id=additional_context.get("correlation_id") if additional_context else None
                )
                
                # Cache rule-based response
                self._cache_response_if_cacheable(response, error_message, error_type, provider_name)
                return response
        
        # For unclassified errors, try AI analysis first if available
        if use_ai_analysis:
            ai_response = self._generate_ai_error_response(context)
            if ai_response:
                # Audit log AI-generated response
                self._audit_logger.log_error_response_generated(
                    error_category=ai_response.category.value,
                    error_severity=ai_response.severity.value,
                    provider_name=provider_name,
                    ai_analysis_used=True,
                    response_cached=True,
                    user_id=additional_context.get("user_id") if additional_context else None,
                    tenant_id=additional_context.get("tenant_id") if additional_context else None,
                    correlation_id=additional_context.get("correlation_id") if additional_context else None
                )
                
                # Cache AI-generated response
                self._cache_response_if_cacheable(ai_response, error_message, error_type, provider_name)
                return ai_response
        
        # Fallback for unclassified errors
        logger.warning(f"Unclassified error: {error_message}")
        fallback_response = self._create_fallback_response(context)
        # Don't cache fallback responses as they're generic
        return fallback_response
    
    def _create_fallback_response(self, context: ErrorContext) -> IntelligentErrorResponse:
        """Create a fallback response for unclassified errors"""
        response_data = {
            "title": "Unexpected Error",
            "summary": "An unexpected error occurred while processing your request.",
            "category": ErrorCategory.UNKNOWN,
            "severity": ErrorSeverity.MEDIUM,
            "next_steps": [
                "Try refreshing the page",
                "Check your internet connection",
                "Contact admin if the problem persists"
            ],
            "contact_admin": True,
            "technical_details": f"Error: {context.error_message}"
        }
        
        # Add provider health information if available
        if context.provider_name:
            provider_health = self._get_provider_health(context.provider_name)
            if provider_health:
                response_data["provider_health"] = {
                    "name": provider_health.name,
                    "status": provider_health.status.value,
                    "success_rate": provider_health.success_rate,
                    "response_time": provider_health.response_time,
                    "error_message": provider_health.error_message,
                    "last_check": provider_health.last_check.isoformat() if provider_health.last_check else None
                }
        
        return IntelligentErrorResponse(**response_data)
    
    def _get_provider_health(self, provider_name: str) -> Optional[ProviderHealthInfo]:
        """Get cached provider health status"""
        health_monitor = get_health_monitor()
        return health_monitor.get_provider_health(provider_name)
    
    def _cache_response_if_cacheable(
        self, 
        response: IntelligentErrorResponse, 
        error_message: str, 
        error_type: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> None:
        """Cache response if it's a cacheable error type"""
        # Cache responses for stable error categories
        cacheable_categories = [
            ErrorCategory.API_KEY_MISSING,
            ErrorCategory.API_KEY_INVALID,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.VALIDATION_ERROR,
            ErrorCategory.RATE_LIMIT
        ]
        
        if response.category in cacheable_categories:
            response_dict = {
                "title": response.title,
                "summary": response.summary,
                "category": response.category,
                "severity": response.severity,
                "next_steps": response.next_steps,
                "provider_health": response.provider_health,
                "contact_admin": response.contact_admin,
                "retry_after": response.retry_after,
                "help_url": response.help_url,
                "technical_details": response.technical_details
            }
            
            self._response_cache.cache_response(
                error_message, response_dict, error_type, provider_name
            )
            logger.debug(f"Cached response for error category: {response.category}")
            
            # Audit log response caching
            self._audit_logger.log_response_cache_event(
                cache_hit=False,
                error_category=response.category.value
            )
    
    def _generate_ai_error_response(self, context: ErrorContext) -> Optional[IntelligentErrorResponse]:
        """Generate an AI-powered error response for unclassified errors"""
        try:
            llm_router = self._get_llm_router()
            llm_utils = self._get_llm_utils()
            
            if not llm_router or not llm_utils:
                self.logger.warning("LLM components not available for AI error analysis")
                return None
            
            # Build context for AI analysis
            analysis_context = self._build_error_analysis_context(context)
            
            # Generate AI analysis using error analysis prompt template
            analysis_prompt = self._build_error_analysis_prompt(context, analysis_context)
            
            self.logger.info("Generating AI-powered error analysis")
            
            # Audit log AI analysis request
            self._audit_logger.log_ai_analysis_requested(
                error_message=context.error_message,
                provider_name=context.provider_name,
                user_id=context.additional_data.get("user_id") if context.additional_data else None,
                tenant_id=context.additional_data.get("tenant_id") if context.additional_data else None,
                correlation_id=context.additional_data.get("correlation_id") if context.additional_data else None
            )
            
            # Use LLM router to get analysis
            start_time = time.time()
            ai_response = llm_router.invoke(
                llm_utils,
                analysis_prompt,
                task_intent="analysis",
                preferred_provider="openai",  # Use reliable provider for error analysis
                preferred_model="gpt-3.5-turbo"
            )
            generation_time_ms = (time.time() - start_time) * 1000
            
            if ai_response and ai_response.strip():
                # Parse and validate AI response
                parsed_response = self._parse_ai_error_response(ai_response, context)
                if parsed_response:
                    self.logger.info("Successfully generated AI-powered error response")
                    
                    # Audit log successful AI analysis
                    self._audit_logger.log_ai_analysis_completed(
                        success=True,
                        llm_provider="openai",
                        llm_model="gpt-3.5-turbo",
                        generation_time_ms=generation_time_ms,
                        user_id=context.additional_data.get("user_id") if context.additional_data else None,
                        tenant_id=context.additional_data.get("tenant_id") if context.additional_data else None,
                        correlation_id=context.additional_data.get("correlation_id") if context.additional_data else None
                    )
                    
                    return parsed_response
            
            self.logger.warning("AI error analysis returned empty or invalid response")
            
            # Audit log failed AI analysis
            self._audit_logger.log_ai_analysis_completed(
                success=False,
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                generation_time_ms=generation_time_ms,
                user_id=context.additional_data.get("user_id") if context.additional_data else None,
                tenant_id=context.additional_data.get("tenant_id") if context.additional_data else None,
                correlation_id=context.additional_data.get("correlation_id") if context.additional_data else None,
                error_message="Empty or invalid AI response"
            )
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI error analysis failed: {e}")
            
            # Audit log AI analysis failure
            self._audit_logger.log_ai_analysis_completed(
                success=False,
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                generation_time_ms=0,
                user_id=context.additional_data.get("user_id") if context.additional_data else None,
                tenant_id=context.additional_data.get("tenant_id") if context.additional_data else None,
                correlation_id=context.additional_data.get("correlation_id") if context.additional_data else None,
                error_message=str(e)
            )
            
            return None
    
    def _enhance_response_with_ai(
        self, 
        base_response: IntelligentErrorResponse, 
        context: ErrorContext
    ) -> Optional[IntelligentErrorResponse]:
        """Enhance a rule-based response with AI-generated insights"""
        try:
            llm_router = self._get_llm_router()
            llm_utils = self._get_llm_utils()
            
            if not llm_router or not llm_utils:
                return None
            
            # Build enhancement context
            analysis_context = self._build_error_analysis_context(context)
            
            # Generate enhancement prompt
            enhancement_prompt = self._build_error_enhancement_prompt(
                base_response, context, analysis_context
            )
            
            self.logger.info("Enhancing error response with AI insights")
            
            # Use LLM router to get enhancement
            ai_enhancement = llm_router.invoke(
                llm_utils,
                enhancement_prompt,
                task_intent="analysis",
                preferred_provider="openai",
                preferred_model="gpt-3.5-turbo"
            )
            
            if ai_enhancement and ai_enhancement.strip():
                # Parse and merge AI enhancement with base response
                enhanced_response = self._merge_ai_enhancement(
                    base_response, ai_enhancement, context
                )
                if enhanced_response:
                    self.logger.info("Successfully enhanced error response with AI")
                    return enhanced_response
            
            return None
            
        except Exception as e:
            self.logger.error(f"AI error enhancement failed: {e}")
            return None
    
    def _build_error_analysis_context(self, context: ErrorContext) -> Dict[str, Any]:
        """Build comprehensive context for AI error analysis"""
        analysis_context = {
            "timestamp": context.timestamp.isoformat() if context.timestamp else None,
            "provider_health": {},
            "system_status": "operational",
            "alternative_providers": []
        }
        
        # Add provider health information
        if context.provider_name:
            provider_health = self._get_provider_health(context.provider_name)
            if provider_health:
                analysis_context["provider_health"] = {
                    "name": provider_health.name,
                    "status": provider_health.status.value,
                    "success_rate": provider_health.success_rate,
                    "response_time": provider_health.response_time,
                    "error_message": provider_health.error_message,
                    "last_check": provider_health.last_check.isoformat() if provider_health.last_check else None
                }
                
                # Get alternative providers
                health_monitor = get_health_monitor()
                alternatives = health_monitor.get_alternative_providers(context.provider_name)
                analysis_context["alternative_providers"] = alternatives or []
        
        # Add additional context data
        if context.additional_data:
            analysis_context.update(context.additional_data)
        
        return analysis_context
    
    def _build_error_analysis_prompt(self, context: ErrorContext, analysis_context: Dict[str, Any]) -> str:
        """Build prompt for AI error analysis"""
        provider_info = ""
        if context.provider_name:
            provider_health = analysis_context.get("provider_health", {})
            if provider_health:
                provider_info = f"""
Provider Information:
- Provider: {context.provider_name}
- Status: {provider_health.get('status', 'unknown')}
- Success Rate: {provider_health.get('success_rate', 'unknown')}%
- Response Time: {provider_health.get('response_time', 'unknown')}ms
- Alternative Providers: {', '.join(analysis_context.get('alternative_providers', []))}
"""
        
        return f"""You are Karen's intelligent error analysis system. Analyze the following error and provide actionable guidance.

Error Details:
- Message: {context.error_message}
- Type: {context.error_type or 'Unknown'}
- Status Code: {context.status_code or 'N/A'}
- Timestamp: {context.timestamp.isoformat() if context.timestamp else 'N/A'}
{provider_info}

Your task is to provide a helpful, actionable response in the following JSON format:
{{
    "title": "Brief, user-friendly error title",
    "summary": "Clear explanation of what went wrong",
    "category": "one of: authentication, authorization, api_key_missing, api_key_invalid, rate_limit, provider_down, network_error, validation_error, database_error, system_error, unknown",
    "severity": "one of: low, medium, high, critical",
    "next_steps": ["2-4 specific, actionable steps to resolve the issue"],
    "contact_admin": false,
    "retry_after": null,
    "help_url": null,
    "technical_details": "Brief technical context if helpful"
}}

Guidelines:
- Be specific and actionable (e.g., "Add OPENAI_API_KEY to your .env file")
- Limit next_steps to 2-4 concrete actions
- Use helpful, direct tone without technical jargon
- If provider is down, suggest alternatives
- If credentials are needed, specify exactly which ones
- Set contact_admin to true only for critical system issues
- Include retry_after (seconds) for temporary issues

Respond with only the JSON object, no additional text."""
    
    def _build_error_enhancement_prompt(
        self, 
        base_response: IntelligentErrorResponse, 
        context: ErrorContext, 
        analysis_context: Dict[str, Any]
    ) -> str:
        """Build prompt for enhancing existing error response"""
        provider_info = ""
        if context.provider_name:
            provider_health = analysis_context.get("provider_health", {})
            if provider_health:
                provider_info = f"""
Provider Status: {provider_health.get('status', 'unknown')}
Alternative Providers: {', '.join(analysis_context.get('alternative_providers', []))}
"""
        
        return f"""You are Karen's intelligent error enhancement system. Improve the following error response with additional insights.

Original Error:
- Message: {context.error_message}
- Type: {context.error_type or 'Unknown'}
- Provider: {context.provider_name or 'N/A'}
{provider_info}

Current Response:
- Title: {base_response.title}
- Summary: {base_response.summary}
- Next Steps: {base_response.next_steps}

Enhance this response by:
1. Adding more specific guidance based on current provider status
2. Suggesting alternative providers if current one is unhealthy
3. Providing more context-aware next steps
4. Keeping the same helpful, direct tone

Respond with enhanced JSON in the same format:
{{
    "title": "Enhanced title",
    "summary": "Enhanced summary with more context",
    "next_steps": ["Enhanced actionable steps"],
    "additional_insights": "Any additional helpful context"
}}

Respond with only the JSON object, no additional text."""
    
    def _parse_ai_error_response(self, ai_response: str, context: ErrorContext) -> Optional[IntelligentErrorResponse]:
        """Parse and validate AI-generated error response"""
        try:
            import json
            
            # Clean the response to extract JSON
            response_text = ai_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            parsed = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["title", "summary", "category", "severity", "next_steps"]
            for field in required_fields:
                if field not in parsed:
                    self.logger.warning(f"AI response missing required field: {field}")
                    return None
            
            # Validate category and severity
            try:
                category = ErrorCategory(parsed["category"])
                severity = ErrorSeverity(parsed["severity"])
            except ValueError as e:
                self.logger.warning(f"Invalid category or severity in AI response: {e}")
                return None
            
            # Validate next_steps is a list
            if not isinstance(parsed["next_steps"], list) or len(parsed["next_steps"]) == 0:
                self.logger.warning("AI response has invalid next_steps")
                return None
            
            # Build response with validated data
            response_data = {
                "title": str(parsed["title"])[:200],  # Limit length
                "summary": str(parsed["summary"])[:500],
                "category": category,
                "severity": severity,
                "next_steps": [str(step)[:200] for step in parsed["next_steps"][:4]],  # Limit to 4 steps
                "contact_admin": bool(parsed.get("contact_admin", False)),
                "retry_after": parsed.get("retry_after"),
                "help_url": parsed.get("help_url"),
                "technical_details": str(parsed.get("technical_details", ""))[:300] if parsed.get("technical_details") else None
            }
            
            # Add provider health if available
            if context.provider_name:
                provider_health = self._get_provider_health(context.provider_name)
                if provider_health:
                    response_data["provider_health"] = {
                        "name": provider_health.name,
                        "status": provider_health.status.value,
                        "success_rate": provider_health.success_rate,
                        "response_time": provider_health.response_time,
                        "error_message": provider_health.error_message,
                        "last_check": provider_health.last_check.isoformat() if provider_health.last_check else None
                    }
            
            return IntelligentErrorResponse(**response_data)
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse AI response as JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _merge_ai_enhancement(
        self, 
        base_response: IntelligentErrorResponse, 
        ai_enhancement: str, 
        context: ErrorContext
    ) -> Optional[IntelligentErrorResponse]:
        """Merge AI enhancement with base response"""
        try:
            import json
            
            # Parse AI enhancement
            enhancement_text = ai_enhancement.strip()
            if enhancement_text.startswith("```json"):
                enhancement_text = enhancement_text[7:]
            if enhancement_text.endswith("```"):
                enhancement_text = enhancement_text[:-3]
            enhancement_text = enhancement_text.strip()
            
            parsed = json.loads(enhancement_text)
            
            # Create enhanced response by merging
            enhanced_data = base_response.dict()
            
            # Update with AI enhancements
            if "title" in parsed and parsed["title"]:
                enhanced_data["title"] = str(parsed["title"])[:200]
            
            if "summary" in parsed and parsed["summary"]:
                enhanced_data["summary"] = str(parsed["summary"])[:500]
            
            if "next_steps" in parsed and isinstance(parsed["next_steps"], list):
                enhanced_data["next_steps"] = [str(step)[:200] for step in parsed["next_steps"][:4]]
            
            # Add additional insights to technical details
            if "additional_insights" in parsed and parsed["additional_insights"]:
                insights = str(parsed["additional_insights"])[:300]
                if enhanced_data.get("technical_details"):
                    enhanced_data["technical_details"] += f" | AI Insights: {insights}"
                else:
                    enhanced_data["technical_details"] = f"AI Insights: {insights}"
            
            return IntelligentErrorResponse(**enhanced_data)
            
        except Exception as e:
            self.logger.warning(f"Failed to merge AI enhancement: {e}")
            return None
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error classification statistics"""
        # This would track error patterns over time
        # Implementation would include metrics collection
        return {
            "total_rules": len(self.classification_rules),
            "categories": [category.value for category in ErrorCategory],
            "cache_size": len(self._provider_health_cache)
        }
    
    def add_classification_rule(self, rule: ErrorClassificationRule) -> None:
        """Add a new classification rule"""
        self.classification_rules.append(rule)
        logger.info(f"Added new classification rule: {rule.name}")
    
    def remove_classification_rule(self, rule_name: str) -> bool:
        """Remove a classification rule by name"""
        initial_count = len(self.classification_rules)
        self.classification_rules = [
            rule for rule in self.classification_rules 
            if rule.name != rule_name
        ]
        removed = len(self.classification_rules) < initial_count
        if removed:
            logger.info(f"Removed classification rule: {rule_name}")
        return removed
    
    def validate_response_quality(self, response: IntelligentErrorResponse) -> bool:
        """Validate that an error response meets quality standards"""
        try:
            # Check title quality
            if not response.title or len(response.title.strip()) < 5:
                return False
            
            # Check summary quality
            if not response.summary or len(response.summary.strip()) < 10:
                return False
            
            # Check next steps quality
            if not response.next_steps or len(response.next_steps) == 0:
                return False
            
            # Ensure next steps are actionable (contain action words)
            action_words = ["add", "check", "verify", "try", "contact", "update", "restart", "wait", "use", "configure"]
            actionable_steps = 0
            for step in response.next_steps:
                if any(word in step.lower() for word in action_words):
                    actionable_steps += 1
            
            if actionable_steps == 0:
                return False
            
            # Check for appropriate severity assignment
            critical_keywords = ["database", "connection", "failed", "unavailable", "critical"]
            high_keywords = ["api", "key", "missing", "invalid", "unauthorized"]
            
            if response.severity == ErrorSeverity.CRITICAL:
                if not any(keyword in response.summary.lower() for keyword in critical_keywords):
                    return False
            
            # Ensure contact_admin is set appropriately
            if response.category in [ErrorCategory.DATABASE_ERROR] and not response.contact_admin:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating response quality: {e}")
            return False
    
    def get_ai_analysis_metrics(self) -> Dict[str, Any]:
        """Get metrics about AI analysis usage and quality"""
        # This would be implemented with actual metrics collection
        return {
            "ai_analysis_enabled": self._get_llm_router() is not None,
            "ai_orchestrator_available": self._get_ai_orchestrator() is not None,
            "llm_utils_available": self._get_llm_utils() is not None,
            "total_classification_rules": len(self.classification_rules)
        }


# Utility functions for response formatting
def format_error_for_user(response: IntelligentErrorResponse) -> Dict[str, Any]:
    """Format an intelligent error response for user consumption"""
    return {
        "title": response.title,
        "message": response.summary,
        "severity": response.severity.value,
        "next_steps": response.next_steps,
        "contact_admin": response.contact_admin,
        "retry_after": response.retry_after,
        "help_url": response.help_url
    }


def format_error_for_api(response: IntelligentErrorResponse) -> Dict[str, Any]:
    """Format an intelligent error response for API consumption"""
    return {
        "error": response.title,
        "message": response.summary,
        "category": response.category.value,
        "severity": response.severity.value,
        "next_steps": response.next_steps,
        "provider_health": response.provider_health,
        "contact_admin": response.contact_admin,
        "retry_after": response.retry_after,
        "help_url": response.help_url,
        "technical_details": response.technical_details
    }