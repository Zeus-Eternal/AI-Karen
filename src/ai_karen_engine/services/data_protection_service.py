"""
Data Protection Service for CoPilot Architecture.

This service provides comprehensive data protection functionality including
encryption, data masking, anonymization, and data retention policies.
"""

import asyncio
import logging
import base64
import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionAlgorithm(str, Enum):
    """Encryption algorithm enumeration."""
    AES_256 = "aes_256"
    RSA_2048 = "rsa_2048"
    FERNET = "fernet"


class DataSensitivity(str, Enum):
    """Data sensitivity level enumeration."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_RESTRICTED = "highly_restricted"


class RetentionPolicy(str, Enum):
    """Data retention policy enumeration."""
    IMMEDIATE = "immediate"  # Delete immediately
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 90 days
    LONG_TERM = "long_term"  # 1 year
    PERMANENT = "permanent"  # Never delete


@dataclass
class EncryptionKey:
    """Encryption key data structure."""
    key_id: str
    name: str
    algorithm: EncryptionAlgorithm
    key_data: bytes
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProtectionPolicy:
    """Data protection policy data structure."""
    policy_id: str
    name: str
    description: str
    sensitivity_levels: List[DataSensitivity]
    encryption_required: bool = True
    masking_required: bool = False
    retention_policy: RetentionPolicy = RetentionPolicy.MEDIUM_TERM
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProtectionResult:
    """Data protection result data structure."""
    is_protected: bool
    protection_type: str
    data: Any
    key_id: Optional[str] = None
    policy_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DataProtectionConfig(ServiceConfig):
    """Data protection configuration."""
    enable_encryption: bool = True
    enable_data_masking: bool = True
    enable_anonymization: bool = True
    enable_retention_policies: bool = True
    default_encryption_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
    key_rotation_days: int = 90
    data_retention_days: int = 90
    key_store_path: str = "data/keys"
    secure_erase: bool = True
    compliance_mode: bool = False
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "data_protection_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class DataProtectionService(BaseService):
    """
    Data Protection Service for CoPilot Architecture.
    
    This service provides comprehensive data protection functionality including
    encryption, data masking, anonymization, and data retention policies.
    """
    
    def __init__(self, config: Optional[DataProtectionConfig] = None):
        """Initialize the Data Protection Service."""
        super().__init__(config or DataProtectionConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Thread-safe data structures
        self._encryption_keys: Dict[str, EncryptionKey] = {}
        self._protection_policies: Dict[str, DataProtectionPolicy] = {}
        self._fernet_encryptors: Dict[str, Fernet] = {}
        self._rsa_private_keys: Dict[str, rsa.RSAPrivateKey] = {}
        self._rsa_public_keys: Dict[str, rsa.RSAPublicKey] = {}
        
        # Load configuration from environment
        self._load_config_from_env()
    
    def _load_config_from_env(self) -> None:
        """Load configuration from environment variables."""
        import os
        
        if "DATA_PROTECTION_ENABLE_ENCRYPTION" in os.environ:
            self.config.enable_encryption = os.environ["DATA_PROTECTION_ENABLE_ENCRYPTION"].lower() == "true"
        
        if "DATA_PROTECTION_ENABLE_MASKING" in os.environ:
            self.config.enable_data_masking = os.environ["DATA_PROTECTION_ENABLE_MASKING"].lower() == "true"
        
        if "DATA_PROTECTION_ENABLE_ANONYMIZATION" in os.environ:
            self.config.enable_anonymization = os.environ["DATA_PROTECTION_ENABLE_ANONYMIZATION"].lower() == "true"
        
        if "DATA_PROTECTION_ENABLE_RETENTION" in os.environ:
            self.config.enable_retention_policies = os.environ["DATA_PROTECTION_ENABLE_RETENTION"].lower() == "true"
        
        if "DATA_PROTECTION_KEY_ROTATION_DAYS" in os.environ:
            self.config.key_rotation_days = int(os.environ["DATA_PROTECTION_KEY_ROTATION_DAYS"])
        
        if "DATA_PROTECTION_RETENTION_DAYS" in os.environ:
            self.config.data_retention_days = int(os.environ["DATA_PROTECTION_RETENTION_DAYS"])
        
        if "DATA_PROTECTION_SECURE_ERASE" in os.environ:
            self.config.secure_erase = os.environ["DATA_PROTECTION_SECURE_ERASE"].lower() == "true"
        
        if "DATA_PROTECTION_COMPLIANCE_MODE" in os.environ:
            self.config.compliance_mode = os.environ["DATA_PROTECTION_COMPLIANCE_MODE"].lower() == "true"
    
    async def initialize(self) -> None:
        """Initialize the Data Protection Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Create key store directory if it doesn't exist
                os.makedirs(self.config.key_store_path, exist_ok=True)
                
                # Load existing keys
                await self._load_existing_keys()
                
                # Load default policies
                await self._load_default_policies()
                
                # Generate default key if none exists
                if not self._encryption_keys:
                    await self._generate_default_key()
                
                self._initialized = True
                logger.info("Data Protection Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Data Protection Service: {e}")
                raise RuntimeError(f"Data Protection Service initialization failed: {e}")
    
    async def _load_existing_keys(self) -> None:
        """Load existing encryption keys from disk."""
        try:
            key_files = [f for f in os.listdir(self.config.key_store_path) if f.endswith('.key')]
            
            for key_file in key_files:
                key_path = os.path.join(self.config.key_store_path, key_file)
                try:
                    with open(key_path, 'rb') as f:
                        key_data = f.read()
                    
                    # Try to deserialize the key
                    try:
                        key_dict = json.loads(key_data.decode('utf-8'))
                        key = EncryptionKey(
                            key_id=key_dict['key_id'],
                            name=key_dict['name'],
                            algorithm=EncryptionAlgorithm(key_dict['algorithm']),
                            key_data=base64.b64decode(key_dict['key_data'].encode('utf-8')),
                            is_active=key_dict.get('is_active', True),
                            created_at=datetime.fromisoformat(key_dict['created_at']),
                            expires_at=datetime.fromisoformat(key_dict['expires_at']) if key_dict.get('expires_at') else None,
                            metadata=key_dict.get('metadata', {})
                        )
                        
                        # Add to keys dictionary
                        self._encryption_keys[key.key_id] = key
                        
                        # Initialize encryptor for Fernet keys
                        if key.algorithm == EncryptionAlgorithm.FERNET:
                            self._fernet_encryptors[key.key_id] = Fernet(key.key_data)
                        elif key.algorithm == EncryptionAlgorithm.RSA_2048:
                            # Load RSA key
                            private_key = serialization.load_pem_private_key(
                                key.key_data,
                                password=None,
                                backend=default_backend()
                            )
                            if isinstance(private_key, rsa.RSAPrivateKey):
                                self._rsa_private_keys[key.key_id] = private_key
                                self._rsa_public_keys[key.key_id] = private_key.public_key()
                    except json.JSONDecodeError:
                        # Handle raw key files (legacy)
                        key_id = os.path.splitext(key_file)[0]
                        key = EncryptionKey(
                            key_id=key_id,
                            name=f"Legacy Key {key_id}",
                            algorithm=EncryptionAlgorithm.FERNET,
                            key_data=key_data,
                            is_active=True,
                            created_at=datetime.utcnow()
                        )
                        
                        # Add to keys dictionary
                        self._encryption_keys[key.key_id] = key
                        
                        # Initialize encryptor for Fernet keys
                        self._fernet_encryptors[key.key_id] = Fernet(key.key_data)
                except Exception as e:
                    logger.warning(f"Failed to load key {key_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to load existing keys: {e}")
    
    async def _load_default_policies(self) -> None:
        """Load default data protection policies."""
        default_policies = [
            DataProtectionPolicy(
                policy_id="public_data_policy",
                name="Public Data Policy",
                description="Policy for public data",
                sensitivity_levels=[DataSensitivity.PUBLIC],
                encryption_required=False,
                masking_required=False,
                retention_policy=RetentionPolicy.PERMANENT
            ),
            DataProtectionPolicy(
                policy_id="internal_data_policy",
                name="Internal Data Policy",
                description="Policy for internal data",
                sensitivity_levels=[DataSensitivity.INTERNAL],
                encryption_required=True,
                masking_required=False,
                retention_policy=RetentionPolicy.LONG_TERM
            ),
            DataProtectionPolicy(
                policy_id="confidential_data_policy",
                name="Confidential Data Policy",
                description="Policy for confidential data",
                sensitivity_levels=[DataSensitivity.CONFIDENTIAL],
                encryption_required=True,
                masking_required=True,
                retention_policy=RetentionPolicy.MEDIUM_TERM
            ),
            DataProtectionPolicy(
                policy_id="restricted_data_policy",
                name="Restricted Data Policy",
                description="Policy for restricted data",
                sensitivity_levels=[DataSensitivity.RESTRICTED],
                encryption_required=True,
                masking_required=True,
                retention_policy=RetentionPolicy.SHORT_TERM
            ),
            DataProtectionPolicy(
                policy_id="highly_restricted_data_policy",
                name="Highly Restricted Data Policy",
                description="Policy for highly restricted data",
                sensitivity_levels=[DataSensitivity.HIGHLY_RESTRICTED],
                encryption_required=True,
                masking_required=True,
                retention_policy=RetentionPolicy.IMMEDIATE
            )
        ]
        
        for policy in default_policies:
            self._protection_policies[policy.policy_id] = policy
    
    async def _generate_default_key(self) -> None:
        """Generate a default encryption key."""
        key_id = "default_key"
        key_name = "Default Encryption Key"
        
        # Generate Fernet key
        key_data = Fernet.generate_key()
        
        # Create encryption key
        key = EncryptionKey(
            key_id=key_id,
            name=key_name,
            algorithm=EncryptionAlgorithm.FERNET,
            key_data=key_data,
            is_active=True
        )
        
        # Add to keys dictionary
        self._encryption_keys[key_id] = key
        
        # Initialize encryptor
        self._fernet_encryptors[key_id] = Fernet(key_data)
        
        # Save key to disk
        await self._save_key(key)
        
        logger.info(f"Generated default encryption key: {key_id}")
    
    async def _save_key(self, key: EncryptionKey) -> bool:
        """
        Save an encryption key to disk.
        
        Args:
            key: Encryption key to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            key_path = os.path.join(self.config.key_store_path, f"{key.key_id}.key")
            
            # Serialize key data
            key_dict = {
                'key_id': key.key_id,
                'name': key.name,
                'algorithm': key.algorithm.value,
                'key_data': base64.b64encode(key.key_data).decode('utf-8'),
                'is_active': key.is_active,
                'created_at': key.created_at.isoformat(),
                'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                'metadata': key.metadata
            }
            
            # Write to file
            with open(key_path, 'w') as f:
                json.dump(key_dict, f)
            
            # Set file permissions to be readable only by owner
            os.chmod(key_path, 0o600)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save key {key.key_id}: {e}")
            return False
    
    async def generate_key(
        self,
        key_id: str,
        name: str,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET,
        expires_in_days: Optional[int] = None
    ) -> Optional[EncryptionKey]:
        """
        Generate a new encryption key.
        
        Args:
            key_id: ID for the new key
            name: Name for the new key
            algorithm: Encryption algorithm to use
            expires_in_days: Number of days until the key expires
            
        Returns:
            New encryption key if generation was successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if key already exists
            if key_id in self._encryption_keys:
                logger.warning(f"Key {key_id} already exists")
                return None
            
            # Generate key based on algorithm
            private_key = None
            if algorithm == EncryptionAlgorithm.FERNET:
                key_data = Fernet.generate_key()
            elif algorithm == EncryptionAlgorithm.RSA_2048:
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                key_data = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            elif algorithm == EncryptionAlgorithm.AES_256:
                # Generate a random key for AES-256
                key_data = os.urandom(32)  # 256 bits
            else:
                logger.error(f"Unsupported encryption algorithm: {algorithm}")
                return None
            
            # Calculate expiration date
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Create encryption key
            key = EncryptionKey(
                key_id=key_id,
                name=name,
                algorithm=algorithm,
                key_data=key_data,
                is_active=True,
                expires_at=expires_at
            )
            
            # Add to keys dictionary
            self._encryption_keys[key_id] = key
            
            # Initialize encryptor
            if algorithm == EncryptionAlgorithm.FERNET:
                self._fernet_encryptors[key_id] = Fernet(key_data)
            elif algorithm == EncryptionAlgorithm.RSA_2048 and private_key is not None:
                self._rsa_private_keys[key_id] = private_key
                self._rsa_public_keys[key_id] = private_key.public_key()
            
            # Save key to disk
            await self._save_key(key)
            
            logger.info(f"Generated encryption key: {key_id}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to generate key {key_id}: {e}")
            return None
    
    async def get_key(self, key_id: str) -> Optional[EncryptionKey]:
        """
        Get an encryption key.
        
        Args:
            key_id: ID of the key to get
            
        Returns:
            Encryption key if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._encryption_keys.get(key_id)
    
    async def get_keys(self, algorithm: Optional[EncryptionAlgorithm] = None) -> List[EncryptionKey]:
        """
        Get encryption keys.
        
        Args:
            algorithm: Optional algorithm to filter by
            
        Returns:
            List of encryption keys
        """
        if not self._initialized:
            await self.initialize()
        
        keys = list(self._encryption_keys.values())
        if algorithm:
            keys = [k for k in keys if k.algorithm == algorithm]
        
        return keys
    
    async def remove_key(self, key_id: str) -> bool:
        """
        Remove an encryption key.
        
        Args:
            key_id: ID of the key to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if key_id in self._encryption_keys:
                # Remove from dictionaries
                del self._encryption_keys[key_id]
                if key_id in self._fernet_encryptors:
                    del self._fernet_encryptors[key_id]
                if key_id in self._rsa_private_keys:
                    del self._rsa_private_keys[key_id]
                if key_id in self._rsa_public_keys:
                    del self._rsa_public_keys[key_id]
                
                # Remove key file
                key_path = os.path.join(self.config.key_store_path, f"{key_id}.key")
                if os.path.exists(key_path):
                    if self.config.secure_erase:
                        # Securely erase the file
                        with open(key_path, 'wb') as f:
                            f.write(os.urandom(os.path.getsize(key_path)))
                    os.remove(key_path)
                
                logger.info(f"Removed encryption key: {key_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove key {key_id}: {e}")
            return False
    
    async def encrypt_data(
        self,
        data: Union[str, bytes, Dict[str, Any]],
        key_id: str = "default_key",
        policy_id: Optional[str] = None
    ) -> Optional[DataProtectionResult]:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            key_id: ID of the encryption key to use
            policy_id: Optional ID of the protection policy to apply
            
        Returns:
            Data protection result if encryption was successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_encryption:
            return DataProtectionResult(
                is_protected=False,
                protection_type="none",
                data=data
            )
        
        try:
            # Get encryption key
            key = self._encryption_keys.get(key_id)
            if not key:
                logger.error(f"Encryption key not found: {key_id}")
                return None
            
            # Check if key is expired
            if key.expires_at and key.expires_at < datetime.utcnow():
                logger.error(f"Encryption key expired: {key_id}")
                return None
            
            # Convert data to bytes if it's a string or dict
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            elif isinstance(data, bytes):
                data_bytes = data
            else:
                logger.error(f"Unsupported data type: {type(data)}")
                return None
            
            # Encrypt data based on algorithm
            if key.algorithm == EncryptionAlgorithm.FERNET:
                if key_id not in self._fernet_encryptors:
                    logger.error(f"Fernet encryptor not found: {key_id}")
                    return None
                
                encrypted_data = self._fernet_encryptors[key_id].encrypt(data_bytes)
            elif key.algorithm == EncryptionAlgorithm.RSA_2048:
                if key_id not in self._rsa_public_keys:
                    logger.error(f"RSA public key not found: {key_id}")
                    return None
                
                # RSA can only encrypt small amounts of data
                # For larger data, we would use hybrid encryption
                if len(data_bytes) > 190:  # RSA 2048 can encrypt 190 bytes
                    logger.error("Data too large for RSA encryption")
                    return None
                
                encrypted_data = self._rsa_public_keys[key_id].encrypt(
                    data_bytes,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            elif key.algorithm == EncryptionAlgorithm.AES_256:
                # For AES-256, we would need to implement AES encryption
                # For now, we'll just use Fernet
                logger.error("AES-256 encryption not implemented yet")
                return None
            else:
                logger.error(f"Unsupported encryption algorithm: {key.algorithm}")
                return None
            
            return DataProtectionResult(
                is_protected=True,
                protection_type="encryption",
                data=encrypted_data,
                key_id=key_id,
                policy_id=policy_id
            )
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return None
    
    async def decrypt_data(
        self,
        encrypted_data: bytes,
        key_id: str = "default_key"
    ) -> Optional[Union[str, bytes, Dict[str, Any]]]:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            key_id: ID of the encryption key to use
            
        Returns:
            Decrypted data if decryption was successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_encryption:
            return encrypted_data
        
        try:
            # Get encryption key
            key = self._encryption_keys.get(key_id)
            if not key:
                logger.error(f"Encryption key not found: {key_id}")
                return None
            
            # Check if key is expired
            if key.expires_at and key.expires_at < datetime.utcnow():
                logger.error(f"Encryption key expired: {key_id}")
                return None
            
            # Decrypt data based on algorithm
            if key.algorithm == EncryptionAlgorithm.FERNET:
                if key_id not in self._fernet_encryptors:
                    logger.error(f"Fernet encryptor not found: {key_id}")
                    return None
                
                decrypted_data = self._fernet_encryptors[key_id].decrypt(encrypted_data)
            elif key.algorithm == EncryptionAlgorithm.RSA_2048:
                if key_id not in self._rsa_private_keys:
                    logger.error(f"RSA private key not found: {key_id}")
                    return None
                
                decrypted_data = self._rsa_private_keys[key_id].decrypt(
                    encrypted_data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            elif key.algorithm == EncryptionAlgorithm.AES_256:
                # For AES-256, we would need to implement AES decryption
                # For now, we'll just return None
                logger.error("AES-256 decryption not implemented yet")
                return None
            else:
                logger.error(f"Unsupported encryption algorithm: {key.algorithm}")
                return None
            
            # Try to decode as JSON first, then as UTF-8 string
            try:
                return json.loads(decrypted_data.decode('utf-8'))
            except json.JSONDecodeError:
                try:
                    return decrypted_data.decode('utf-8')
                except UnicodeDecodeError:
                    return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return None
    
    async def mask_data(
        self,
        data: Union[str, Dict[str, Any]],
        mask_char: str = "*",
        policy_id: Optional[str] = None
    ) -> Optional[DataProtectionResult]:
        """
        Mask sensitive data.
        
        Args:
            data: Data to mask
            mask_char: Character to use for masking
            policy_id: Optional ID of the protection policy to apply
            
        Returns:
            Data protection result if masking was successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_data_masking:
            return DataProtectionResult(
                is_protected=False,
                protection_type="none",
                data=data
            )
        
        try:
            # Get policy if specified
            policy = None
            if policy_id:
                policy = self._protection_policies.get(policy_id)
            
            # Mask data based on type
            if isinstance(data, str):
                # Mask email addresses
                if '@' in data:
                    local, domain = data.split('@', 1)
                    if len(local) > 2:
                        masked_local = local[0] + mask_char * (len(local) - 2) + local[-1]
                        masked_data = masked_local + '@' + domain
                    else:
                        masked_data = mask_char * len(local) + '@' + domain
                # Mask phone numbers
                elif data.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
                    digits = ''.join(c for c in data if c.isdigit())
                    if len(digits) >= 4:
                        masked_digits = digits[:-4] + mask_char * 4
                        masked_data = data
                        for i, c in enumerate(data):
                            if c.isdigit():
                                masked_data = masked_data[:i] + (mask_char if i < len(data) - 4 else digits[-(len(data) - i)]) + masked_data[i+1:]
                    else:
                        masked_data = mask_char * len(data)
                # Mask credit card numbers
                elif data.replace(' ', '').replace('-', '').isdigit() and 13 <= len(data.replace(' ', '').replace('-', '')) <= 19:
                    digits = ''.join(c for c in data if c.isdigit())
                    masked_digits = mask_char * (len(digits) - 4) + digits[-4:]
                    masked_data = data
                    digit_index = 0
                    for i, c in enumerate(data):
                        if c.isdigit():
                            if digit_index < len(digits) - 4:
                                masked_data = masked_data[:i] + mask_char + masked_data[i+1:]
                            digit_index += 1
                # Mask other strings
                else:
                    if len(data) > 2:
                        masked_data = data[0] + mask_char * (len(data) - 2) + data[-1]
                    else:
                        masked_data = mask_char * len(data)
            elif isinstance(data, dict):
                # Mask dictionary values
                masked_data = {}
                for key, value in data.items():
                    # Mask sensitive keys
                    if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token', 'key', 'ssn']):
                        if isinstance(value, str):
                            masked_data[key] = mask_char * len(value)
                        else:
                            masked_data[key] = value
                    else:
                        masked_data[key] = value
            else:
                logger.error(f"Unsupported data type for masking: {type(data)}")
                return None
            
            return DataProtectionResult(
                is_protected=True,
                protection_type="masking",
                data=masked_data,
                policy_id=policy_id
            )
            
        except Exception as e:
            logger.error(f"Failed to mask data: {e}")
            return None
    
    async def anonymize_data(
        self,
        data: Union[str, Dict[str, Any]],
        policy_id: Optional[str] = None
    ) -> Optional[DataProtectionResult]:
        """
        Anonymize data by removing or replacing personally identifiable information.
        
        Args:
            data: Data to anonymize
            policy_id: Optional ID of the protection policy to apply
            
        Returns:
            Data protection result if anonymization was successful, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_anonymization:
            return DataProtectionResult(
                is_protected=False,
                protection_type="none",
                data=data
            )
        
        try:
            # Get policy if specified
            policy = None
            if policy_id:
                policy = self._protection_policies.get(policy_id)
            
            # Anonymize data based on type
            if isinstance(data, str):
                # Generate a hash of the data to use as an identifier
                data_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]
                anonymized_data = f"anon_{data_hash}"
            elif isinstance(data, dict):
                # Anonymize dictionary values
                anonymized_data = {}
                for key, value in data.items():
                    # Anonymize PII keys
                    if any(pii in key.lower() for pii in ['name', 'email', 'phone', 'address', 'ssn', 'id']):
                        if isinstance(value, str):
                            value_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]
                            anonymized_data[key] = f"anon_{value_hash}"
                        else:
                            anonymized_data[key] = value
                    else:
                        anonymized_data[key] = value
            else:
                logger.error(f"Unsupported data type for anonymization: {type(data)}")
                return None
            
            return DataProtectionResult(
                is_protected=True,
                protection_type="anonymization",
                data=anonymized_data,
                policy_id=policy_id
            )
            
        except Exception as e:
            logger.error(f"Failed to anonymize data: {e}")
            return None
    
    async def apply_retention_policy(
        self,
        data_id: str,
        policy_id: str,
        created_at: Optional[datetime] = None
    ) -> bool:
        """
        Apply retention policy to data.
        
        Args:
            data_id: ID of the data to apply policy to
            policy_id: ID of the retention policy to apply
            created_at: Optional creation time of the data
            
        Returns:
            True if data should be kept, False if it should be deleted
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.config.enable_retention_policies:
            return True
        
        try:
            # Get policy
            policy = self._protection_policies.get(policy_id)
            if not policy:
                logger.error(f"Retention policy not found: {policy_id}")
                return True
            
            # Use current time if creation time not provided
            if not created_at:
                created_at = datetime.utcnow()
            
            # Check if data should be deleted based on retention policy
            if policy.retention_policy == RetentionPolicy.IMMEDIATE:
                return False
            elif policy.retention_policy == RetentionPolicy.SHORT_TERM:
                retention_days = 30
            elif policy.retention_policy == RetentionPolicy.MEDIUM_TERM:
                retention_days = 90
            elif policy.retention_policy == RetentionPolicy.LONG_TERM:
                retention_days = 365
            elif policy.retention_policy == RetentionPolicy.PERMANENT:
                return True
            else:
                logger.error(f"Unknown retention policy: {policy.retention_policy}")
                return True
            
            # Check if data has expired
            expiration_time = created_at + timedelta(days=retention_days)
            if datetime.utcnow() > expiration_time:
                logger.info(f"Data {data_id} has expired based on retention policy {policy_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}")
            return True
    
    async def add_policy(self, policy: DataProtectionPolicy) -> bool:
        """
        Add a new data protection policy.
        
        Args:
            policy: Policy to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            self._protection_policies[policy.policy_id] = policy
            logger.info(f"Added data protection policy: {policy.name} ({policy.policy_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add policy {policy.policy_id}: {e}")
            return False
    
    async def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a data protection policy.
        
        Args:
            policy_id: ID of the policy to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if policy_id in self._protection_policies:
                del self._protection_policies[policy_id]
                logger.info(f"Removed data protection policy: {policy_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove policy {policy_id}: {e}")
            return False
    
    async def get_policy(self, policy_id: str) -> Optional[DataProtectionPolicy]:
        """
        Get a data protection policy.
        
        Args:
            policy_id: ID of the policy to get
            
        Returns:
            Policy if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._protection_policies.get(policy_id)
    
    async def get_policies(self, sensitivity_level: Optional[DataSensitivity] = None) -> List[DataProtectionPolicy]:
        """
        Get data protection policies.
        
        Args:
            sensitivity_level: Optional sensitivity level to filter by
            
        Returns:
            List of policies
        """
        if not self._initialized:
            await self.initialize()
        
        policies = list(self._protection_policies.values())
        if sensitivity_level:
            policies = [p for p in policies if sensitivity_level in p.sensitivity_levels]
        
        return policies
    
    async def rotate_keys(self) -> bool:
        """
        Rotate encryption keys that are due for rotation.
        
        Returns:
            True if rotation was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            rotation_count = 0
            current_time = datetime.utcnow()
            
            # Find keys that need rotation
            keys_to_rotate = []
            for key_id, key in self._encryption_keys.items():
                if not key.is_active:
                    continue
                
                # Check if key is due for rotation
                rotation_time = key.created_at + timedelta(days=self.config.key_rotation_days)
                if current_time > rotation_time:
                    keys_to_rotate.append(key)
            
            # Rotate each key
            for key in keys_to_rotate:
                # Generate new key
                new_key_id = f"{key.key_id}_rotated_{int(current_time.timestamp())}"
                new_key = await self.generate_key(
                    key_id=new_key_id,
                    name=f"{key.name} (Rotated)",
                    algorithm=key.algorithm,
                    expires_in_days=self.config.key_rotation_days
                )
                
                if new_key:
                    # Deactivate old key
                    key.is_active = False
                    await self._save_key(key)
                    rotation_count += 1
            
            logger.info(f"Rotated {rotation_count} encryption keys")
            return rotation_count > 0
            
        except Exception as e:
            logger.error(f"Failed to rotate keys: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the data protection service.
        
        Returns:
            Dictionary with data protection service statistics
        """
        if not self._initialized:
            await self.initialize()
        
        # Count keys by algorithm
        keys_by_algorithm = {}
        for key in self._encryption_keys.values():
            algorithm = key.algorithm.value
            if algorithm not in keys_by_algorithm:
                keys_by_algorithm[algorithm] = []
            keys_by_algorithm[algorithm].append(key.key_id)
        
        # Count policies by sensitivity level
        policies_by_sensitivity = {}
        for policy in self._protection_policies.values():
            for sensitivity in policy.sensitivity_levels:
                sensitivity_level = sensitivity.value
                if sensitivity_level not in policies_by_sensitivity:
                    policies_by_sensitivity[sensitivity_level] = []
                policies_by_sensitivity[sensitivity_level].append(policy.policy_id)
        
        # Count active vs inactive keys
        active_keys = [k for k in self._encryption_keys.values() if k.is_active]
        inactive_keys = [k for k in self._encryption_keys.values() if not k.is_active]
        
        # Count expired keys
        current_time = datetime.utcnow()
        expired_keys = [k for k in self._encryption_keys.values() if k.expires_at and k.expires_at < current_time]
        
        return {
            "total_keys": len(self._encryption_keys),
            "active_keys": len(active_keys),
            "inactive_keys": len(inactive_keys),
            "expired_keys": len(expired_keys),
            "keys_by_algorithm": {
                algorithm: len(keys)
                for algorithm, keys in keys_by_algorithm.items()
            },
            "total_policies": len(self._protection_policies),
            "policies_by_sensitivity": {
                sensitivity: len(policies)
                for sensitivity, policies in policies_by_sensitivity.items()
            },
            "config": {
                "enable_encryption": self.config.enable_encryption,
                "enable_data_masking": self.config.enable_data_masking,
                "enable_anonymization": self.config.enable_anonymization,
                "enable_retention_policies": self.config.enable_retention_policies,
                "key_rotation_days": self.config.key_rotation_days,
                "data_retention_days": self.config.data_retention_days,
                "secure_erase": self.config.secure_erase,
                "compliance_mode": self.config.compliance_mode
            }
        }
    
    async def health_check(self) -> bool:
        """
        Check health of the Data Protection Service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            # Check if we can encrypt and decrypt data
            test_data = "test_data"
            encrypted_result = await self.encrypt_data(test_data)
            if not encrypted_result:
                return False
            
            decrypted_data = await self.decrypt_data(encrypted_result.data)
            if decrypted_data != test_data:
                return False
            
            # Check if we can mask data
            masked_result = await self.mask_data(test_data)
            if not masked_result:
                return False
            
            # Check if we can anonymize data
            anonymized_result = await self.anonymize_data(test_data)
            if not anonymized_result:
                return False
            
            # Check if we can apply retention policy
            keep_data = await self.apply_retention_policy(
                data_id="test_data",
                policy_id="public_data_policy"
            )
            if not isinstance(keep_data, bool):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Data Protection Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Data Protection Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Data Protection Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Data Protection Service."""
        if not self._initialized:
            return
        
        # Clear sensitive data from memory
        self._fernet_encryptors.clear()
        self._rsa_private_keys.clear()
        self._rsa_public_keys.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Data Protection Service stopped successfully")