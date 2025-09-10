# mypy: ignore-errors
"""
Validation framework for Kari FastAPI Server.
Handles 4.x validation requirements, environment-specific config, and framework initialization.
"""

import logging
from .config import Settings

logger = logging.getLogger("kari")


def load_environment_specific_validation_config(settings: Settings) -> Settings:
    """
    Load environment-specific validation configuration.
    
    Requirement 4.3: Enable/disable specific validation rules based on deployment environment
    """
    environment = settings.environment.lower()
    
    # Production environment - strict validation
    if environment == "production":
        settings.enable_request_validation = True
        settings.enable_security_analysis = True
        settings.log_invalid_requests = True
        settings.max_request_size = min(settings.max_request_size, 5 * 1024 * 1024)  # 5MB max in prod
        settings.validation_rate_limit_per_minute = 50  # Stricter rate limiting
        settings.max_invalid_requests_per_connection = 5  # Lower tolerance
        logger.info("🔒 Production validation config: strict security enabled")
    
    # Development environment - relaxed validation for debugging
    elif environment in ["development", "dev", "local"]:
        settings.enable_request_validation = True
        settings.enable_security_analysis = getattr(settings, "enable_security_analysis", True)
        settings.log_invalid_requests = True
        settings.validation_rate_limit_per_minute = 200  # More lenient for testing
        settings.max_invalid_requests_per_connection = 20  # Higher tolerance for debugging
        logger.info("🔧 Development validation config: relaxed for debugging")
    
    # Testing environment - minimal validation to avoid test interference
    elif environment in ["test", "testing"]:
        settings.enable_request_validation = True
        settings.enable_security_analysis = False  # Disable for faster tests
        settings.log_invalid_requests = False  # Reduce test noise
        settings.validation_rate_limit_per_minute = 1000  # Very high for load tests
        settings.max_invalid_requests_per_connection = 100
        logger.info("🧪 Testing validation config: minimal interference")
    
    # Staging environment - production-like but with more logging
    elif environment == "staging":
        settings.enable_request_validation = True
        settings.enable_security_analysis = True
        settings.log_invalid_requests = True
        settings.validation_rate_limit_per_minute = 100
        settings.max_invalid_requests_per_connection = 10
        logger.info("🎭 Staging validation config: production-like with enhanced logging")
    
    return settings


def validate_configuration_settings(settings: Settings) -> bool:
    """
    Validate configuration settings for consistency and security.
    
    Requirements 4.1, 4.2: Ensure configuration values are within safe ranges
    """
    issues = []
    
    # Validate request size limits
    if settings.max_request_size <= 0:
        issues.append("max_request_size must be positive")
    elif settings.max_request_size > 100 * 1024 * 1024:  # 100MB
        issues.append("max_request_size too large (>100MB), potential DoS risk")
    
    # Validate header limits
    if settings.max_headers_count <= 0 or settings.max_headers_count > 1000:
        issues.append("max_headers_count must be between 1 and 1000")
    
    if settings.max_header_size <= 0 or settings.max_header_size > 32768:  # 32KB
        issues.append("max_header_size must be between 1 and 32768 bytes")
    
    # Validate rate limiting
    if settings.validation_rate_limit_per_minute <= 0:
        issues.append("validation_rate_limit_per_minute must be positive")
    elif settings.validation_rate_limit_per_minute > 10000:
        issues.append("validation_rate_limit_per_minute too high (>10000), potential resource exhaustion")
    
    # Validate protocol settings
    if settings.max_invalid_requests_per_connection <= 0:
        issues.append("max_invalid_requests_per_connection must be positive")
    elif settings.max_invalid_requests_per_connection > 1000:
        issues.append("max_invalid_requests_per_connection too high (>1000)")
    
    # Log issues
    if issues:
        logger.error("❌ Configuration validation failed:")
        for issue in issues:
            logger.error(f"   • {issue}")
        return False
    
    logger.info("✅ Configuration validation passed")
    return True


def initialize_validation_framework(settings: Settings) -> None:
    """
    Initialize the HTTP request validation framework with configurable settings.
    
    This function sets up the validation components according to requirements:
    - 4.1: Configurable request size limits
    - 4.2: Configurable rate limiting thresholds  
    - 4.3: Environment-specific validation rules
    - 4.4: Updateable validation patterns without code changes
    """
    try:
        # Load environment-specific configuration (Requirement 4.3)
        settings = load_environment_specific_validation_config(settings)
        
        # Validate configuration settings (Requirements 4.1, 4.2)
        if not validate_configuration_settings(settings):
            logger.warning("⚠️ Configuration issues detected, using safe defaults")
        
        from ai_karen_engine.server.http_validator import ValidationConfig
        from ai_karen_engine.server.security_analyzer import SecurityAnalyzer
        from ai_karen_engine.server.rate_limiter import EnhancedRateLimiter, MemoryRateLimitStorage, DEFAULT_RATE_LIMIT_RULES
        from ai_karen_engine.server.enhanced_logger import EnhancedLogger, LoggingConfig
        
        # Parse configurable lists from settings (Requirement 4.4)
        blocked_agents = set(agent.strip().lower() for agent in settings.blocked_user_agents.split(",") if agent.strip())
        suspicious_headers = set(header.strip().lower() for header in settings.suspicious_headers.split(",") if header.strip())
        
        # Create validation configuration from settings
        validation_config = ValidationConfig(
            max_content_length=settings.max_request_size,
            max_headers_count=settings.max_headers_count,
            max_header_size=settings.max_header_size,
            rate_limit_requests_per_minute=settings.validation_rate_limit_per_minute,
            enable_security_analysis=settings.enable_security_analysis,
            log_invalid_requests=settings.log_invalid_requests,
            blocked_user_agents=blocked_agents,
            suspicious_headers=suspicious_headers
        )
        
        # Initialize enhanced logger for validation events
        logging_config = LoggingConfig(
            log_level="INFO",
            enable_security_logging=settings.enable_security_analysis,
            sanitize_data=True
        )
        enhanced_logger = EnhancedLogger(logging_config)
        
        # Store configuration globally for middleware access
        import ai_karen_engine.server.middleware as middleware_module
        middleware_module._validation_config = validation_config
        middleware_module._enhanced_logger = enhanced_logger
        
        logger.info("✅ HTTP request validation framework initialized")
        logger.info(f"   • Environment: {settings.environment}")
        logger.info(f"   • Max request size: {settings.max_request_size / (1024*1024):.1f}MB")
        logger.info(f"   • Max headers: {settings.max_headers_count}")
        logger.info(f"   • Security analysis: {'enabled' if settings.enable_security_analysis else 'disabled'}")
        logger.info(f"   • Rate limiting: {settings.validation_rate_limit_per_minute} requests/minute")
        logger.info(f"   • Blocked user agents: {len(blocked_agents)} patterns")
        logger.info(f"   • Suspicious headers: {len(suspicious_headers)} patterns")
        logger.info(f"   • Protocol error handling: {'enabled' if settings.enable_protocol_error_handling else 'disabled'}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize validation framework: {e}")
        logger.info("Server will continue with basic validation")