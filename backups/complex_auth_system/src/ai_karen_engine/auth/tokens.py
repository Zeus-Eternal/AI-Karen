"""
Enhanced token management for the consolidated authentication service.

This module provides JWT token creation, validation, and management
for access tokens, refresh tokens, and other authentication tokens
with enhanced security features including token rotation and JTI tracking.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set, Tuple

try:
    import jwt
except ImportError:
    # Fallback for environments without PyJWT
    jwt = None

from ai_karen_engine.auth.config import JWTConfig
from ai_karen_engine.auth.exceptions import InvalidTokenError, TokenExpiredError
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.core.cache import get_token_cache, get_request_deduplicator
from ai_karen_engine.services.audit_logging import get_audit_logger


class EnhancedTokenManager:
    """
    Enhanced JWT token manager for authentication tokens with security features.

    Handles creation and validation of access tokens, refresh tokens,
    and other authentication-related tokens with token rotation,
    JTI tracking for replay prevention, and enhanced security.
    """

    def __init__(self, config: JWTConfig) -> None:
        """Initialize enhanced token manager with JWT configuration."""
        self.config = config
        self._revoked_jtis: Set[str] = set()  # In-memory JTI blacklist
        self._issued_jtis: Set[str] = set()   # Track issued JTIs
        self._token_cache = get_token_cache()
        self._deduplicator = get_request_deduplicator()
        self._audit_logger = get_audit_logger()

        if jwt is None:
            raise ImportError(
                "PyJWT is required for token management. Install with: pip install PyJWT"
            )

    def _generate_jti(self) -> str:
        """Generate a unique JTI (JWT ID) for token tracking."""
        jti = secrets.token_hex(16)
        # Ensure uniqueness
        while jti in self._issued_jtis:
            jti = secrets.token_hex(16)
        self._issued_jtis.add(jti)
        return jti

    def _is_jti_revoked(self, jti: str) -> bool:
        """Check if a JTI has been revoked."""
        return jti in self._revoked_jtis

    def _revoke_jti(self, jti: str) -> None:
        """Revoke a JTI to prevent token reuse."""
        self._revoked_jtis.add(jti)

    async def create_access_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None, long_lived: bool = False
    ) -> str:
        """
        Create a JWT access token for a user with enhanced security.

        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time (optional, defaults to 15 minutes)
            long_lived: If True, creates a long-lived token (24 hours) for API stability

        Returns:
            JWT access token string
        """
        start_time = time.time()
        
        try:
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            elif long_lived:
                # Use 24 hours for long-lived tokens to reduce API timeouts
                expire = datetime.now(timezone.utc) + timedelta(hours=24)
            else:
                # Use 15 minutes for regular access tokens as per requirements
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)

            now = datetime.now(timezone.utc)
            jti = self._generate_jti()

            payload = {
                "sub": user_data.user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "roles": user_data.roles,
                "tenant_id": user_data.tenant_id,
                "is_verified": user_data.is_verified,
                "is_active": user_data.is_active,
                "exp": int(expire.timestamp()),
                "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),  # Not before
                "jti": jti,
                "typ": "access",
            }

            token = jwt.encode(
                payload, self.config.secret_key, algorithm=self.config.algorithm
            )
            
            # Audit log token creation performance
            duration_ms = (time.time() - start_time) * 1000
            self._audit_logger.log_token_operation_performance(
                operation_name="create_access_token",
                duration_ms=duration_ms,
                success=True,
                user_id=user_data.user_id,
                tenant_id=user_data.tenant_id,
                token_jti=jti
            )
            
            return token
            
        except Exception as e:
            # Audit log token creation failure
            duration_ms = (time.time() - start_time) * 1000
            self._audit_logger.log_token_operation_performance(
                operation_name="create_access_token",
                duration_ms=duration_ms,
                success=False,
                user_id=user_data.user_id,
                tenant_id=user_data.tenant_id,
                error_message=str(e)
            )
            raise

    async def create_refresh_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token for a user with enhanced security.

        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time (optional, defaults to 7 days)

        Returns:
            JWT refresh token string
        """
        start_time = time.time()
        
        try:
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                # Use 7 days for refresh tokens as per requirements
                expire = datetime.now(timezone.utc) + timedelta(days=7)

            now = datetime.now(timezone.utc)
            jti = self._generate_jti()

            payload = {
                "sub": user_data.user_id,
                "email": user_data.email,
                "tenant_id": user_data.tenant_id,
                "exp": int(expire.timestamp()),
                "iat": int(now.timestamp()),
                "nbf": int(now.timestamp()),  # Not before
                "jti": jti,
                "typ": "refresh",
            }

            token = jwt.encode(
                payload, self.config.secret_key, algorithm=self.config.algorithm
            )
            
            # Audit log token creation performance
            duration_ms = (time.time() - start_time) * 1000
            self._audit_logger.log_token_operation_performance(
                operation_name="create_refresh_token",
                duration_ms=duration_ms,
                success=True,
                user_id=user_data.user_id,
                tenant_id=user_data.tenant_id,
                token_jti=jti
            )
            
            return token
            
        except Exception as e:
            # Audit log token creation failure
            duration_ms = (time.time() - start_time) * 1000
            self._audit_logger.log_token_operation_performance(
                operation_name="create_refresh_token",
                duration_ms=duration_ms,
                success=False,
                user_id=user_data.user_id,
                tenant_id=user_data.tenant_id,
                error_message=str(e)
            )
            raise

    async def create_password_reset_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT token for password reset.

        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time (optional)

        Returns:
            JWT password reset token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = (
                datetime.now(timezone.utc) + self.config.password_reset_token_expiry
            )

        payload = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "password_reset",
            "jti": secrets.token_hex(16),
        }

        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

    async def create_email_verification_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT token for email verification.

        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time (optional)

        Returns:
            JWT email verification token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = (
                datetime.now(timezone.utc) + self.config.email_verification_token_expiry
            )

        payload = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "email_verification",
            "jti": secrets.token_hex(16),
        }

        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

    async def validate_token(
        self, token: str, expected_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a JWT token with enhanced security checks and caching.

        Args:
            token: JWT token to validate
            expected_type: Expected token type (optional)

        Returns:
            Token payload dictionary

        Raises:
            InvalidTokenError: If token is invalid or malformed
            TokenExpiredError: If token has expired
        """
        # Check cache first for valid tokens
        cached_result = self._token_cache.get_validation_result(token)
        if cached_result is not None:
            if cached_result.get("valid"):
                payload = cached_result["payload"]
                # Still check if JTI was revoked after caching
                jti = payload.get("jti")
                if jti and self._is_jti_revoked(jti):
                    self._token_cache.invalidate_token(token)
                    raise InvalidTokenError(
                        "Token has been revoked",
                        token_type=expected_type,
                    )
                return payload
            else:
                # Cached invalid result
                error_type = cached_result.get("error_type")
                error_message = cached_result.get("error_message", "Token validation failed")
                if "expired" in error_message.lower():
                    raise TokenExpiredError(token_type=expected_type)
                else:
                    raise InvalidTokenError(error_message, token_type=expected_type)

        # Deduplicate simultaneous validation requests for the same token
        return await self._deduplicator.deduplicate(
            self._validate_token_uncached, token, expected_type
        )

    async def _validate_token_uncached(
        self, token: str, expected_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Internal method to validate token without caching (used by deduplicator).
        """
        try:
            # Decode token with all validations
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[self.config.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "require": ["exp", "iat", "jti", "sub", "typ"]
                }
            )

            # Check token type if specified
            token_type = payload.get("typ")
            if expected_type and token_type != expected_type:
                error_msg = f"Invalid token type. Expected {expected_type}, got {token_type}"
                # Cache the invalid result
                self._token_cache.cache_validation_result(
                    token, 
                    {"valid": False, "error_message": error_msg, "error_type": expected_type},
                    custom_ttl=60  # Cache invalid results for shorter time
                )
                raise InvalidTokenError(error_msg, token_type=expected_type)

            # Check if JTI is revoked (replay prevention)
            jti = payload.get("jti")
            if jti and self._is_jti_revoked(jti):
                error_msg = "Token has been revoked"
                # Don't cache revoked tokens as revocation status can change
                raise InvalidTokenError(error_msg, token_type=token_type)

            # Additional security checks
            now = datetime.now(timezone.utc).timestamp()
            
            # Check not-before time
            nbf = payload.get("nbf")
            if nbf and now < nbf:
                error_msg = "Token not yet valid"
                self._token_cache.cache_validation_result(
                    token, 
                    {"valid": False, "error_message": error_msg, "error_type": expected_type},
                    custom_ttl=30
                )
                raise InvalidTokenError(error_msg, token_type=token_type)

            # Cache successful validation
            # Calculate remaining TTL based on token expiry
            exp_timestamp = payload.get("exp", 0)
            remaining_ttl = max(30, int(exp_timestamp - now) - 60)  # Cache until 1 min before expiry
            
            self._token_cache.cache_validation_result(
                token,
                {"valid": True, "payload": payload},
                custom_ttl=min(remaining_ttl, 300)  # Max 5 minutes cache
            )

            return payload

        except jwt.ExpiredSignatureError:
            error_msg = "Token has expired"
            self._token_cache.cache_validation_result(
                token,
                {"valid": False, "error_message": error_msg, "error_type": expected_type},
                custom_ttl=60
            )
            raise TokenExpiredError(token_type=expected_type)
        except jwt.InvalidTokenError as e:
            error_msg = f"Invalid token: {e}"
            self._token_cache.cache_validation_result(
                token,
                {"valid": False, "error_message": error_msg, "error_type": expected_type},
                custom_ttl=60
            )
            raise InvalidTokenError(error_msg, token_type=expected_type)
        except Exception as e:
            error_msg = f"Token validation failed: {e}"
            # Don't cache unexpected errors
            raise InvalidTokenError(error_msg, token_type=expected_type)

    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate an access token and return its payload."""
        return await self.validate_token(token, "access")

    async def validate_refresh_token(self, token: str) -> Dict[str, Any]:
        """Validate a refresh token and return its payload."""
        return await self.validate_token(token, "refresh")

    async def validate_password_reset_token(self, token: str) -> Dict[str, Any]:
        """Validate a password reset token and return its payload."""
        return await self.validate_token(token, "password_reset")

    async def validate_email_verification_token(self, token: str) -> Dict[str, Any]:
        """Validate an email verification token and return its payload."""
        return await self.validate_token(token, "email_verification")

    async def rotate_tokens(
        self, refresh_token: str, user_data: UserData
    ) -> Tuple[str, str, datetime]:
        """
        Rotate both access and refresh tokens for enhanced security.

        Args:
            refresh_token: Valid refresh token to rotate
            user_data: Current user data

        Returns:
            Tuple of (new_access_token, new_refresh_token, refresh_expires_at)

        Raises:
            InvalidTokenError: If refresh token is invalid
            TokenExpiredError: If refresh token has expired
        """
        # Validate refresh token
        payload = await self.validate_refresh_token(refresh_token)

        # Verify the token belongs to the user
        if payload.get("sub") != user_data.user_id:
            raise InvalidTokenError(
                "Refresh token does not belong to user", token_type="refresh"
            )

        # Revoke the old refresh token JTI to prevent reuse
        old_jti = payload.get("jti")
        if old_jti:
            self._revoke_jti(old_jti)

        # Create new tokens
        new_access_token = await self.create_access_token(user_data)
        new_refresh_token = await self.create_refresh_token(user_data)
        
        # Calculate refresh token expiry
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        return new_access_token, new_refresh_token, refresh_expires_at

    async def refresh_access_token(
        self, refresh_token: str, user_data: UserData
    ) -> str:
        """
        Create a new access token using a refresh token (legacy method).

        Args:
            refresh_token: Valid refresh token
            user_data: Current user data

        Returns:
            New access token

        Raises:
            InvalidTokenError: If refresh token is invalid
            TokenExpiredError: If refresh token has expired
        """
        # Use token rotation for enhanced security
        new_access_token, _, _ = await self.rotate_tokens(refresh_token, user_data)
        return new_access_token

    def get_token_payload_without_validation(
        self, token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get token payload without validation (for debugging/logging).

        Args:
            token: JWT token

        Returns:
            Token payload or None if token is malformed
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token is expired without full validation.

        Args:
            token: JWT token

        Returns:
            True if token is expired, False otherwise
        """
        try:
            payload = self.get_token_payload_without_validation(token)
            if not payload or "exp" not in payload:
                return True

            exp_timestamp = payload["exp"]
            return datetime.now(timezone.utc).timestamp() > exp_timestamp

        except Exception:
            return True

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get the expiry time of a token.

        Args:
            token: JWT token

        Returns:
            Expiry datetime or None if token is malformed
        """
        try:
            payload = self.get_token_payload_without_validation(token)
            if not payload or "exp" not in payload:
                return None

            return datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        except Exception:
            return None

    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a token by adding its JTI to the blacklist.

        Args:
            token: JWT token to revoke

        Returns:
            True if token was successfully revoked, False otherwise
        """
        try:
            payload = self.get_token_payload_without_validation(token)
            if not payload:
                return False

            jti = payload.get("jti")
            if jti:
                self._revoke_jti(jti)
                # Invalidate cached validation result
                self._token_cache.invalidate_token(token)
                return True
            
            return False

        except Exception:
            return False

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a specific user.
        
        Note: This is a simplified implementation. In production,
        you would need to track user tokens in a database.

        Args:
            user_id: User ID whose tokens should be revoked

        Returns:
            Number of tokens revoked
        """
        # In a real implementation, this would query the database
        # for all active tokens for the user and revoke their JTIs
        # For now, this is a placeholder
        return 0

    def get_jti_from_token(self, token: str) -> Optional[str]:
        """
        Extract JTI from a token without full validation.

        Args:
            token: JWT token

        Returns:
            JTI string or None if not found
        """
        try:
            payload = self.get_token_payload_without_validation(token)
            return payload.get("jti") if payload else None
        except Exception:
            return None

    def cleanup_expired_jtis(self) -> int:
        """
        Clean up expired JTIs from the revocation list.
        
        This should be called periodically to prevent memory leaks.

        Returns:
            Number of JTIs cleaned up
        """
        # In a real implementation, this would check token expiry times
        # and remove expired JTIs from the blacklist
        # For now, this is a placeholder
        return 0

    async def create_password_reset_token_with_storage(
        self,
        user_data: UserData,
        db_client,
        expires_delta: Optional[timedelta] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> str:
        """
        Create a password reset token and store it in the database.

        Args:
            user_data: User data to encode in token
            db_client: Database client for token storage
            expires_delta: Custom expiration time (optional)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Password reset token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = (
                datetime.now(timezone.utc) + self.config.password_reset_token_expiry
            )

        # Generate unique token ID
        token_id = secrets.token_hex(16)

        payload = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "password_reset",
            "jti": token_id,
        }

        token = jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

        # Store token hash in database for validation
        import hashlib

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        await db_client.store_password_reset_token(
            token_id=token_id,
            user_id=user_data.user_id,
            token_hash=token_hash,
            expires_at=expire,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return token

    async def verify_password_reset_token_with_storage(
        self, token: str, db_client
    ) -> Optional[UserData]:
        """
        Verify a password reset token using database storage and return user data.

        Args:
            token: Password reset token to verify
            db_client: Database client for token validation

        Returns:
            UserData if token is valid, None otherwise
        """
        try:
            # First validate the JWT token structure
            payload = await self.validate_password_reset_token(token)
            token_id = payload.get("jti")
            user_id = payload.get("sub")

            if not token_id or not user_id:
                return None

            # Check token in database
            import hashlib

            token_hash = hashlib.sha256(token.encode()).hexdigest()
            stored_token = await db_client.get_password_reset_token(token_id)

            if not stored_token:
                return None

            # Verify token hash matches
            if stored_token["token_hash"] != token_hash:
                return None

            # Check if token is expired
            if datetime.now(timezone.utc) > stored_token["expires_at"]:
                return None

            # Mark token as used
            await db_client.mark_password_reset_token_used(token_id)

            # Get user data from database
            user_data = await db_client.get_user_by_id(user_id)
            return user_data

        except (InvalidTokenError, TokenExpiredError):
            return None
        except Exception:
            return None

    async def create_email_verification_token_with_storage(
        self,
        user_data: UserData,
        db_client,
        expires_delta: Optional[timedelta] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> str:
        """
        Create an email verification token and store it in the database.

        Args:
            user_data: User data to encode in token
            db_client: Database client for token storage
            expires_delta: Custom expiration time (optional)
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Email verification token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = (
                datetime.now(timezone.utc) + self.config.email_verification_token_expiry
            )

        # Generate unique token ID
        token_id = secrets.token_hex(16)

        payload = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "email_verification",
            "jti": token_id,
        }

        token = jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

        # Store token hash in database for validation
        import hashlib

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        await db_client.store_email_verification_token(
            token_id=token_id,
            user_id=user_data.user_id,
            token_hash=token_hash,
            expires_at=expire,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return token

    async def verify_email_verification_token_with_storage(
        self, token: str, db_client
    ) -> Optional[UserData]:
        """
        Verify an email verification token using database storage and return user data.

        Args:
            token: Email verification token to verify
            db_client: Database client for token validation

        Returns:
            UserData if token is valid, None otherwise
        """
        try:
            # First validate the JWT token structure
            payload = await self.validate_email_verification_token(token)
            token_id = payload.get("jti")
            user_id = payload.get("sub")

            if not token_id or not user_id:
                return None

            # Check token in database
            import hashlib

            token_hash = hashlib.sha256(token.encode()).hexdigest()
            stored_token = await db_client.get_email_verification_token(token_id)

            if not stored_token:
                return None

            # Verify token hash matches
            if stored_token["token_hash"] != token_hash:
                return None

            # Check if token is expired
            if datetime.now(timezone.utc) > stored_token["expires_at"]:
                return None

            # Mark token as used
            await db_client.mark_email_verification_token_used(token_id)

            # Get user data from database
            user_data = await db_client.get_user_by_id(user_id)
            return user_data

        except (InvalidTokenError, TokenExpiredError):
            return None
        except Exception:
            return None

    async def verify_password_reset_token(self, token: str) -> Optional[UserData]:
        """
        Verify a password reset token and return the associated user data.

        Args:
            token: Password reset token to verify

        Returns:
            UserData if token is valid, None otherwise
        """
        try:
            payload = await self.validate_password_reset_token(token)
            user_id = payload.get("sub")

            if not user_id:
                return None

            # In a real implementation, this would fetch user data from database
            # For now, create a minimal UserData object
            return UserData(
                user_id=user_id,
                email=payload.get("email", ""),
                full_name=payload.get("full_name"),
                tenant_id=payload.get("tenant_id", "default"),
            )

        except (InvalidTokenError, TokenExpiredError):
            return None
        except Exception:
            return None


# Backward compatibility alias
TokenManager = EnhancedTokenManager


class SimpleTokenManager:
    """
    Simple token manager for environments without PyJWT.

    Uses basic token generation and validation without JWT.
    This is less secure and should only be used for development.
    """

    def __init__(self, config: JWTConfig) -> None:
        """Initialize simple token manager."""
        self.config = config
        self.tokens: Dict[str, Dict[str, Any]] = {}

    async def create_access_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a simple access token."""
        token = secrets.token_urlsafe(32)

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + self.config.access_token_expiry

        self.tokens[token] = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "roles": user_data.roles,
            "tenant_id": user_data.tenant_id,
            "is_verified": user_data.is_verified,
            "is_active": user_data.is_active,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        return token

    async def create_refresh_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a simple refresh token."""
        token = secrets.token_urlsafe(32)

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + self.config.refresh_token_expiry

        self.tokens[token] = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "tenant_id": user_data.tenant_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_hex(16),
        }

        return token

    async def validate_token(
        self, token: str, expected_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a simple token."""
        if token not in self.tokens:
            raise InvalidTokenError("Token not found", token_type=expected_type)

        payload = self.tokens[token]

        # Check expiration
        if datetime.now(timezone.utc) > payload["exp"]:
            del self.tokens[token]
            raise TokenExpiredError(token_type=expected_type)

        # Check token type
        if expected_type and payload.get("type") != expected_type:
            raise InvalidTokenError(
                f"Invalid token type. Expected {expected_type}, got {payload.get('type')}",
                token_type=expected_type,
            )

        return payload

    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate a simple access token."""
        return await self.validate_token(token, "access")

    async def validate_refresh_token(self, token: str) -> Dict[str, Any]:
        """Validate a simple refresh token."""
        return await self.validate_token(token, "refresh")
