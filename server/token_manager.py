# mypy: ignore-errors
"""
Token Management Utilities for Extension Runtime Authentication.
Handles JWT token generation, validation, refresh logic, blacklisting, and service-to-service authentication.
"""

import jwt
import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import asyncio
import json

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    """Token types for different authentication scenarios."""
    ACCESS = "access"
    REFRESH = "refresh"
    SERVICE = "service"
    BACKGROUND_TASK = "background_task"
    API_KEY = "api_key"


class TokenStatus(str, Enum):
    """Token status for validation and blacklisting."""
    VALID = "valid"
    EXPIRED = "expired"
    BLACKLISTED = "blacklisted"
    INVALID = "invalid"
    REVOKED = "revoked"


@dataclass
class TokenPayload:
    """Structured token payload for consistent token generation."""
    user_id: Optional[str] = None
    service_name: Optional[str] = None
    tenant_id: str = "default"
    roles: List[str] = None
    permissions: List[str] = None
    token_type: TokenType = TokenType.ACCESS
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    issuer: str = "kari-extension-system"
    audience: str = "kari-extensions"
    jti: Optional[str] = None  # JWT ID for blacklisting
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.roles is None:
            self.roles = ["user"]
        if self.permissions is None:
            self.permissions = ["extension:read"]
        if self.issued_at is None:
            self.issued_at = datetime.now(timezone.utc)
        if self.jti is None:
            self.jti = self._generate_jti()
    
    def _generate_jti(self) -> str:
        """Generate unique JWT ID for token tracking."""
        # Create unique ID based on user/service, timestamp, and random component
        identifier = self.user_id or self.service_name or "anonymous"
        timestamp = int(self.issued_at.timestamp()) if self.issued_at else int(datetime.now(timezone.utc).timestamp())
        random_component = secrets.token_hex(8)
        
        # Create hash for consistent length
        content = f"{identifier}:{timestamp}:{random_component}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_jwt_payload(self) -> Dict[str, Any]:
        """Convert to JWT payload format."""
        payload = {
            "jti": self.jti,
            "iss": self.issuer,
            "aud": self.audience,
            "token_type": self.token_type.value,
            "iat": int(self.issued_at.timestamp()),
        }
        
        if self.expires_at:
            payload["exp"] = int(self.expires_at.timestamp())
        
        if self.user_id:
            payload["user_id"] = self.user_id
        
        if self.service_name:
            payload["service_name"] = self.service_name
        
        payload.update({
            "tenant_id": self.tenant_id,
            "roles": self.roles,
            "permissions": self.permissions,
        })
        
        return payload


class TokenBlacklist:
    """Redis-based token blacklist for security."""
    
    def __init__(self, redis_client: Optional[Any] = None, key_prefix: str = "token_blacklist"):
        """Initialize token blacklist with Redis client."""
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.local_blacklist: Set[str] = set()  # Fallback for when Redis is unavailable
        self.use_redis = redis_client is not None
        
        if not self.use_redis:
            logger.warning("Redis client not available, using in-memory token blacklist")
    
    async def blacklist_token(self, jti: str, expires_at: Optional[datetime] = None) -> bool:
        """Add token to blacklist."""
        try:
            if self.use_redis:
                key = f"{self.key_prefix}:{jti}"
                
                # Set expiration to match token expiration or default to 24 hours
                if expires_at:
                    ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
                    if ttl > 0:
                        await self._redis_set(key, "blacklisted", ex=ttl)
                    else:
                        # Token already expired, no need to blacklist
                        return True
                else:
                    # Default TTL of 24 hours
                    await self._redis_set(key, "blacklisted", ex=86400)
                
                logger.info(f"Token {jti} added to Redis blacklist")
            else:
                # Fallback to local blacklist
                self.local_blacklist.add(jti)
                logger.info(f"Token {jti} added to local blacklist")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to blacklist token {jti}: {e}")
            # Fallback to local blacklist
            self.local_blacklist.add(jti)
            return False
    
    async def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        try:
            if self.use_redis:
                key = f"{self.key_prefix}:{jti}"
                result = await self._redis_get(key)
                return result is not None
            else:
                return jti in self.local_blacklist
                
        except Exception as e:
            logger.error(f"Failed to check blacklist for token {jti}: {e}")
            # Fallback to local blacklist
            return jti in self.local_blacklist
    
    async def remove_from_blacklist(self, jti: str) -> bool:
        """Remove token from blacklist (for token refresh scenarios)."""
        try:
            if self.use_redis:
                key = f"{self.key_prefix}:{jti}"
                await self._redis_delete(key)
                logger.info(f"Token {jti} removed from Redis blacklist")
            else:
                self.local_blacklist.discard(jti)
                logger.info(f"Token {jti} removed from local blacklist")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove token {jti} from blacklist: {e}")
            return False
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens from local blacklist (Redis handles TTL automatically)."""
        if not self.use_redis:
            # For local blacklist, we can't determine expiration without additional metadata
            # This would require storing expiration times, which is complex for the fallback
            # For now, we'll rely on periodic full cleanup or Redis TTL
            pass
        
        return 0
    
    async def _redis_set(self, key: str, value: str, ex: int) -> None:
        """Async wrapper for Redis SET operation."""
        if self.redis_client:
            # For sync Redis client, we'll use it directly
            # In a real async implementation, you'd use aioredis
            self.redis_client.set(key, value, ex=ex)
    
    async def _redis_get(self, key: str) -> Optional[str]:
        """Async wrapper for Redis GET operation."""
        if self.redis_client:
            return self.redis_client.get(key)
        return None
    
    async def _redis_delete(self, key: str) -> None:
        """Async wrapper for Redis DELETE operation."""
        if self.redis_client:
            self.redis_client.delete(key)


class TokenManager:
    """Comprehensive token management for extension authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize token manager with configuration."""
        self.config = config
        self.secret_key = config.get("secret_key", "dev-secret-key")
        self.algorithm = config.get("algorithm", "HS256")
        self.access_token_expire_minutes = config.get("access_token_expire_minutes", 60)
        self.service_token_expire_minutes = config.get("service_token_expire_minutes", 30)
        self.refresh_token_expire_days = config.get("refresh_token_expire_days", 7)
        self.blacklist_enabled = config.get("token_blacklist_enabled", True)
        
        # Initialize token blacklist
        self.blacklist = None
        if self.blacklist_enabled:
            try:
                # Try to initialize Redis client for blacklist if available
                if REDIS_AVAILABLE:
                    redis_url = config.get("redis_url", "redis://localhost:6379/0")
                    redis_client = redis.from_url(redis_url, decode_responses=True)
                    self.blacklist = TokenBlacklist(redis_client)
                else:
                    logger.info("Redis not available, using local token blacklist")
                    self.blacklist = TokenBlacklist()  # Use local fallback
            except Exception as e:
                logger.warning(f"Failed to initialize Redis for token blacklist: {e}")
                self.blacklist = TokenBlacklist()  # Use local fallback
        
        # Token refresh tracking
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Token manager initialized with blacklist support")
    
    def generate_access_token(
        self,
        user_id: str,
        tenant_id: str = "default",
        roles: List[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, TokenPayload]:
        """Generate JWT access token for user authentication."""
        
        if expires_delta:
            expires_at = datetime.now(timezone.utc) + expires_delta
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = TokenPayload(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles or ["user"],
            permissions=permissions or ["extension:read"],
            token_type=TokenType.ACCESS,
            expires_at=expires_at
        )
        
        token = jwt.encode(payload.to_jwt_payload(), self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"Generated access token for user {user_id} (expires: {expires_at})")
        return token, payload
    
    def generate_refresh_token(
        self,
        user_id: str,
        tenant_id: str = "default",
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, TokenPayload]:
        """Generate refresh token for token renewal."""
        
        if expires_delta:
            expires_at = datetime.now(timezone.utc) + expires_delta
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        payload = TokenPayload(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=["refresh"],
            permissions=["token:refresh"],
            token_type=TokenType.REFRESH,
            expires_at=expires_at
        )
        
        token = jwt.encode(payload.to_jwt_payload(), self.secret_key, algorithm=self.algorithm)
        
        # Store refresh token metadata for validation
        self.refresh_tokens[payload.jti] = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "issued_at": payload.issued_at,
            "expires_at": expires_at,
            "used": False
        }
        
        logger.debug(f"Generated refresh token for user {user_id} (expires: {expires_at})")
        return token, payload
    
    def generate_service_token(
        self,
        service_name: str,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, TokenPayload]:
        """Generate service-to-service authentication token."""
        
        if expires_delta:
            expires_at = datetime.now(timezone.utc) + expires_delta
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.service_token_expire_minutes)
        
        payload = TokenPayload(
            service_name=service_name,
            tenant_id="system",
            roles=["service"],
            permissions=permissions or ["extension:background_tasks", "extension:health"],
            token_type=TokenType.SERVICE,
            expires_at=expires_at
        )
        
        token = jwt.encode(payload.to_jwt_payload(), self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"Generated service token for {service_name} (expires: {expires_at})")
        return token, payload
    
    def generate_background_task_token(
        self,
        task_name: str,
        user_id: Optional[str] = None,
        service_name: Optional[str] = None,
        permissions: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> Tuple[str, TokenPayload]:
        """Generate token specifically for background task execution."""
        
        if expires_delta:
            expires_at = datetime.now(timezone.utc) + expires_delta
        else:
            # Background task tokens have shorter expiration (15 minutes default)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Determine identifier and tenant
        if user_id:
            identifier = user_id
            tenant_id = "default"
        elif service_name:
            identifier = None
            tenant_id = "system"
        else:
            identifier = f"task:{task_name}"
            tenant_id = "system"
        
        payload = TokenPayload(
            user_id=identifier,
            service_name=service_name,
            tenant_id=tenant_id,
            roles=["background_task"],
            permissions=permissions or ["extension:background_tasks", "extension:execute"],
            token_type=TokenType.BACKGROUND_TASK,
            expires_at=expires_at
        )
        
        token = jwt.encode(payload.to_jwt_payload(), self.secret_key, algorithm=self.algorithm)
        
        logger.debug(f"Generated background task token for {task_name} (expires: {expires_at})")
        return token, payload
    
    async def validate_token(self, token: str) -> Tuple[TokenStatus, Optional[Dict[str, Any]]]:
        """Validate JWT token and return status with payload."""
        try:
            # Decode token without verification first to get JTI for blacklist check
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            jti = unverified_payload.get("jti")
            
            # Check blacklist if enabled
            if self.blacklist_enabled and self.blacklist and jti:
                if await self.blacklist.is_blacklisted(jti):
                    logger.warning(f"Token {jti} is blacklisted")
                    return TokenStatus.BLACKLISTED, None
            
            # Verify token signature and expiration
            # Note: We don't verify audience to maintain compatibility
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_aud": False}
            )
            
            # Additional validation for refresh tokens
            if payload.get("token_type") == TokenType.REFRESH.value:
                if not self._validate_refresh_token(payload):
                    return TokenStatus.INVALID, None
            
            logger.debug(f"Token {jti} validated successfully")
            return TokenStatus.VALID, payload
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token validation failed: expired")
            return TokenStatus.EXPIRED, None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Token validation failed: invalid ({e})")
            return TokenStatus.INVALID, None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return TokenStatus.INVALID, None
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        new_permissions: Optional[List[str]] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Refresh access token using refresh token."""
        try:
            # Validate refresh token
            status, payload = await self.validate_token(refresh_token)
            
            if status != TokenStatus.VALID:
                logger.warning(f"Refresh token validation failed: {status}")
                return None, None, None
            
            if payload.get("token_type") != TokenType.REFRESH.value:
                logger.warning("Invalid token type for refresh operation")
                return None, None, None
            
            # Check if refresh token was already used
            jti = payload.get("jti")
            if jti in self.refresh_tokens and self.refresh_tokens[jti].get("used"):
                logger.warning(f"Refresh token {jti} already used")
                return None, None, None
            
            # Mark refresh token as used
            if jti in self.refresh_tokens:
                self.refresh_tokens[jti]["used"] = True
            
            # Generate new access token
            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id", "default")
            
            # Use new permissions if provided, otherwise use default
            permissions = new_permissions or ["extension:read", "extension:write"]
            
            new_access_token, access_payload = self.generate_access_token(
                user_id=user_id,
                tenant_id=tenant_id,
                permissions=permissions
            )
            
            # Generate new refresh token
            new_refresh_token, refresh_payload = self.generate_refresh_token(
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            # Blacklist old refresh token
            if self.blacklist_enabled and self.blacklist and jti:
                await self.blacklist.blacklist_token(jti, datetime.fromtimestamp(payload.get("exp", 0), timezone.utc))
            
            logger.info(f"Successfully refreshed tokens for user {user_id}")
            return new_access_token, new_refresh_token, access_payload.to_jwt_payload()
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None, None, None
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke token by adding to blacklist."""
        try:
            # Decode token to get JTI and expiration
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if not jti:
                logger.warning("Cannot revoke token without JTI")
                return False
            
            if self.blacklist_enabled and self.blacklist:
                expires_at = datetime.fromtimestamp(exp, timezone.utc) if exp else None
                success = await self.blacklist.blacklist_token(jti, expires_at)
                
                if success:
                    logger.info(f"Token {jti} revoked successfully")
                    return True
                else:
                    logger.error(f"Failed to revoke token {jti}")
                    return False
            else:
                logger.warning("Token blacklist not enabled, cannot revoke token")
                return False
                
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a specific user (requires additional tracking)."""
        # This would require maintaining a user-to-token mapping
        # For now, we'll implement a basic version that clears refresh tokens
        revoked_count = 0
        
        try:
            # Remove all refresh tokens for the user
            tokens_to_remove = []
            for jti, token_data in self.refresh_tokens.items():
                if token_data.get("user_id") == user_id:
                    tokens_to_remove.append(jti)
            
            for jti in tokens_to_remove:
                del self.refresh_tokens[jti]
                if self.blacklist_enabled and self.blacklist:
                    await self.blacklist.blacklist_token(jti)
                revoked_count += 1
            
            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Failed to revoke tokens for user {user_id}: {e}")
            return 0
    
    def _validate_refresh_token(self, payload: Dict[str, Any]) -> bool:
        """Validate refresh token payload."""
        jti = payload.get("jti")
        
        if not jti or jti not in self.refresh_tokens:
            return False
        
        token_data = self.refresh_tokens[jti]
        
        # Check if token was already used
        if token_data.get("used"):
            return False
        
        # Check expiration
        expires_at = token_data.get("expires_at")
        if expires_at and datetime.now(timezone.utc) > expires_at:
            return False
        
        return True
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token information without validation (for debugging)."""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Add human-readable timestamps
            if "iat" in payload:
                payload["issued_at_readable"] = datetime.fromtimestamp(payload["iat"], timezone.utc).isoformat()
            
            if "exp" in payload:
                payload["expires_at_readable"] = datetime.fromtimestamp(payload["exp"], timezone.utc).isoformat()
                payload["time_until_expiry"] = str(datetime.fromtimestamp(payload["exp"], timezone.utc) - datetime.now(timezone.utc))
            
            return payload
            
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None
    
    async def cleanup_expired_refresh_tokens(self) -> int:
        """Clean up expired refresh tokens from memory."""
        current_time = datetime.now(timezone.utc)
        expired_tokens = []
        
        for jti, token_data in self.refresh_tokens.items():
            expires_at = token_data.get("expires_at")
            if expires_at and current_time > expires_at:
                expired_tokens.append(jti)
        
        for jti in expired_tokens:
            del self.refresh_tokens[jti]
        
        logger.info(f"Cleaned up {len(expired_tokens)} expired refresh tokens")
        return len(expired_tokens)


# Global token manager instance
_token_manager: Optional[TokenManager] = None


def get_token_manager(config: Optional[Dict[str, Any]] = None) -> TokenManager:
    """Get or create global token manager instance."""
    global _token_manager
    
    if _token_manager is None:
        if config is None:
            # Import here to avoid circular imports
            from server.config import settings
            config = settings.get_extension_auth_config()
        
        _token_manager = TokenManager(config)
    
    return _token_manager


def create_token_manager(config: Dict[str, Any]) -> TokenManager:
    """Create a new token manager instance with specific configuration."""
    return TokenManager(config)


# Convenience functions for common token operations
async def generate_user_tokens(
    user_id: str,
    tenant_id: str = "default",
    roles: List[str] = None,
    permissions: List[str] = None
) -> Dict[str, Any]:
    """Generate both access and refresh tokens for a user."""
    token_manager = get_token_manager()
    
    access_token, access_payload = token_manager.generate_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        roles=roles,
        permissions=permissions
    )
    
    refresh_token, refresh_payload = token_manager.generate_refresh_token(
        user_id=user_id,
        tenant_id=tenant_id
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": token_manager.access_token_expire_minutes * 60,
        "access_payload": access_payload.to_jwt_payload(),
        "refresh_payload": refresh_payload.to_jwt_payload()
    }


async def validate_and_extract_user_context(token: str) -> Optional[Dict[str, Any]]:
    """Validate token and extract user context for API endpoints."""
    token_manager = get_token_manager()
    status, payload = await token_manager.validate_token(token)
    
    if status != TokenStatus.VALID or not payload:
        return None
    
    # Convert JWT payload to user context format
    if payload.get("token_type") == TokenType.SERVICE.value:
        return {
            'service_name': payload.get('service_name'),
            'token_type': 'service',
            'permissions': payload.get('permissions', []),
            'user_id': f"service:{payload.get('service_name')}",
            'tenant_id': 'system',
            'roles': ['service']
        }
    else:
        return {
            'user_id': payload.get('user_id'),
            'tenant_id': payload.get('tenant_id', 'default'),
            'roles': payload.get('roles', []),
            'permissions': payload.get('permissions', []),
            'token_type': payload.get('token_type', 'access'),
            'jti': payload.get('jti')
        }