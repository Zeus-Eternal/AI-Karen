"""
Token management for the consolidated authentication service.

This module provides JWT token creation, validation, and management
for access tokens, refresh tokens, and other authentication tokens.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

try:
    import jwt
except ImportError:
    # Fallback for environments without PyJWT
    jwt = None

from .config import JWTConfig
from .exceptions import InvalidTokenError, TokenExpiredError
from .models import UserData


class TokenManager:
    """
    JWT token manager for authentication tokens.

    Handles creation and validation of access tokens, refresh tokens,
    and other authentication-related tokens.
    """

    def __init__(self, config: JWTConfig) -> None:
        """Initialize token manager with JWT configuration."""
        self.config = config

        if jwt is None:
            raise ImportError(
                "PyJWT is required for token management. Install with: pip install PyJWT"
            )

    async def create_access_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token for a user.

        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time (optional)

        Returns:
            JWT access token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + self.config.access_token_expiry

        payload = {
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

        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

    async def create_refresh_token(
        self, user_data: UserData, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token for a user.

        Args:
            user_data: User data to encode in token
            expires_delta: Custom expiration time (optional)

        Returns:
            JWT refresh token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + self.config.refresh_token_expiry

        payload = {
            "sub": user_data.user_id,
            "email": user_data.email,
            "tenant_id": user_data.tenant_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_hex(16),  # Unique token ID for revocation
        }

        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

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
        Validate a JWT token and return its payload.

        Args:
            token: JWT token to validate
            expected_type: Expected token type (optional)

        Returns:
            Token payload dictionary

        Raises:
            InvalidTokenError: If token is invalid or malformed
            TokenExpiredError: If token has expired
        """
        try:
            payload = jwt.decode(
                token, self.config.secret_key, algorithms=[self.config.algorithm]
            )

            # Check token type if specified
            if expected_type and payload.get("type") != expected_type:
                raise InvalidTokenError(
                    f"Invalid token type. Expected {expected_type}, got {payload.get('type')}",
                    token_type=expected_type,
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError(token_type=expected_type)
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {e}", token_type=expected_type)
        except Exception as e:
            raise InvalidTokenError(
                f"Token validation failed: {e}", token_type=expected_type
            )

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

    async def refresh_access_token(
        self, refresh_token: str, user_data: UserData
    ) -> str:
        """
        Create a new access token using a refresh token.

        Args:
            refresh_token: Valid refresh token
            user_data: Current user data

        Returns:
            New access token

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

        # Create new access token
        return await self.create_access_token(user_data)

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

            return datetime.fromtimestamp(payload["exp"])

        except Exception:
            return None

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
