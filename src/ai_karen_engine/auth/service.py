"""
Main AuthService interface for the consolidated authentication system.

This module provides the unified AuthService class that orchestrates all
authentication layers (core, security, intelligence) and serves as the
single entry point for all authentication operations.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import AuthConfig
from .core import CoreAuthenticator
from .security import SecurityEnhancer
from .intelligence import IntelligenceEngine, LoginAttempt
from .models import UserData, SessionData, AuthEvent, AuthEventType
from .monitoring import AuthMonitor
from .exceptions import (
    AuthError,
    InvalidCredentialsError,
    UserNotFoundError,
    UserAlreadyExistsError,
    SessionExpiredError,
    SessionNotFoundError,
    RateLimitExceededError,
    SecurityError,
    AnomalyDetectedError,
    ConfigurationError,
)


class AuthService:
    """
    Unified authentication service that orchestrates all authentication layers.
    
    This is the main interface that all application code should use for
    authentication operations. It provides a clean, consistent API while
    internally coordinating between the core authentication layer, security
    enhancements, and intelligence features based on configuration.
    
    Features:
    - Core authentication (login, session management, user management)
    - Security enhancements (rate limiting, audit logging, session validation)
    - Intelligence features (anomaly detection, behavioral analysis, risk scoring)
    - Configuration-driven feature enabling/disabling
    - Comprehensive error handling and logging
    """
    
    def __init__(self, config: AuthConfig) -> None:
        """
        Initialize the unified authentication service.
        
        Args:
            config: Authentication configuration that determines which
                   features are enabled and how they are configured
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AuthService")
        
        # Initialize core authentication layer (always present)
        self.core_auth = CoreAuthenticator(config)
        
        # Initialize security layer if enabled
        self.security_layer: Optional[SecurityEnhancer] = None
        if config.features.enable_security_features:
            self.security_layer = SecurityEnhancer(config)
        
        # Initialize intelligence layer if enabled
        self.intelligence_layer: Optional[IntelligenceEngine] = None
        if config.features.enable_intelligent_auth:
            self.intelligence_layer = IntelligenceEngine(config)
        
        # Initialize monitoring system if enabled
        self.monitor: Optional[AuthMonitor] = None
        if config.monitoring.enable_monitoring:
            self.monitor = AuthMonitor(config)
        
        self._initialized = False
        self.logger.info(f"AuthService initialized with mode: {config.get_mode_description()}")
    
    async def initialize(self) -> None:
        """Initialize the authentication service and all its components."""
        if self._initialized:
            return
        
        self.logger.info("Initializing AuthService components...")
        
        try:
            # Initialize intelligence layer if present
            if self.intelligence_layer:
                await self.intelligence_layer.initialize()
                self.logger.info("Intelligence layer initialized")
            
            # Initialize security layer if present
            if self.security_layer:
                await self.security_layer.initialize()
                self.logger.info("Security layer initialized")
            
            self._initialized = True
            self.logger.info("AuthService initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AuthService: {e}")
            raise ConfigurationError(f"AuthService initialization failed: {e}")
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[UserData]:
        """
        Authenticate a user with email and password.
        
        This method orchestrates the full authentication flow including
        security checks, rate limiting, and intelligence analysis.
        
        Args:
            email: User's email address
            password: User's password
            ip_address: Client IP address for security tracking
            user_agent: Client user agent string
            device_fingerprint: Optional device fingerprint for security
            geolocation: Optional geolocation data
            request_context: Additional request context for analysis
            **kwargs: Additional authentication parameters
            
        Returns:
            UserData if authentication successful, None otherwise
            
        Raises:
            InvalidCredentialsError: Invalid email/password combination
            AccountLockedError: Account is locked due to failed attempts
            RateLimitExceededError: Too many requests from this source
            AnomalyDetectedError: Blocked by intelligence system
            SecurityError: Blocked by security measures
        """
        await self.initialize()
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Security layer pre-checks
            if self.security_layer:
                # Check rate limiting
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address,
                    email=email,
                    event_type="login_attempt"
                )
            
            # Step 2: Intelligence layer analysis (if enabled)
            intelligence_result = None
            if self.intelligence_layer:
                login_attempt = LoginAttempt(
                    user_id=None,  # Unknown at this point
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=datetime.utcnow(),
                    device_fingerprint=device_fingerprint,
                    geolocation=geolocation,
                    session_context=request_context
                )
                
                # Get user data for behavioral analysis
                existing_user = await self.core_auth.get_user_by_email(email)
                
                # Get historical events for analysis
                historical_events = []
                if existing_user and self.security_layer:
                    historical_events = await self.security_layer.get_user_auth_history(
                        existing_user.user_id,
                        days=self.config.intelligence.behavioral_window_days
                    )
                
                intelligence_result = await self.intelligence_layer.analyze_login_attempt(
                    login_attempt, existing_user, historical_events
                )
                
                # Block if intelligence system recommends it
                if intelligence_result.should_block:
                    await self._log_blocked_attempt(
                        email, ip_address, user_agent, "intelligence_block",
                        intelligence_result.to_dict()
                    )
                    raise AnomalyDetectedError(
                        message="Login blocked by intelligence system",
                        risk_score=intelligence_result.risk_score,
                        anomaly_types=intelligence_result.anomaly_result.anomaly_types if intelligence_result.anomaly_result else [],
                        details=intelligence_result.to_dict()
                    )
            
            # Step 3: Core authentication
            user_data = await self.core_auth.authenticate_user(
                email=email,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent,
                **kwargs
            )
            
            # Step 4: Post-authentication security updates
            if self.security_layer and user_data:
                # Record successful attempt
                await self.security_layer.record_successful_attempt(
                    ip_address=ip_address,
                    email=email,
                    user_id=user_data.user_id
                )
                
                # Update intelligence data if available
                if intelligence_result:
                    await self.security_layer.update_user_intelligence_data(
                        user_data.user_id, intelligence_result
                    )
            
            # Record successful authentication event
            await self._record_auth_event(
                event_type=AuthEventType.LOGIN_SUCCESS,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id if user_data else None,
                email=email,
                tenant_id=user_data.tenant_id if user_data else None,
                ip_address=ip_address,
                user_agent=user_agent,
                risk_score=intelligence_result.risk_score if intelligence_result else 0.0,
                security_flags=intelligence_result.security_flags if intelligence_result else []
            )
            
            # Record performance metric
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self._record_performance_metric("authenticate_user", processing_time, True)
            
            return user_data
            
        except (InvalidCredentialsError, RateLimitExceededError, AnomalyDetectedError) as e:
            # Record failed attempt for rate limiting and security
            if self.security_layer:
                await self.security_layer.record_failed_attempt(
                    ip_address=ip_address,
                    email=email,
                    error_type=type(e).__name__,
                    details=getattr(e, 'details', {})
                )
            
            # Record failed authentication event
            await self._record_auth_event(
                event_type=AuthEventType.LOGIN_FAILED,
                success=False,
                start_time=start_time,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
                risk_score=getattr(e, 'risk_score', 0.0),
                security_flags=getattr(e, 'security_flags', []),
                details=getattr(e, 'details', {})
            )
            
            # Record performance metric for failed attempt
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self._record_performance_metric("authenticate_user", processing_time, False)
            
            raise
        
        except Exception as e:
            self.logger.error(f"Unexpected error in authenticate_user: {e}")
            # Still record the failed attempt
            if self.security_layer:
                await self.security_layer.record_failed_attempt(
                    ip_address=ip_address,
                    email=email,
                    error_type="system_error",
                    details={"error": str(e)}
                )
            
            # Record failed authentication event
            await self._record_auth_event(
                event_type=AuthEventType.LOGIN_FAILED,
                success=False,
                start_time=start_time,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
                details={"error_type": "system_error"}
            )
            
            # Record performance metric for system error
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self._record_performance_metric("authenticate_user", processing_time, False)
            
            raise AuthError(f"Authentication failed due to system error: {e}")
    
    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SessionData:
        """
        Create a new authentication session for a user.
        
        Args:
            user_data: Authenticated user data
            ip_address: Client IP address
            user_agent: Client user agent string
            device_fingerprint: Optional device fingerprint
            geolocation: Optional geolocation data
            request_context: Additional request context
            **kwargs: Additional session parameters
            
        Returns:
            SessionData with tokens and session information
            
        Raises:
            SecurityError: Session creation blocked by security measures
        """
        await self.initialize()
        
        try:
            # Create session through core authenticator
            session_data = await self.core_auth.create_session(
                user_data=user_data,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                **kwargs
            )
            
            # Add geolocation if provided
            if geolocation:
                session_data.geolocation = geolocation
            
            # Apply security enhancements if enabled
            if self.security_layer:
                # Validate session security
                security_result = await self.security_layer.validate_session_security(
                    session=session_data,
                    current_ip=ip_address,
                    current_user_agent=user_agent,
                    request_context=request_context
                )
                
                # Update session with security information
                session_data.risk_score = security_result["risk_score"]
                for flag in security_result["security_flags"]:
                    session_data.add_security_flag(flag)
                
                # Log session creation
                await self.security_layer.log_session_event(
                    AuthEventType.SESSION_CREATED,
                    session_data,
                    success=True
                )
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise SecurityError(f"Session creation failed: {e}")
    
    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[UserData]:
        """
        Validate a session token and return user data if valid.
        
        Args:
            session_token: Session token to validate
            ip_address: Current client IP address
            user_agent: Current client user agent
            request_context: Additional request context
            **kwargs: Additional validation parameters
            
        Returns:
            UserData if session is valid, None otherwise
            
        Raises:
            SessionExpiredError: Session has expired
            SessionNotFoundError: Session not found
            SecurityError: Session validation failed security checks
        """
        await self.initialize()
        
        try:
            # Validate session through core authenticator
            user_data = await self.core_auth.validate_session(session_token, **kwargs)
            
            if not user_data:
                return None
            
            # Apply security validation if enabled
            if self.security_layer:
                # Get full session data for security validation
                session_data = await self.core_auth.session_store.get_session(session_token)
                if session_data:
                    # Validate session security
                    security_result = await self.security_layer.validate_session_security(
                        session=session_data,
                        current_ip=ip_address,
                        current_user_agent=user_agent,
                        request_context=request_context
                    )
                    
                    # Check if session should be blocked
                    if not security_result["valid"]:
                        await self.invalidate_session(
                            session_token, 
                            reason="security_validation_failed"
                        )
                        raise SecurityError(
                            message="Session failed security validation",
                            details=security_result
                        )
                    
                    # Update session with new security information
                    session_data.risk_score = security_result["risk_score"]
                    for flag in security_result["security_flags"]:
                        session_data.add_security_flag(flag)
                    
                    # Update session in store
                    await self.core_auth.session_store.update_session(session_data)
            
            return user_data
            
        except (SessionExpiredError, SessionNotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            raise SecurityError(f"Session validation failed: {e}")
    
    async def invalidate_session(
        self,
        session_token: str,
        reason: str = "manual",
        **kwargs
    ) -> bool:
        """
        Invalidate a session token.
        
        Args:
            session_token: Session token to invalidate
            reason: Reason for invalidation
            **kwargs: Additional parameters
            
        Returns:
            True if session was invalidated, False otherwise
        """
        await self.initialize()
        
        try:
            # Invalidate through core authenticator
            result = await self.core_auth.invalidate_session(
                session_token, reason=reason, **kwargs
            )
            
            # Log invalidation if security layer is enabled
            if self.security_layer and result:
                session_data = await self.core_auth.session_store.get_session(session_token)
                if session_data:
                    await self.security_layer.log_session_event(
                        AuthEventType.SESSION_INVALIDATED,
                        session_data,
                        success=True,
                        details={"reason": reason}
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Session invalidation error: {e}")
            return False
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        tenant_id: str = "default",
        roles: Optional[List[str]] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> UserData:
        """
        Create a new user account.
        
        Args:
            email: User's email address
            password: User's password
            full_name: User's full name
            tenant_id: Tenant ID for multi-tenant support
            roles: User roles
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional user data
            
        Returns:
            UserData for the created user
            
        Raises:
            UserAlreadyExistsError: User with email already exists
            PasswordValidationError: Password doesn't meet requirements
            RateLimitExceededError: Too many user creation attempts
        """
        await self.initialize()
        
        try:
            # Check rate limiting for user creation if security layer enabled
            if self.security_layer:
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address,
                    event_type="user_creation"
                )
            
            # Create user through core authenticator
            user_data = await self.core_auth.create_user(
                email=email,
                password=password,
                full_name=full_name,
                tenant_id=tenant_id,
                roles=roles,
                **kwargs
            )
            
            # Log user creation if security layer enabled
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_CREATED,
                        user_id=user_data.user_id,
                        email=email,
                        tenant_id=tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True
                    )
                )
            
            return user_data
            
        except (UserAlreadyExistsError, RateLimitExceededError) as e:
            # Log failed attempt
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_CREATED,
                        email=email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message=str(e)
                    )
                )
            raise
    
    async def update_user_password(
        self,
        user_id: str,
        new_password: str,
        current_password: Optional[str] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> bool:
        """
        Update a user's password.
        
        Args:
            user_id: User ID
            new_password: New password
            current_password: Current password for verification
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional parameters
            
        Returns:
            True if password was updated successfully
            
        Raises:
            UserNotFoundError: User not found
            InvalidCredentialsError: Current password is incorrect
            PasswordValidationError: New password doesn't meet requirements
        """
        await self.initialize()
        
        try:
            # Update password through core authenticator
            result = await self.core_auth.update_user_password(
                user_id=user_id,
                new_password=new_password,
                current_password=current_password,
                **kwargs
            )
            
            # Log password change if security layer enabled
            if self.security_layer and result:
                user_data = await self.core_auth.get_user_by_id(user_id)
                if user_data:
                    await self.security_layer.log_auth_event(
                        AuthEvent(
                            event_type=AuthEventType.PASSWORD_CHANGED,
                            user_id=user_id,
                            email=user_data.email,
                            tenant_id=user_data.tenant_id,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            success=True
                        )
                    )
            
            return result
            
        except Exception as e:
            # Log failed attempt
            if self.security_layer:
                user_data = await self.core_auth.get_user_by_id(user_id)
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.PASSWORD_CHANGED,
                        user_id=user_id,
                        email=user_data.email if user_data else None,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message=str(e)
                    )
                )
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserData]:
        """Get user data by user ID."""
        await self.initialize()
        return await self.core_auth.get_user_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get user data by email address."""
        await self.initialize()
        return await self.core_auth.get_user_by_email(email)
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences dictionary
            **kwargs: Additional parameters
            
        Returns:
            True if preferences were updated successfully
        """
        await self.initialize()
        
        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)
            
            # Update preferences
            user_data.preferences.update(preferences)
            user_data.updated_at = datetime.utcnow()
            
            # Save updated user data
            await self.core_auth.db_client.update_user(user_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user preferences: {e}")
            raise
    
    async def create_password_reset_token(
        self,
        email: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> Optional[str]:
        """
        Create a password reset token for a user.
        
        Args:
            email: User's email address
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional parameters
            
        Returns:
            Password reset token if user exists, None otherwise
        """
        await self.initialize()
        
        try:
            # Check if user exists
            user_data = await self.core_auth.get_user_by_email(email)
            if not user_data:
                # Don't reveal that user doesn't exist - still log the attempt
                if self.security_layer:
                    await self.security_layer.log_auth_event(
                        AuthEvent(
                            event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
                            email=email,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            success=False,
                            error_message="User not found"
                        )
                    )
                return None
            
            # Check rate limiting if security layer enabled
            if self.security_layer:
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address,
                    email=email,
                    event_type="password_reset_request"
                )
            
            # Create reset token with database storage
            reset_token = await self.core_auth.token_manager.create_password_reset_token_with_storage(
                user_data=user_data,
                db_client=self.core_auth.db_client,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log password reset request
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
                        user_id=user_data.user_id,
                        email=email,
                        tenant_id=user_data.tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True
                    )
                )
            
            return reset_token
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create password reset token: {e}")
            return None
    
    async def verify_password_reset_token(
        self,
        token: str,
        new_password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> bool:
        """
        Verify a password reset token and update the password.
        
        Args:
            token: Password reset token
            new_password: New password
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional parameters
            
        Returns:
            True if password was reset successfully
        """
        await self.initialize()
        
        try:
            # Verify and use the reset token with database storage
            user_data = await self.core_auth.token_manager.verify_password_reset_token_with_storage(
                token=token,
                db_client=self.core_auth.db_client
            )
            if not user_data:
                # Log failed password reset attempt
                if self.security_layer:
                    await self.security_layer.log_auth_event(
                        AuthEvent(
                            event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            success=False,
                            error_message="Invalid or expired token"
                        )
                    )
                return False
            
            # Update the password (without requiring current password for reset)
            await self.update_user_password(
                user_id=user_data.user_id,
                new_password=new_password,
                current_password=None,  # No current password required for reset
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log successful password reset
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
                        user_id=user_data.user_id,
                        email=user_data.email,
                        tenant_id=user_data.tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True
                    )
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Password reset verification failed: {e}")
            # Log failed password reset attempt
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message=str(e)
                    )
                )
            return False
    
    async def create_email_verification_token(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> Optional[str]:
        """
        Create an email verification token for a user.
        
        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional parameters
            
        Returns:
            Email verification token if user exists, None otherwise
        """
        await self.initialize()
        
        try:
            # Get user data
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)
            
            # Check if user is already verified
            if user_data.is_verified:
                self.logger.info(f"User {user_id} is already verified")
                return None
            
            # Check rate limiting if security layer enabled
            if self.security_layer:
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address,
                    email=user_data.email,
                    event_type="email_verification_request"
                )
            
            # Create verification token with database storage
            verification_token = await self.core_auth.token_manager.create_email_verification_token_with_storage(
                user_data=user_data,
                db_client=self.core_auth.db_client,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log email verification request
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_UPDATED,  # Using existing event type
                        user_id=user_data.user_id,
                        email=user_data.email,
                        tenant_id=user_data.tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True,
                        details={"action": "email_verification_requested"}
                    )
                )
            
            return verification_token
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create email verification token: {e}")
            return None
    
    async def verify_email_address(
        self,
        token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> bool:
        """
        Verify a user's email address using a verification token.
        
        Args:
            token: Email verification token
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional parameters
            
        Returns:
            True if email was verified successfully
        """
        await self.initialize()
        
        try:
            # Verify and use the verification token with database storage
            user_data = await self.core_auth.token_manager.verify_email_verification_token_with_storage(
                token=token,
                db_client=self.core_auth.db_client
            )
            if not user_data:
                # Log failed email verification attempt
                if self.security_layer:
                    await self.security_layer.log_auth_event(
                        AuthEvent(
                            event_type=AuthEventType.USER_UPDATED,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            success=False,
                            error_message="Invalid or expired verification token",
                            details={"action": "email_verification_failed"}
                        )
                    )
                return False
            
            # Mark user as verified
            user_data.is_verified = True
            user_data.updated_at = datetime.utcnow()
            await self.core_auth.db_client.update_user(user_data)
            
            # Log successful email verification
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_UPDATED,
                        user_id=user_data.user_id,
                        email=user_data.email,
                        tenant_id=user_data.tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True,
                        details={"action": "email_verified"}
                    )
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Email verification failed: {e}")
            # Log failed email verification attempt
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_UPDATED,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message=str(e),
                        details={"action": "email_verification_failed"}
                    )
                )
            return False
    
    async def update_user_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> bool:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            full_name: New full name (optional)
            preferences: New preferences to merge (optional)
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional profile fields
            
        Returns:
            True if profile was updated successfully
        """
        await self.initialize()
        
        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)
            
            # Track what was updated for logging
            updates = {}
            
            # Update full name if provided
            if full_name is not None:
                user_data.full_name = full_name
                updates["full_name"] = full_name
            
            # Update preferences if provided
            if preferences is not None:
                user_data.preferences.update(preferences)
                updates["preferences"] = list(preferences.keys())
            
            # Update timestamp
            user_data.updated_at = datetime.utcnow()
            
            # Save updated user data
            await self.core_auth.db_client.update_user(user_data)
            
            # Log profile update if security layer enabled
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.PROFILE_UPDATED,
                        user_id=user_id,
                        email=user_data.email,
                        tenant_id=user_data.tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True,
                        details={"updates": updates}
                    )
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update user profile: {e}")
            # Log failed profile update
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.PROFILE_UPDATED,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message=str(e)
                    )
                )
            raise
    
    async def deactivate_user(
        self,
        user_id: str,
        reason: str = "manual",
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID
            reason: Reason for deactivation
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional parameters
            
        Returns:
            True if user was deactivated successfully
        """
        await self.initialize()
        
        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)
            
            # Deactivate user
            user_data.is_active = False
            user_data.updated_at = datetime.utcnow()
            
            # Save updated user data
            await self.core_auth.db_client.update_user(user_data)
            
            # Invalidate all user sessions
            # Note: This would require additional session management functionality
            # For now, we'll just log the deactivation
            
            # Log user deactivation if security layer enabled
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_DEACTIVATED,
                        user_id=user_id,
                        email=user_data.email,
                        tenant_id=user_data.tenant_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=True,
                        details={"reason": reason}
                    )
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate user: {e}")
            # Log failed deactivation
            if self.security_layer:
                await self.security_layer.log_auth_event(
                    AuthEvent(
                        event_type=AuthEventType.USER_DEACTIVATED,
                        user_id=user_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        error_message=str(e)
                    )
                )
            raise
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive service statistics.
        
        Returns:
            Dictionary with service statistics and health information
        """
        await self.initialize()
        
        stats = {
            "service_name": self.config.service_name,
            "service_version": self.config.service_version,
            "environment": self.config.environment,
            "mode": self.config.get_mode_description(),
            "initialized": self._initialized,
            "features": {
                "security_enabled": self.security_layer is not None,
                "intelligence_enabled": self.intelligence_layer is not None,
                "database_enabled": self.config.features.use_database,
                "rate_limiting_enabled": self.config.features.enable_rate_limiting,
                "audit_logging_enabled": self.config.features.enable_audit_logging,
            }
        }
        
        # Add security layer stats if available
        if self.security_layer:
            stats["security"] = await self.security_layer.get_stats()
        
        # Add intelligence layer stats if available
        if self.intelligence_layer:
            stats["intelligence"] = await self.intelligence_layer.get_stats()
        
        return stats
    
    async def _log_blocked_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        block_reason: str,
        details: Dict[str, Any]
    ) -> None:
        """Log a blocked authentication attempt."""
        if self.security_layer:
            await self.security_layer.log_security_event(
                event_type=AuthEventType.LOGIN_BLOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                details={
                    "block_reason": block_reason,
                    **details
                }
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the authentication service.
        
        Returns:
            Dictionary with health status information
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        try:
            await self.initialize()
            
            # Check core authenticator
            try:
                # Simple database connectivity check
                await self.core_auth.db_client.health_check()
                health["components"]["database"] = {"status": "healthy"}
            except Exception as e:
                health["components"]["database"] = {"status": "unhealthy", "error": str(e)}
                health["status"] = "degraded"
            
            # Check security layer
            if self.security_layer:
                try:
                    security_stats = await self.security_layer.get_stats()
                    health["components"]["security"] = {"status": "healthy", "stats": security_stats}
                except Exception as e:
                    health["components"]["security"] = {"status": "unhealthy", "error": str(e)}
                    health["status"] = "degraded"
            
            # Check intelligence layer
            if self.intelligence_layer:
                try:
                    intelligence_stats = await self.intelligence_layer.get_stats()
                    health["components"]["intelligence"] = {"status": "healthy", "stats": intelligence_stats}
                except Exception as e:
                    health["components"]["intelligence"] = {"status": "unhealthy", "error": str(e)}
                    health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["error"] = str(e)
        
        return health
    
    async def _record_auth_event(
        self,
        event_type: AuthEventType,
        success: bool,
        start_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        session_token: Optional[str] = None,
        error_message: Optional[str] = None,
        risk_score: float = 0.0,
        security_flags: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Record an authentication event for monitoring and logging."""
        # Calculate processing time if start_time provided
        processing_time_ms = 0.0
        if start_time:
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create auth event
        event = AuthEvent(
            event_type=event_type,
            user_id=user_id,
            email=email,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_token=session_token,
            success=success,
            error_message=error_message,
            risk_score=risk_score,
            security_flags=security_flags or [],
            processing_time_ms=processing_time_ms,
            details=details or {},
            **kwargs
        )
        
        # Log through security layer if available
        if self.security_layer:
            await self.security_layer.log_auth_event(event)
        
        # Record through monitoring system if available
        if self.monitor:
            await self.monitor.record_auth_event(event)
    
    async def _record_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a performance metric."""
        if self.monitor:
            await self.monitor.record_performance_metric(operation, duration_ms, success, tags)
    
    async def _log_blocked_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        reason: str,
        details: Dict[str, Any]
    ) -> None:
        """Log a blocked authentication attempt."""
        await self._record_auth_event(
            event_type=AuthEventType.LOGIN_BLOCKED,
            success=False,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=f"Login blocked: {reason}",
            blocked_by_security=True,
            details=details
        )
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        if self.monitor:
            return self.monitor.get_monitoring_stats()
        return {"monitoring_enabled": False}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        if self.monitor:
            return self.monitor.get_health_status()
        return {"status": "unknown", "reason": "Monitoring not enabled"}
    
    async def shutdown(self) -> None:
        """Shutdown the authentication service and all components."""
        self.logger.info("Shutting down AuthService...")
        
        try:
            # Shutdown monitoring
            if self.monitor:
                await self.monitor.shutdown()
            
            # Shutdown intelligence layer
            if self.intelligence_layer:
                # Intelligence layer doesn't have shutdown method yet, but we can add it later
                pass
            
            # Shutdown security layer
            if self.security_layer:
                # Security layer doesn't have shutdown method yet, but we can add it later
                pass
            
            self.logger.info("AuthService shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during AuthService shutdown: {e}")
            raise


# Factory functions for backward compatibility
async def create_auth_service(config: Optional[AuthConfig] = None) -> AuthService:
    """
    Create and initialize an AuthService instance.
    
    Args:
        config: Optional configuration. If not provided, loads from environment.
        
    Returns:
        Initialized AuthService instance
    """
    if config is None:
        config = AuthConfig.load()
    
    service = AuthService(config)
    await service.initialize()
    return service


# Global service instance for backward compatibility
_global_auth_service: Optional[AuthService] = None


async def get_auth_service(config: Optional[AuthConfig] = None) -> AuthService:
    """
    Get the global AuthService instance, creating it if necessary.
    
    Args:
        config: Optional configuration for service creation
        
    Returns:
        Global AuthService instance
    """
    global _global_auth_service
    
    if _global_auth_service is None:
        _global_auth_service = await create_auth_service(config)
    
    return _global_auth_service


# Compatibility functions for existing services
async def get_production_auth_service() -> AuthService:
    """Get AuthService configured for production use."""
    config = AuthConfig.load()
    # Ensure production-appropriate settings
    config.features.enable_security_features = True
    config.features.enable_rate_limiting = True
    config.features.enable_audit_logging = True
    return await create_auth_service(config)


async def get_intelligent_auth_service() -> AuthService:
    """Get AuthService with intelligence features enabled."""
    config = AuthConfig.load()
    # Enable intelligence features
    config.features.enable_intelligent_auth = True
    config.features.enable_anomaly_detection = True
    config.features.enable_behavioral_analysis = True
    return await create_auth_service(config)


async def get_unified_auth_service() -> AuthService:
    """Get unified AuthService (compatibility alias)."""
    return await get_auth_service()