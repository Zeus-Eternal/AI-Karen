"""
Main AuthService interface for the consolidated authentication system.

This module provides the unified AuthService class that orchestrates all
authentication layers (core, security, intelligence) and serves as the
single entry point for all authentication operations.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.core import CoreAuthenticator
from ai_karen_engine.auth.exceptions import (
    AnomalyDetectedError,
    AuthError,
    ConfigurationError,
    InvalidCredentialsError,
    RateLimitExceededError,
    SecurityError,
    SessionExpiredError,
    SessionNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ai_karen_engine.auth.intelligence import IntelligenceEngine, LoginAttempt
from ai_karen_engine.auth.models import AuthEvent, AuthEventType, SessionData, UserData
from ai_karen_engine.auth.monitoring import AuthMonitor
from ai_karen_engine.auth.monitoring_extensions import EnhancedAuthMonitor
from ai_karen_engine.auth.security import SecurityEnhancer


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
        self.enhanced_monitor: Optional[EnhancedAuthMonitor] = None
        if config.monitoring.enable_monitoring:
            self.monitor = AuthMonitor(config)
            # Initialize enhanced monitoring for advanced analytics
            self.enhanced_monitor = EnhancedAuthMonitor(config)

        self._initialized = False
        self.logger.info(
            f"AuthService initialized with mode: {config.get_mode_description()}"
        )

    async def initialize(self) -> None:
        """Initialize the authentication service and all its components."""
        if self._initialized:
            return

        self.logger.info("Initializing AuthService components...")
        try:
            # Ensure database schema is initialized before other components
            await self.core_auth.db_client.initialize_schema()
            self.logger.info("Database schema initialized")

            # Initialize core authentication layer
            await self.core_auth.initialize()
            self.logger.info("Core authentication layer initialized")

            # Initialize intelligence layer if present
            if self.intelligence_layer:
                await self.intelligence_layer.initialize()
                self.logger.info("Intelligence layer initialized")

            # Initialize security layer if present
            if self.security_layer:
                await self.security_layer.initialize()
                self.logger.info("Security layer initialized")

            # Setup default users if needed
            await self._setup_default_users()
            self.logger.info("Default users setup completed")

            self._initialized = True
            self.logger.info("AuthService initialization completed successfully")

        except Exception as e:
            self.logger.exception("Failed to initialize AuthService: %s", e)
            raise ConfigurationError(f"AuthService initialization failed: {e}") from e

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: Security layer pre-checks
            if self.security_layer:
                # Check rate limiting
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address, email=email, event_type="login_attempt"
                )

            # Step 2: Intelligence layer analysis (if enabled)
            intelligence_result = None
            if self.intelligence_layer:
                login_attempt = LoginAttempt(
                    user_id=None,  # Unknown at this point
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=datetime.now(timezone.utc),
                    device_fingerprint=device_fingerprint,
                    geolocation=geolocation,
                    session_context=request_context,
                )

                # Get user data for behavioral analysis
                existing_user = await self.core_auth.get_user_by_email(email)

                # Get historical events for analysis
                historical_events = []
                if existing_user and self.security_layer:
                    historical_events = await self.security_layer.get_user_auth_history(
                        existing_user.user_id,
                        days=self.config.intelligence.behavioral_window_days,
                    )

                intelligence_result = (
                    await self.intelligence_layer.analyze_login_attempt(
                        login_attempt, existing_user, historical_events
                    )
                )

                # Block if intelligence system recommends it
                if intelligence_result.should_block:
                    await self._log_blocked_attempt(
                        email,
                        ip_address,
                        user_agent,
                        "intelligence_block",
                        intelligence_result.to_dict(),
                    )
                    raise AnomalyDetectedError(
                        message="Login blocked by intelligence system",
                        risk_score=intelligence_result.risk_score,
                        anomaly_types=intelligence_result.anomaly_result.anomaly_types
                        if intelligence_result.anomaly_result
                        else [],
                        details=intelligence_result.to_dict(),
                    )

            # Step 3: Core authentication
            user_data = await self.core_auth.authenticate_user(
                email=email,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent,
                **kwargs,
            )

            # Step 4: Post-authentication security updates
            if self.security_layer and user_data:
                # Record successful attempt
                await self.security_layer.record_successful_attempt(
                    ip_address=ip_address, email=email, user_id=user_data.user_id
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
                risk_score=intelligence_result.risk_score
                if intelligence_result
                else 0.0,
                security_flags=intelligence_result.security_flags
                if intelligence_result
                else [],
            )

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric(
                "authenticate_user", processing_time, True
            )

            return user_data

        except (
            InvalidCredentialsError,
            RateLimitExceededError,
            AnomalyDetectedError,
        ) as e:
            # Record failed attempt for rate limiting and security
            if self.security_layer:
                await self.security_layer.record_failed_attempt(
                    ip_address=ip_address,
                    email=email,
                    error_type=type(e).__name__,
                    details=getattr(e, "details", {}),
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
                risk_score=getattr(e, "risk_score", 0.0),
                security_flags=getattr(e, "security_flags", []),
                details=getattr(e, "details", {}),
            )

            # Record performance metric for failed attempt
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric(
                "authenticate_user", processing_time, False
            )

            raise

        except Exception as e:
            self.logger.error(f"Unexpected error in authenticate_user: {e}")
            # Still record the failed attempt
            if self.security_layer:
                await self.security_layer.record_failed_attempt(
                    ip_address=ip_address,
                    email=email,
                    error_type="system_error",
                    details={"error": str(e)},
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
                details={"error_type": "system_error"},
            )

            # Record performance metric for system error
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric(
                "authenticate_user", processing_time, False
            )

            raise AuthError(f"Authentication failed due to system error: {e}")

    async def authenticate_external(
        self,
        provider_id: str,
        provider_type: str,
        provider_user: str,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: str = "default",
        **kwargs,
    ) -> Optional[UserData]:
        """Authenticate a user via external identity provider."""
        await self.initialize()

        try:
            return await self.core_auth.authenticate_external(
                provider_id=provider_id,
                provider_type=provider_type,
                provider_user=provider_user,
                email=email,
                full_name=full_name,
                config=config or {},
                metadata=metadata or {},
                tenant_id=tenant_id,
                **kwargs,
            )
        except Exception as e:
            self.logger.error(f"External authentication error: {e}")
            raise AuthError(f"External authentication failed: {e}")

    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.SESSION_CREATED,
            success=False,
            user_id=user_data.user_id,
            email=user_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start"},
        )

        start_time = datetime.now(timezone.utc)

        try:
            session_data = await self.core_auth.create_session(
                user_data=user_data,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                **kwargs,
            )

            if geolocation:
                session_data.geolocation = geolocation

            if self.security_layer:
                security_result = await self.security_layer.validate_session_security(
                    session=session_data,
                    current_ip=ip_address,
                    current_user_agent=user_agent,
                    request_context=request_context,
                )

                session_data.risk_score = security_result["risk_score"]
                for flag in security_result["security_flags"]:
                    session_data.add_security_flag(flag)

                # Log session creation
                await self.security_layer.log_session_event(
                    AuthEventType.SESSION_CREATED, session_data, success=True
                )

            # Record authentication event
            await self._record_auth_event(
                event_type=AuthEventType.SESSION_CREATED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_token=session_data.session_token,
                risk_score=session_data.risk_score,
                security_flags=session_data.security_flags,
            )

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric(
                "create_session", processing_time, True
            )

            return session_data

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_auth_event(
                event_type=AuthEventType.SESSION_CREATED,
                success=False,
                start_time=start_time,
                user_id=user_data.user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "create_session", processing_time, False
            )
            self.logger.error(f"Failed to create session: {e}")
            raise SecurityError(f"Session creation failed: {e}")

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        request_context: Optional[Dict[str, Any]] = None,
        **kwargs,
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.SESSION_VALIDATED,
            success=False,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start"},
        )

        try:
            user_data = await self.core_auth.validate_session(session_token, **kwargs)

            if not user_data:
                await self._record_auth_event(
                    event_type=AuthEventType.SESSION_VALIDATED,
                    success=False,
                    start_time=start_time,
                    session_token=session_token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message="session_not_found",
                )
                await self._record_performance_metric(
                    "validate_session",
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                    False,
                )
                return None

            if self.security_layer:
                session_data = await self.core_auth.session_manager.store.get_session(
                    session_token
                )
                if session_data:
                    security_result = (
                        await self.security_layer.validate_session_security(
                            session=session_data,
                            current_ip=ip_address,
                            current_user_agent=user_agent,
                            request_context=request_context,
                        )
                    )

                    if not security_result["valid"]:
                        await self.invalidate_session(
                            session_token, reason="security_validation_failed"
                        )
                        raise SecurityError(
                            message="Session failed security validation",
                            details=security_result,
                        )

                    session_data.risk_score = security_result["risk_score"]
                    for flag in security_result["security_flags"]:
                        session_data.add_security_flag(flag)

                    await self.core_auth.session_manager.store.update_session(
                        session_data
                    )

            await self._record_auth_event(
                event_type=AuthEventType.SESSION_VALIDATED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=user_data.email,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._record_performance_metric(
                "validate_session",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return user_data

        except (SessionExpiredError, SessionNotFoundError) as e:
            await self._record_auth_event(
                event_type=AuthEventType.SESSION_VALIDATED,
                success=False,
                start_time=start_time,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "validate_session",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            raise
        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.SESSION_VALIDATED,
                success=False,
                start_time=start_time,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "validate_session",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Session validation error: {e}")
            raise SecurityError(f"Session validation failed: {e}")

    async def invalidate_session(
        self, session_token: str, reason: str = "manual", **kwargs
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.LOGOUT,
            success=False,
            session_token=session_token,
            details={"stage": "start", "reason": reason},
        )

        start_time = datetime.now(timezone.utc)

        try:
            result = await self.core_auth.invalidate_session(
                session_token, reason=reason, **kwargs
            )

            session_data = None

            # Log invalidation if security layer is enabled
            if self.security_layer and result:
                session_data = await self.core_auth.session_manager.store.get_session(
                    session_token
                )
                if session_data:
                    await self.security_layer.log_session_event(
                        AuthEventType.SESSION_INVALIDATED,
                        session_data,
                        success=True,
                        details={"reason": reason},
                    )

            # Record auth event
            await self._record_auth_event(
                event_type=AuthEventType.SESSION_INVALIDATED,
                success=result,
                start_time=start_time,
                user_id=session_data.user_data.user_id if session_data else None,
                email=session_data.user_data.email if session_data else None,
                tenant_id=session_data.user_data.tenant_id if session_data else None,
                ip_address=session_data.ip_address if session_data else "unknown",
                user_agent=session_data.user_agent if session_data else "",
                session_token=session_token,
                details={"reason": reason},
            )

            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric(
                "invalidate_session", processing_time, result
            )

            return result

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_auth_event(
                event_type=AuthEventType.SESSION_INVALIDATED,
                success=False,
                start_time=start_time,
                session_token=session_token,
                error_message=str(e),
                details={"reason": reason},
            )
            await self._record_performance_metric(
                "invalidate_session", processing_time, False
            )
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
        **kwargs,
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
        start_time = datetime.now(timezone.utc)

        try:
            if self.security_layer:
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address, event_type="user_creation"
                )

            user_data = await self.core_auth.create_user(
                email=email,
                password=password,
                full_name=full_name,
                tenant_id=tenant_id,
                roles=roles,
                **kwargs,
            )
            # Record auth event
            await self._record_auth_event(
                event_type=AuthEventType.USER_CREATED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=email,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric("create_user", processing_time, True)

            return user_data

        except (UserAlreadyExistsError, RateLimitExceededError) as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_auth_event(
                event_type=AuthEventType.USER_CREATED,
                success=False,
                start_time=start_time,
                email=email,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric("create_user", processing_time, False)
            raise

    async def update_user_password(
        self,
        user_id: str,
        new_password: str,
        current_password: Optional[str] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
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
        start_time = datetime.now(timezone.utc)

        try:
            result = await self.core_auth.update_user_password(
                user_id=user_id,
                new_password=new_password,
                current_password=current_password,
                **kwargs,
            )

            user_data = await self.core_auth.get_user_by_id(user_id) if result else None

            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_CHANGED,
                success=result,
                start_time=start_time,
                user_id=user_id,
                email=user_data.email if user_data else None,
                tenant_id=user_data.tenant_id if user_data else None,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            await self._record_performance_metric(
                "update_user_password", processing_time, result
            )

            await self._record_performance_metric(
                "update_user_password",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                result,
            )
            return result

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            user_data = await self.core_auth.get_user_by_id(user_id)
            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_CHANGED,
                success=False,
                start_time=start_time,
                user_id=user_id,
                email=user_data.email if user_data else None,
                tenant_id=user_data.tenant_id if user_data else None,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "update_user_password", processing_time, False
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
        self, user_id: str, preferences: Dict[str, Any], **kwargs
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.USER_UPDATED,
            success=False,
            user_id=user_id,
            details={"stage": "start", "action": "preferences_update"},
        )

        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)

            user_data.preferences.update(preferences)
            user_data.updated_at = datetime.now(timezone.utc)

            await self.core_auth.db_client.update_user(user_data)

            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=True,
                start_time=start_time,
                user_id=user_id,
                email=user_data.email,
                details={"action": "preferences_update"},
            )
            await self._record_performance_metric(
                "update_user_preferences",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return True

        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=False,
                start_time=start_time,
                user_id=user_id,
                error_message=str(e),
                details={"action": "preferences_update"},
            )
            await self._record_performance_metric(
                "update_user_preferences",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Failed to update user preferences: {e}")
            raise

    async def create_password_reset_token(
        self, email: str, ip_address: str = "unknown", user_agent: str = "", **kwargs
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
            success=False,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start"},
        )

        try:
            user_data = await self.core_auth.get_user_by_email(email)
            if not user_data:
                await self._record_auth_event(
                    event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
                    success=False,
                    start_time=start_time,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message="User not found",
                )
                await self._record_performance_metric(
                    "create_password_reset_token",
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                    False,
                )
                return None

            if self.security_layer:
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address,
                    email=email,
                    event_type="password_reset_request",
                )

            reset_token = await self.core_auth.token_manager.create_password_reset_token_with_storage(
                user_data=user_data,
                db_client=self.core_auth.db_client,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._record_performance_metric(
                "create_password_reset_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return reset_token

        except RateLimitExceededError:
            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
                success=False,
                start_time=start_time,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message="rate_limit_exceeded",
            )
            await self._record_performance_metric(
                "create_password_reset_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            raise
        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_RESET_REQUESTED,
                success=False,
                start_time=start_time,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "create_password_reset_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Failed to create password reset token: {e}")
            return None

    async def verify_password_reset_token(
        self,
        token: str,
        new_password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start"},
        )

        try:
            user_data = await self.core_auth.token_manager.verify_password_reset_token_with_storage(
                token=token, db_client=self.core_auth.db_client
            )
            if not user_data:
                await self._record_auth_event(
                    event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
                    success=False,
                    start_time=start_time,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message="Invalid or expired token",
                )
                await self._record_performance_metric(
                    "verify_password_reset_token",
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                    False,
                )
                return False

            await self.update_user_password(
                user_id=user_data.user_id,
                new_password=new_password,
                current_password=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._record_performance_metric(
                "verify_password_reset_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return True

        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.PASSWORD_RESET_COMPLETED,
                success=False,
                start_time=start_time,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "verify_password_reset_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Password reset verification failed: {e}")
            return False

    async def create_email_verification_token(
        self, user_id: str, ip_address: str = "unknown", user_agent: str = "", **kwargs
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.USER_UPDATED,
            success=False,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start", "action": "email_verification_requested"},
        )

        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)

            if user_data.is_verified:
                self.logger.info(f"User {user_id} is already verified")
                await self._record_auth_event(
                    event_type=AuthEventType.USER_UPDATED,
                    success=False,
                    start_time=start_time,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message="already_verified",
                    details={"action": "email_verification_requested"},
                )
                await self._record_performance_metric(
                    "create_email_verification_token",
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                    False,
                )
                return None

            if self.security_layer:
                await self.security_layer.check_rate_limit(
                    ip_address=ip_address,
                    email=user_data.email,
                    event_type="email_verification_request",
                )

            verification_token = await self.core_auth.token_manager.create_email_verification_token_with_storage(
                user_data=user_data,
                db_client=self.core_auth.db_client,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"action": "email_verification_requested"},
            )
            await self._record_performance_metric(
                "create_email_verification_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return verification_token

        except RateLimitExceededError:
            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=False,
                start_time=start_time,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message="rate_limit_exceeded",
                details={"action": "email_verification_requested"},
            )
            await self._record_performance_metric(
                "create_email_verification_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            raise
        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=False,
                start_time=start_time,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
                details={"action": "email_verification_requested"},
            )
            await self._record_performance_metric(
                "create_email_verification_token",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Failed to create email verification token: {e}")
            return None

    async def verify_email_address(
        self, token: str, ip_address: str = "unknown", user_agent: str = "", **kwargs
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.USER_UPDATED,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start", "action": "email_verification"},
        )

        try:
            user_data = await self.core_auth.token_manager.verify_email_verification_token_with_storage(
                token=token, db_client=self.core_auth.db_client
            )
            if not user_data:
                await self._record_auth_event(
                    event_type=AuthEventType.USER_UPDATED,
                    success=False,
                    start_time=start_time,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    error_message="Invalid or expired verification token",
                    details={"action": "email_verification_failed"},
                )
                await self._record_performance_metric(
                    "verify_email_address",
                    (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                    False,
                )
                return False

            user_data.is_verified = True
            user_data.updated_at = datetime.now(timezone.utc)
            await self.core_auth.db_client.update_user(user_data)

            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=True,
                start_time=start_time,
                user_id=user_data.user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"action": "email_verified"},
            )
            await self._record_performance_metric(
                "verify_email_address",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return True

        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.USER_UPDATED,
                success=False,
                start_time=start_time,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
                details={"action": "email_verification_failed"},
            )
            await self._record_performance_metric(
                "verify_email_address",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Email verification failed: {e}")
            return False

    async def update_user_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.PROFILE_UPDATED,
            success=False,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start"},
        )

        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)

            updates = {}
            if full_name is not None:
                user_data.full_name = full_name
                updates["full_name"] = full_name

            if preferences is not None:
                user_data.preferences.update(preferences)
                updates["preferences"] = list(preferences.keys())

            user_data.updated_at = datetime.now(timezone.utc)
            await self.core_auth.db_client.update_user(user_data)

            await self._record_auth_event(
                event_type=AuthEventType.PROFILE_UPDATED,
                success=True,
                start_time=start_time,
                user_id=user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"updates": updates},
            )
            await self._record_performance_metric(
                "update_user_profile",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return True

        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.PROFILE_UPDATED,
                success=False,
                start_time=start_time,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
            )
            await self._record_performance_metric(
                "update_user_profile",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Failed to update user profile: {e}")
            raise

    async def deactivate_user(
        self,
        user_id: str,
        reason: str = "manual",
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
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
        start_time = datetime.now(timezone.utc)
        await self._record_auth_event(
            event_type=AuthEventType.USER_DEACTIVATED,
            success=False,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"stage": "start", "reason": reason},
        )

        try:
            user_data = await self.core_auth.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)

            user_data.is_active = False
            user_data.updated_at = datetime.now(timezone.utc)

            await self.core_auth.db_client.update_user(user_data)

            await self._record_auth_event(
                event_type=AuthEventType.USER_DEACTIVATED,
                success=True,
                start_time=start_time,
                user_id=user_id,
                email=user_data.email,
                tenant_id=user_data.tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"reason": reason},
            )
            await self._record_performance_metric(
                "deactivate_user",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                True,
            )
            return True

        except Exception as e:
            await self._record_auth_event(
                event_type=AuthEventType.USER_DEACTIVATED,
                success=False,
                start_time=start_time,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=str(e),
                details={"reason": reason},
            )
            await self._record_performance_metric(
                "deactivate_user",
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                False,
            )
            self.logger.error(f"Failed to deactivate user: {e}")
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
            },
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
        details: Dict[str, Any],
    ) -> None:
        """Log a blocked authentication attempt."""
        if self.security_layer:
            await self.security_layer.log_security_event(
                event_type=AuthEventType.LOGIN_BLOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                email=email,
                details={"block_reason": block_reason, **details},
            )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the authentication service.

        Returns:
            Dictionary with health status information
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {},
        }

        try:
            await self.initialize()

            # Check core authenticator
            try:
                # Simple database connectivity check
                await self.core_auth.db_client.health_check()
                health["components"]["database"] = {"status": "healthy"}
            except Exception as e:
                health["components"]["database"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health["status"] = "degraded"

            # Check security layer
            if self.security_layer:
                try:
                    security_stats = await self.security_layer.get_stats()
                    health["components"]["security"] = {
                        "status": "healthy",
                        "stats": security_stats,
                    }
                except Exception as e:
                    health["components"]["security"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }
                    health["status"] = "degraded"

            # Check intelligence layer
            if self.intelligence_layer:
                try:
                    intelligence_stats = await self.intelligence_layer.get_stats()
                    health["components"]["intelligence"] = {
                        "status": "healthy",
                        "stats": intelligence_stats,
                    }
                except Exception as e:
                    health["components"]["intelligence"] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }
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
        **kwargs,
    ) -> None:
        """Record an authentication event for monitoring and logging."""
        # Calculate processing time if start_time provided
        processing_time_ms = 0.0
        if start_time:
            processing_time_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

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
            **kwargs,
        )

        # Log through security layer if available
        if self.security_layer:
            await self.security_layer.log_auth_event(event)

        # Record through monitoring system if available
        if self.monitor:
            await self.monitor.record_auth_event(event)

        # Enhanced monitoring with advanced analytics
        if self.enhanced_monitor:
            analysis_results = await self.enhanced_monitor.analyze_auth_event(event)
            # Log analysis results if significant patterns detected
            if analysis_results.get("security_patterns") or analysis_results.get(
                "recommendations"
            ):
                self.logger.info(
                    f"Enhanced monitoring analysis for event {event.event_id}",
                    extra={
                        "event_id": event.event_id,
                        "analysis_results": analysis_results,
                        "security_patterns": len(
                            analysis_results.get("security_patterns", [])
                        ),
                        "recommendations": len(
                            analysis_results.get("recommendations", [])
                        ),
                    },
                )

    async def _record_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record a performance metric."""
        if self.monitor:
            await self.monitor.record_performance_metric(
                operation, duration_ms, success, tags
            )

    async def _log_blocked_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        reason: str,
        details: Dict[str, Any],
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
            details=details,
        )

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        if self.monitor:
            return self.monitor.get_monitoring_stats()
        return {"monitoring_enabled": False}

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        if self.monitor:
            health = self.monitor.get_health_status()
            # Add enhanced monitoring status if available
            if self.enhanced_monitor:
                enhanced_status = self.enhanced_monitor.get_comprehensive_status()
                health["enhanced_monitoring"] = enhanced_status
            return health
        return {"status": "unknown", "reason": "Monitoring not enabled"}

    def get_comprehensive_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status including advanced analytics."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "basic_monitoring": {},
            "enhanced_monitoring": {},
            "overall_health": "unknown",
        }

        # Basic monitoring status
        if self.monitor:
            status["basic_monitoring"] = {
                "enabled": True,
                "health": self.monitor.get_health_status(),
                "metrics": self.monitor.get_monitoring_stats(),
                "alerts": self.monitor.alerts.get_alert_stats(),
            }

        # Enhanced monitoring status
        if self.enhanced_monitor:
            status[
                "enhanced_monitoring"
            ] = self.enhanced_monitor.get_comprehensive_status()

        # Determine overall health
        basic_health = (
            status["basic_monitoring"].get("health", {}).get("status", "unknown")
        )
        enhanced_health = status["enhanced_monitoring"].get(
            "monitoring_health", "unknown"
        )

        if basic_health == "critical" or enhanced_health == "critical":
            status["overall_health"] = "critical"
        elif basic_health == "degraded" or enhanced_health == "degraded":
            status["overall_health"] = "degraded"
        elif basic_health == "warning" or enhanced_health == "warning":
            status["overall_health"] = "warning"
        elif basic_health == "healthy" and enhanced_health in ["healthy", "active"]:
            status["overall_health"] = "healthy"

        return status

    async def _setup_default_users(self) -> None:
        """
        Setup default users during authentication service initialization.

        Creates essential default users if they don't already exist:
        - Admin user for system administration
        - Anonymous user for unauthenticated operations
        - Test user for development/testing (only in non-production environments)
        """
        self.logger.info("Setting up default users...")

        try:
            # Default users configuration
            default_users = []

            # 1. Admin user - always create in all environments
            # Support both ADMIN_EMAIL/ADMIN_PASSWORD and AUTH_DEFAULT_* formats
            admin_email = os.getenv("ADMIN_EMAIL") or os.getenv(
                "AUTH_DEFAULT_ADMIN_EMAIL", "admin@kari.ai"
            )
            admin_password = os.getenv("ADMIN_PASSWORD") or os.getenv(
                "AUTH_DEFAULT_ADMIN_PASSWORD", "password123"
            )

            # Validate admin credentials format
            if not self._validate_email_format(admin_email):
                self.logger.warning(
                    f"Invalid admin email format: {admin_email}, using default"
                )
                admin_email = "admin@kari.ai"

            if not self._validate_password_strength(admin_password):
                self.logger.warning(
                    "Admin password doesn't meet minimum requirements, using default"
                )
                admin_password = "password123"

            default_users.append(
                {
                    "email": admin_email,
                    "password": admin_password,
                    "full_name": "System Administrator",
                    "roles": ["admin", "user"],
                    "tenant_id": "default",
                    "is_verified": True,
                    "description": "Default admin user",
                }
            )

            # 2. Anonymous user for unauthenticated operations
            # Support both ANONYMOUS_EMAIL/ANONYMOUS_PASSWORD and AUTH_ANONYMOUS_* formats
            anonymous_email = os.getenv("ANONYMOUS_EMAIL") or os.getenv(
                "AUTH_ANONYMOUS_EMAIL", "anonymous@karen.ai"
            )
            anonymous_password = os.getenv("ANONYMOUS_PASSWORD") or os.getenv(
                "AUTH_ANONYMOUS_PASSWORD", "anonymous"
            )

            # Validate anonymous credentials format
            if not self._validate_email_format(anonymous_email):
                self.logger.warning(
                    f"Invalid anonymous email format: {anonymous_email}, using default"
                )
                anonymous_email = "anonymous@karen.ai"

            if not self._validate_password_strength(anonymous_password):
                self.logger.warning(
                    "Anonymous password doesn't meet minimum requirements, using default"
                )
                anonymous_password = "anonymous"

            default_users.append(
                {
                    "email": anonymous_email,
                    "password": anonymous_password,
                    "full_name": "Anonymous User",
                    "roles": ["anonymous"],
                    "tenant_id": "default",
                    "is_verified": True,
                    "description": "Anonymous user for unauthenticated operations",
                }
            )

            # 3. Test user - only in development/testing environments
            if self.config.environment in ["development", "testing", "dev", "test"]:
                # Support both TEST_EMAIL/TEST_PASSWORD and AUTH_TEST_USER_* formats
                test_email = os.getenv("TEST_EMAIL") or os.getenv(
                    "AUTH_TEST_USER_EMAIL", "test@example.com"
                )
                test_password = os.getenv("TEST_PASSWORD") or os.getenv(
                    "AUTH_TEST_USER_PASSWORD", "testpassword"
                )

                # Validate test credentials format
                if not self._validate_email_format(test_email):
                    self.logger.warning(
                        f"Invalid test email format: {test_email}, using default"
                    )
                    test_email = "test@example.com"

                if not self._validate_password_strength(test_password):
                    self.logger.warning(
                        "Test password doesn't meet minimum requirements, using default"
                    )
                    test_password = "testpassword"

                default_users.append(
                    {
                        "email": test_email,
                        "password": test_password,
                        "full_name": "Test User",
                        "roles": ["user"],
                        "tenant_id": "default",
                        "is_verified": True,
                        "description": "Test user for development and testing",
                    }
                )

            # Create users that don't already exist
            created_users = []
            skipped_users = []

            for user_config in default_users:
                try:
                    # Check if user already exists
                    existing_user = await self.core_auth.get_user_by_email(
                        user_config["email"]
                    )

                    if existing_user:
                        skipped_users.append(user_config["email"])
                        self.logger.debug(
                            f"User {user_config['email']} already exists, skipping"
                        )
                        continue

                    # Create the user
                    user_data = await self.core_auth.create_user(
                        email=user_config["email"],
                        password=user_config["password"],
                        full_name=user_config["full_name"],
                        tenant_id=user_config["tenant_id"],
                        roles=user_config["roles"],
                    )

                    # Ensure user is verified if specified
                    if (
                        user_config.get("is_verified", False)
                        and not user_data.is_verified
                    ):
                        user_data.is_verified = True
                        await self.core_auth.db_client.update_user(user_data)

                    created_users.append(user_config["email"])
                    self.logger.info(
                        f"Created default user: {user_config['email']} ({user_config['description']})"
                    )

                except Exception as e:
                    self.logger.error(
                        f"Failed to create default user {user_config['email']}: {e}"
                    )
                    # Continue with other users even if one fails
                    continue

            # Log summary
            if created_users:
                self.logger.info(
                    f"Successfully created {len(created_users)} default users: {', '.join(created_users)}"
                )

            if skipped_users:
                self.logger.info(
                    f"Skipped {len(skipped_users)} existing users: {', '.join(skipped_users)}"
                )

            # Log default credentials for development environments
            if self.config.environment in ["development", "testing", "dev", "test"]:
                self.logger.info("Default user credentials for development:")
                for user_config in default_users:
                    if (
                        user_config["email"] in created_users
                        or user_config["email"] in skipped_users
                    ):
                        self.logger.info(
                            f"  {user_config['email']} / {user_config['password']} ({user_config['description']})"
                        )

        except Exception as e:
            self.logger.error(f"Error during default users setup: {e}")
            # Don't raise exception to avoid breaking initialization
            # Default users are helpful but not critical for service operation

    def _validate_email_format(self, email: str) -> bool:
        """
        Validate email format for custom credentials.

        Args:
            email: Email address to validate

        Returns:
            True if email format is valid, False otherwise
        """
        import re

        # Basic email validation pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email))

    def _validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength for custom credentials.

        Args:
            password: Password to validate

        Returns:
            True if password meets minimum requirements, False otherwise
        """
        # Minimum requirements: at least 6 characters
        # In production, you might want stricter requirements
        return len(password) >= 6

    async def shutdown(self) -> None:
        """Shutdown the authentication service and all components."""
        self.logger.info("Shutting down AuthService...")

        try:
            # Shutdown enhanced monitoring
            if self.enhanced_monitor:
                await self.enhanced_monitor.shutdown()

            # Shutdown monitoring
            if self.monitor:
                await self.monitor.shutdown()

            # Shutdown intelligence layer
            if self.intelligence_layer:
                await self.intelligence_layer.shutdown()

            # Shutdown security layer
            if self.security_layer:
                await self.security_layer.shutdown()

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
    # Respect environment configuration for production settings
    # Only override if environment variables are not explicitly set
    if os.getenv("AUTH_ENABLE_SECURITY_FEATURES") is None:
        config.features.enable_security_features = True
    if os.getenv("AUTH_ENABLE_RATE_LIMITING") is None:
        config.features.enable_rate_limiting = True
    if os.getenv("AUTH_ENABLE_AUDIT_LOGGING") is None:
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
