"""
Data Encryption and Protection Service.

This service provides comprehensive encryption capabilities including:
- Data encryption at rest and in transit
- Key management and rotation
- Data classification and protection
- Secure storage mechanisms
"""

import asyncio
import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from sqlalchemy import select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.audit_logging import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
)

logger = get_logger(__name__)


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes-256-gcm"
    AES_256_CBC = "aes-256-cbc"
    CHACHA20_POLY1305 = "chacha20-poly1305"


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class KeyStatus(str, Enum):
    """Encryption key status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"


@dataclass
class EncryptionKey:
    """Encryption key data structure."""
    key_id: str
    algorithm: EncryptionAlgorithm
    key_data: bytes
    salt: bytes
    iv: Optional[bytes] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: KeyStatus = KeyStatus.ACTIVE
    usage_count: int = 0
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EncryptionResult:
    """Encryption operation result."""
    success: bool
    data: Optional[bytes] = None
    key_id: Optional[str] = None
    algorithm: Optional[EncryptionAlgorithm] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProtectionRule:
    """Data protection rule."""
    rule_id: str
    classification: DataClassification
    encryption_required: bool = True
    key_rotation_days: int = 90
    access_logging: bool = True
    retention_days: int = 2555  # 7 years
    allowed_locations: List[str] = field(default_factory=list)
    denied_locations: List[str] = field(default_factory=list)


@dataclass
class EncryptionConfig(ServiceConfig):
    """Encryption service configuration."""
    # Default encryption settings
    default_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    key_size_bits: int = 256
    iv_size_bytes: int = 12
    salt_size_bytes: int = 16
    
    # Key management settings
    key_rotation_days: int = 90
    key_retention_days: int = 365
    max_keys_per_user: int = 5
    key_derivation_iterations: int = 100000
    
    # Data protection settings
    enable_classification: bool = True
    default_classification: DataClassification = DataClassification.INTERNAL
    enable_auto_encryption: bool = True
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True
    
    # Storage settings
    secure_storage_path: str = "/tmp/secure_storage"
    temp_storage_path: str = "/tmp/temp_storage"
    
    # Performance settings
    encryption_cache_size: int = 100
    batch_size: int = 1000
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "encryption_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class KeyManager:
    """Encryption key management."""
    
    def __init__(self, config: EncryptionConfig):
        """Initialize key manager."""
        self.config = config
        self._keys: Dict[str, EncryptionKey] = {}
        self._key_cache: Dict[str, bytes] = {}
    
    def generate_key(
        self,
        algorithm: Optional[EncryptionAlgorithm] = None,
        expires_in_days: Optional[int] = None
    ) -> EncryptionKey:
        """
        Generate a new encryption key.
        
        Args:
            algorithm: Encryption algorithm to use
            expires_in_days: Number of days until key expires
            
        Returns:
            Generated encryption key
        """
        try:
            algorithm = algorithm or self.config.default_algorithm
            
            # Generate random key
            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                key_data = os.urandom(32)  # 256 bits
            elif algorithm == EncryptionAlgorithm.AES_256_CBC:
                key_data = os.urandom(32)  # 256 bits
            elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                key_data = os.urandom(32)  # 256 bits
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            # Generate salt
            salt = os.urandom(self.config.salt_size_bytes)
            
            # Generate IV if needed
            iv = None
            if algorithm in [EncryptionAlgorithm.AES_256_CBC]:
                iv = os.urandom(self.config.iv_size_bytes)
            
            # Calculate expiration
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create key object
            key = EncryptionKey(
                key_id=secrets.token_urlsafe(32),
                algorithm=algorithm,
                key_data=key_data,
                salt=salt,
                iv=iv,
                expires_at=expires_at
            )
            
            # Store key
            self._keys[key.key_id] = key
            
            logger.info(f"Generated encryption key: {key.key_id}")
            return key
            
        except Exception as e:
            logger.error(f"Error generating encryption key: {e}")
            raise
    
    def derive_key(
        self,
        password: str,
        salt: bytes,
        algorithm: Optional[EncryptionAlgorithm] = None
    ) -> bytes:
        """
        Derive encryption key from password.
        
        Args:
            password: User password
            salt: Salt for key derivation
            algorithm: Encryption algorithm
            
        Returns:
            Derived key bytes
        """
        try:
            algorithm = algorithm or self.config.default_algorithm
            
            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits
                salt=salt,
                iterations=self.config.key_derivation_iterations,
            )
            
            key = kdf.derive(password.encode())
            
            logger.debug(f"Derived encryption key from password")
            return key
            
        except Exception as e:
            logger.error(f"Error deriving encryption key: {e}")
            raise
    
    def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """
        Get encryption key by ID.
        
        Args:
            key_id: Key ID
            
        Returns:
            Encryption key or None if not found
        """
        return self._keys.get(key_id)
    
    def rotate_key(self, key_id: str) -> Optional[EncryptionKey]:
        """
        Rotate an encryption key.
        
        Args:
            key_id: Key ID to rotate
            
        Returns:
            New encryption key or None if rotation failed
        """
        try:
            old_key = self._keys.get(key_id)
            if not old_key:
                logger.warning(f"Key not found for rotation: {key_id}")
                return None
            
            # Generate new key
            new_key = self.generate_key(old_key.algorithm)
            
            # Mark old key as inactive
            old_key.status = KeyStatus.INACTIVE
            
            logger.info(f"Rotated encryption key: {key_id}")
            return new_key
            
        except Exception as e:
            logger.error(f"Error rotating encryption key: {e}")
            return None
    
    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an encryption key.
        
        Args:
            key_id: Key ID to revoke
            
        Returns:
            True if revocation was successful, False otherwise
        """
        try:
            key = self._keys.get(key_id)
            if not key:
                logger.warning(f"Key not found for revocation: {key_id}")
                return False
            
            # Mark key as revoked
            key.status = KeyStatus.REVOKED
            
            # Remove from cache
            if key_id in self._key_cache:
                del self._key_cache[key_id]
            
            logger.info(f"Revoked encryption key: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking encryption key: {e}")
            return False
    
    def get_active_keys(self, user_id: Optional[str] = None) -> List[EncryptionKey]:
        """
        Get active encryption keys.
        
        Args:
            user_id: Optional user ID filter
            
        Returns:
            List of active encryption keys
        """
        active_keys = []
        
        for key in self._keys.values():
            if key.status == KeyStatus.ACTIVE:
                if user_id is None or key.metadata.get("user_id") == user_id:
                    active_keys.append(key)
        
        return active_keys
    
    def cleanup_expired_keys(self) -> int:
        """
        Clean up expired keys.
        
        Returns:
            Number of keys cleaned up
        """
        now = datetime.utcnow()
        expired_count = 0
        
        for key_id, key in list(self._keys.items()):
            if key.expires_at and key.expires_at < now:
                key.status = KeyStatus.EXPIRED
                
                # Remove from cache
                if key_id in self._key_cache:
                    del self._key_cache[key_id]
                
                expired_count += 1
                logger.info(f"Expired encryption key: {key_id}")
        
        return expired_count


class EncryptionService(BaseService):
    """
    Data Encryption and Protection Service.
    
    This service provides comprehensive encryption capabilities including
    data encryption at rest and in transit, key management, and
    data protection mechanisms.
    """
    
    def __init__(self, config: Optional[EncryptionConfig] = None):
        """Initialize Encryption Service."""
        super().__init__(config or EncryptionConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Database session will be injected
        self._db_session: Optional[AsyncSession] = None
        
        # Thread-safe data structures
        self._protection_rules: Dict[str, DataProtectionRule] = {}
        self._encrypted_data_cache: Dict[str, bytes] = {}
        
        # Initialize managers
        self._key_manager = KeyManager(self.config)
        
        # Initialize audit logger
        self._audit_logger = get_audit_logger()
    
    async def initialize(self) -> None:
        """Initialize Encryption Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Validate configuration
                self._validate_config()
                
                # Load default protection rules
                self._load_default_protection_rules()
                
                self._initialized = True
                logger.info("Encryption Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Encryption Service: {e}")
                raise RuntimeError(f"Encryption Service initialization failed: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.config.key_size_bits < 128:
            logger.warning("Key size should be at least 128 bits")
        
        if self.config.key_rotation_days < 30:
            logger.warning("Key rotation should be at least every 30 days")
    
    def _load_default_protection_rules(self) -> None:
        """Load default data protection rules."""
        default_rules = [
            DataProtectionRule(
                rule_id="public_data",
                classification=DataClassification.PUBLIC,
                encryption_required=False,
                key_rotation_days=0,
                access_logging=False,
                retention_days=30
            ),
            DataProtectionRule(
                rule_id="internal_data",
                classification=DataClassification.INTERNAL,
                encryption_required=True,
                key_rotation_days=90,
                access_logging=True,
                retention_days=2555
            ),
            DataProtectionRule(
                rule_id="confidential_data",
                classification=DataClassification.CONFIDENTIAL,
                encryption_required=True,
                key_rotation_days=60,
                access_logging=True,
                retention_days=2555
            ),
            DataProtectionRule(
                rule_id="restricted_data",
                classification=DataClassification.RESTRICTED,
                encryption_required=True,
                key_rotation_days=30,
                access_logging=True,
                retention_days=2555
            ),
        ]
        
        for rule in default_rules:
            self._protection_rules[rule.rule_id] = rule
    
    def set_db_session(self, session: AsyncSession) -> None:
        """Set database session for the service."""
        self._db_session = session
    
    async def encrypt_data(
        self,
        data: Union[str, bytes, Dict[str, Any]],
        *,
        key_id: Optional[str] = None,
        algorithm: Optional[EncryptionAlgorithm] = None,
        classification: Optional[DataClassification] = None
    ) -> EncryptionResult:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            key_id: Optional key ID to use
            algorithm: Optional encryption algorithm
            classification: Data classification level
            
        Returns:
            Encryption result
        """
        try:
            # Convert data to bytes if needed
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = data
            
            # Get or generate key
            if key_id:
                key = self._key_manager.get_key(key_id)
                if not key:
                    return EncryptionResult(
                        success=False,
                        error_message=f"Key not found: {key_id}"
                    )
            else:
                if key.status != KeyStatus.ACTIVE:
                    return EncryptionResult(
                        success=False,
                        error_message=f"Key is not active: {key_id}"
                    )
            else:
                key = self._key_manager.generate_key(algorithm)
            
            # Get protection rule
            rule = self._get_protection_rule(classification or self.config.default_classification)
            
            # Check if encryption is required
            if rule.encryption_required and not key:
                return EncryptionResult(
                    success=False,
                    error_message=f"Encryption required for {classification.value} data"
                )
            
            # Encrypt data
            if key.algorithm == EncryptionAlgorithm.AES_256_GCM:
                # Use authenticated encryption
                fernet = Fernet(base64.urlsafe_b64encode(key.key_data))
                encrypted_data = fernet.encrypt(data_bytes)
                
                result = EncryptionResult(
                    success=True,
                    data=encrypted_data,
                    key_id=key.key_id,
                    algorithm=key.algorithm
                )
            else:
                # Use standard encryption
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                
                # Generate random IV if not provided
                iv = key.iv or os.urandom(self.config.iv_size_bytes)
                
                # Create cipher
                cipher = Cipher(
                    algorithms.AES(key.key_data),
                    modes.GCM(iv),
                    backend=default_backend()
                )
                
                # Encrypt data
                encryptor = cipher.encryptor()
                encrypted_data = encryptor.update(data_bytes).finalize()
                
                result = EncryptionResult(
                    success=True,
                    data=encrypted_data,
                    key_id=key.key_id,
                    algorithm=key.algorithm,
                    metadata={"iv": iv}
                )
            
            # Update key usage
            key.usage_count += 1
            key.last_used = datetime.utcnow()
            
            # Log encryption
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Data encrypted with {key.algorithm.value}",
                "metadata": {
                    "key_id": key.key_id,
                    "algorithm": key.algorithm.value,
                    "data_size": len(data_bytes),
                    "classification": classification.value if classification else self.config.default_classification.value
                }
            })
            
            logger.info(f"Data encrypted with key {key.key_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return EncryptionResult(
                success=False,
                error_message=f"Encryption error: {str(e)}"
            )
    
    async def decrypt_data(
        self,
        encrypted_data: bytes,
        key_id: str,
        *,
        iv: Optional[bytes] = None
    ) -> EncryptionResult:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data
            key_id: Key ID to use
            iv: Initialization vector (if needed)
            
        Returns:
            Encryption result
        """
        try:
            # Get key
            key = self._key_manager.get_key(key_id)
            if not key:
                return EncryptionResult(
                    success=False,
                    error_message=f"Key not found: {key_id}"
                )
            
            if key.status != KeyStatus.ACTIVE:
                return EncryptionResult(
                    success=False,
                    error_message=f"Key is not active: {key_id}"
                )
            
            # Decrypt data
            if key.algorithm == EncryptionAlgorithm.AES_256_GCM:
                # Use authenticated decryption
                fernet = Fernet(base64.urlsafe_b64encode(key.key_data))
                decrypted_data = fernet.decrypt(encrypted_data)
                
                result = EncryptionResult(
                    success=True,
                    data=decrypted_data,
                    key_id=key_id,
                    algorithm=key.algorithm
                )
            else:
                # Use standard decryption
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                
                # Get IV from metadata or parameter
                iv = iv or key.iv
                if not iv:
                    return EncryptionResult(
                        success=False,
                        error_message="IV required for decryption"
                    )
                
                # Create cipher
                cipher = Cipher(
                    algorithms.AES(key.key_data),
                    modes.GCM(iv),
                    backend=default_backend()
                )
                
                # Decrypt data
                decryptor = cipher.decryptor()
                decrypted_data = decryptor.update(encrypted_data).finalize()
                
                result = EncryptionResult(
                    success=True,
                    data=decrypted_data,
                    key_id=key_id,
                    algorithm=key.algorithm
                )
            
            # Update key usage
            key.usage_count += 1
            key.last_used = datetime.utcnow()
            
            # Log decryption
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Data decrypted with {key.algorithm.value}",
                "metadata": {
                    "key_id": key_id,
                    "algorithm": key.algorithm.value,
                    "data_size": len(encrypted_data)
                }
            })
            
            logger.info(f"Data decrypted with key {key_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return EncryptionResult(
                success=False,
                error_message=f"Decryption error: {str(e)}"
            )
    
    async def generate_encryption_key(
        self,
        user_id: str,
        *,
        algorithm: Optional[EncryptionAlgorithm] = None,
        expires_in_days: Optional[int] = None
    ) -> EncryptionResult:
        """
        Generate a new encryption key for a user.
        
        Args:
            user_id: User ID
            algorithm: Optional encryption algorithm
            expires_in_days: Number of days until key expires
            
        Returns:
            Encryption result
        """
        try:
            # Generate key
            key = self._key_manager.generate_key(algorithm, expires_in_days)
            
            # Add user metadata
            key.metadata["user_id"] = user_id
            key.metadata["created_for"] = "user_encryption"
            
            # Store key
            self._key_manager._keys[key.key_id] = key
            
            # Log key generation
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Encryption key generated for user {user_id}",
                "user_id": user_id,
                "metadata": {
                    "key_id": key.key_id,
                    "algorithm": key.algorithm.value,
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None
                }
            })
            
            logger.info(f"Generated encryption key for user {user_id}: {key.key_id}")
            return EncryptionResult(
                success=True,
                key_id=key.key_id,
                algorithm=key.algorithm
            )
            
        except Exception as e:
            logger.error(f"Error generating encryption key: {e}")
            return EncryptionResult(
                success=False,
                error_message=f"Key generation error: {str(e)}"
            )
    
    async def rotate_encryption_key(
        self,
        key_id: str
    ) -> EncryptionResult:
        """
        Rotate an encryption key.
        
        Args:
            key_id: Key ID to rotate
            
        Returns:
            Encryption result
        """
        try:
            # Rotate key
            new_key = self._key_manager.rotate_key(key_id)
            if not new_key:
                return EncryptionResult(
                    success=False,
                    error_message=f"Key rotation failed: {key_id}"
                )
            
            # Log key rotation
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Encryption key rotated: {key_id}",
                "metadata": {
                    "old_key_id": key_id,
                    "new_key_id": new_key.key_id,
                    "algorithm": new_key.algorithm.value
                }
            })
            
            logger.info(f"Rotated encryption key: {key_id} -> {new_key.key_id}")
            return EncryptionResult(
                success=True,
                key_id=new_key.key_id,
                algorithm=new_key.algorithm
            )
            
        except Exception as e:
            logger.error(f"Error rotating encryption key: {e}")
            return EncryptionResult(
                success=False,
                error_message=f"Key rotation error: {str(e)}"
            )
    
    async def revoke_encryption_key(
        self,
        key_id: str
    ) -> EncryptionResult:
        """
        Revoke an encryption key.
        
        Args:
            key_id: Key ID to revoke
            
        Returns:
            Encryption result
        """
        try:
            # Revoke key
            success = self._key_manager.revoke_key(key_id)
            
            if success:
                # Log key revocation
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.WARNING,
                    "message": f"Encryption key revoked: {key_id}",
                    "metadata": {
                        "key_id": key_id
                    }
                })
                
                logger.info(f"Revoked encryption key: {key_id}")
                return EncryptionResult(success=True)
            else:
                return EncryptionResult(
                    success=False,
                    error_message=f"Key revocation failed: {key_id}"
                )
            
        except Exception as e:
            logger.error(f"Error revoking encryption key: {e}")
            return EncryptionResult(
                success=False,
                error_message=f"Key revocation error: {str(e)}"
            )
    
    def _get_protection_rule(self, classification: DataClassification) -> DataProtectionRule:
        """Get protection rule for data classification."""
        return self._protection_rules.get(classification.value, self._protection_rules["internal_data"])
    
    async def get_user_keys(self, user_id: str) -> List[EncryptionKey]:
        """
        Get encryption keys for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of encryption keys
        """
        return self._key_manager.get_active_keys(user_id)
    
    async def get_encryption_statistics(self) -> Dict[str, Any]:
        """
        Get encryption service statistics.
        
        Returns:
            Dictionary with encryption statistics
        """
        try:
            all_keys = list(self._key_manager._keys.values())
            active_keys = [k for k in all_keys if k.status == KeyStatus.ACTIVE]
            expired_keys = [k for k in all_keys if k.status == KeyStatus.EXPIRED]
            revoked_keys = [k for k in all_keys if k.status == KeyStatus.REVOKED]
            
            # Calculate algorithm distribution
            algorithm_counts = {}
            for key in all_keys:
                algorithm = key.algorithm.value
                algorithm_counts[algorithm] = algorithm_counts.get(algorithm, 0) + 1
            
            return {
                "total_keys": len(all_keys),
                "active_keys": len(active_keys),
                "expired_keys": len(expired_keys),
                "revoked_keys": len(revoked_keys),
                "algorithm_distribution": algorithm_counts,
                "protection_rules": len(self._protection_rules),
                "encryption_enabled": self.config.enable_auto_encryption,
                "encrypt_at_rest": self.config.encrypt_at_rest,
                "encrypt_in_transit": self.config.encrypt_in_transit
            }
            
        except Exception as e:
            logger.error(f"Error getting encryption statistics: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check the health of the Encryption Service."""
        if not self._initialized:
            return False
        
        try:
            # Test key generation
            test_key = self._key_manager.generate_key()
            if not test_key.key_id:
                return False
            
            # Test data encryption
            test_data = b"test data for encryption health check"
            encrypt_result = await self.encrypt_data(test_data, key_id=test_key.key_id)
            
            if not encrypt_result.success:
                return False
            
            # Test data decryption
            decrypt_result = await self.decrypt_data(encrypt_result.data, test_key.key_id)
            
            if not decrypt_result.success:
                return False
            
            # Verify data integrity
            if decrypt_result.data != test_data:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Encryption Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Encryption Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Encryption Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Encryption Service."""
        if not self._initialized:
            return
        
        # Clean up expired keys
        self._key_manager.cleanup_expired_keys()
        
        # Clear caches
        self._encrypted_data_cache.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Encryption Service stopped successfully")


__all__ = [
    "EncryptionService",
    "EncryptionConfig",
    "KeyManager",
    "EncryptionKey",
    "EncryptionResult",
    "DataProtectionRule",
    "EncryptionAlgorithm",
    "DataClassification",
    "KeyStatus",
]