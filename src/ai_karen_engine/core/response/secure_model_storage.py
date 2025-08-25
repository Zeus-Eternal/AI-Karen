"""
Secure Model Storage and Version Management System

This module provides secure storage, versioning, and access control for AI models
used in the Response Core orchestrator. Includes encryption, integrity verification,
and comprehensive audit logging.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
"""

import asyncio
import hashlib
import json
import logging
import shutil
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import tempfile
import zipfile
import pickle
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ai_karen_engine.auth.models import UserData
from ai_karen_engine.services.audit_logging import get_audit_logger
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class ModelType(str, Enum):
    """Types of AI models."""
    SPACY_NLP = "spacy_nlp"
    TRANSFORMER = "transformer"
    LLAMA_CPP = "llama_cpp"
    DISTILBERT = "distilbert"
    BASIC_CLASSIFIER = "basic_classifier"
    CUSTOM = "custom"


class ModelStatus(str, Enum):
    """Model status in storage."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    CORRUPTED = "corrupted"
    QUARANTINED = "quarantined"


class SecurityLevel(str, Enum):
    """Security levels for model storage."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class ModelMetadata:
    """Metadata for stored models."""
    model_id: str
    name: str
    version: str
    model_type: ModelType
    description: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    status: ModelStatus = ModelStatus.ACTIVE
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    
    # File information
    file_path: str = ""
    file_size: int = 0
    checksum: str = ""
    encrypted: bool = False
    
    # Model information
    architecture: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_data_hash: Optional[str] = None
    
    # Access control
    access_permissions: List[str] = field(default_factory=list)
    tenant_id: str = "default"
    
    # Audit trail
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    last_accessed_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data

@dataclass
class ModelVersion:
    """Version information for models."""
    version_id: str
    model_id: str
    version_number: str
    parent_version: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    description: str = ""
    changes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


class SecureModelStorage:
    """Secure storage system for AI models with encryption and access control."""
    
    def __init__(self, storage_path: str = "models/secure", encryption_key: Optional[str] = None):
        """Initialize secure model storage."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.encryption_key = encryption_key or os.environ.get("MODEL_ENCRYPTION_KEY")
        if self.encryption_key:
            self.cipher = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        else:
            self.cipher = None
            logger.warning("No encryption key provided - models will be stored unencrypted")
        
        # Initialize metadata storage
        self.metadata_file = self.storage_path / "metadata.json"
        self.versions_file = self.storage_path / "versions.json"
        
        # Load existing metadata
        self.models_metadata: Dict[str, ModelMetadata] = {}
        self.versions_metadata: Dict[str, List[ModelVersion]] = {}
        self._load_metadata()
        
        # Initialize audit logger
        self.audit_logger = get_audit_logger()
    
    def _generate_encryption_key(self, password: str, salt: bytes) -> bytes:
        """Generate encryption key from password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _encrypt_file(self, file_path: Path, output_path: Path) -> bool:
        """Encrypt a file using Fernet encryption."""
        if not self.cipher:
            return False
        
        try:
            with open(file_path, 'rb') as infile:
                data = infile.read()
            
            encrypted_data = self.cipher.encrypt(data)
            
            with open(output_path, 'wb') as outfile:
                outfile.write(encrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to encrypt file {file_path}: {e}")
            return False
    
    def _decrypt_file(self, encrypted_path: Path, output_path: Path) -> bool:
        """Decrypt a file using Fernet encryption."""
        if not self.cipher:
            return False
        
        try:
            with open(encrypted_path, 'rb') as infile:
                encrypted_data = infile.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as outfile:
                outfile.write(decrypted_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to decrypt file {encrypted_path}: {e}")
            return False
    
    def _load_metadata(self) -> None:
        """Load metadata from storage."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    for model_id, metadata_dict in data.items():
                        # Convert datetime strings back to datetime objects
                        metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
                        metadata_dict['updated_at'] = datetime.fromisoformat(metadata_dict['updated_at'])
                        if metadata_dict.get('last_accessed'):
                            metadata_dict['last_accessed'] = datetime.fromisoformat(metadata_dict['last_accessed'])
                        
                        self.models_metadata[model_id] = ModelMetadata(**metadata_dict)
            
            if self.versions_file.exists():
                with open(self.versions_file, 'r') as f:
                    data = json.load(f)
                    for model_id, versions_list in data.items():
                        versions = []
                        for version_dict in versions_list:
                            version_dict['created_at'] = datetime.fromisoformat(version_dict['created_at'])
                            versions.append(ModelVersion(**version_dict))
                        self.versions_metadata[model_id] = versions
                        
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save metadata to storage."""
        try:
            # Save models metadata
            models_data = {
                model_id: metadata.to_dict()
                for model_id, metadata in self.models_metadata.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(models_data, f, indent=2)
            
            # Save versions metadata
            versions_data = {
                model_id: [version.to_dict() for version in versions]
                for model_id, versions in self.versions_metadata.items()
            }
            with open(self.versions_file, 'w') as f:
                json.dump(versions_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    async def store_model(
        self,
        model_path: Path,
        name: str,
        model_type: ModelType,
        description: str,
        user: UserData,
        version: str = "1.0.0",
        security_level: SecurityLevel = SecurityLevel.INTERNAL,
        encrypt: bool = True,
        parameters: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, float]] = None
    ) -> str:
        """Store a model securely with metadata and versioning."""
        try:
            model_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)
            
            # Create model directory
            model_dir = self.storage_path / model_id
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine storage filename
            original_name = model_path.name
            stored_filename = f"{model_id}_{original_name}"
            stored_path = model_dir / stored_filename
            
            # Calculate checksum before encryption
            original_checksum = self._calculate_checksum(model_path)
            
            # Store model file (encrypted if requested and available)
            encrypted = False
            if encrypt and self.cipher and security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
                encrypted_path = model_dir / f"{stored_filename}.enc"
                if self._encrypt_file(model_path, encrypted_path):
                    stored_path = encrypted_path
                    encrypted = True
                else:
                    # Fall back to unencrypted storage
                    shutil.copy2(model_path, stored_path)
            else:
                shutil.copy2(model_path, stored_path)
            
            # Create metadata
            metadata = ModelMetadata(
                model_id=model_id,
                name=name,
                version=version,
                model_type=model_type,
                description=description,
                created_at=timestamp,
                created_by=user.user_id,
                updated_at=timestamp,
                updated_by=user.user_id,
                security_level=security_level,
                file_path=str(stored_path),
                file_size=stored_path.stat().st_size,
                checksum=original_checksum,
                encrypted=encrypted,
                parameters=parameters or {},
                performance_metrics=performance_metrics or {},
                tenant_id=user.tenant_id
            )
            
            # Store metadata
            self.models_metadata[model_id] = metadata
            
            # Create version record
            version_record = ModelVersion(
                version_id=str(uuid.uuid4()),
                model_id=model_id,
                version_number=version,
                created_at=timestamp,
                created_by=user.user_id,
                description=f"Initial version: {description}"
            )
            
            if model_id not in self.versions_metadata:
                self.versions_metadata[model_id] = []
            self.versions_metadata[model_id].append(version_record)
            
            # Save metadata
            self._save_metadata()
            
            # Audit log
            self.audit_logger.log_audit_event({
                "event_type": "model_stored",
                "severity": "info",
                "message": f"Model {name} stored securely",
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "metadata": {
                    "model_id": model_id,
                    "model_name": name,
                    "model_type": model_type.value,
                    "version": version,
                    "encrypted": encrypted,
                    "security_level": security_level.value,
                    "file_size": metadata.file_size
                }
            })
            
            logger.info(f"Model {name} stored successfully with ID {model_id}")
            return model_id
            
        except Exception as e:
            logger.error(f"Failed to store model {name}: {e}")
            raise
    
    async def retrieve_model(
        self,
        model_id: str,
        user: UserData,
        output_path: Optional[Path] = None
    ) -> Path:
        """Retrieve a model from secure storage."""
        try:
            # Check if model exists
            if model_id not in self.models_metadata:
                raise ValueError(f"Model {model_id} not found")
            
            metadata = self.models_metadata[model_id]
            
            # Check access permissions (basic tenant isolation)
            if metadata.tenant_id != user.tenant_id and not user.has_role("admin"):
                raise PermissionError(f"Access denied to model {model_id}")
            
            # Check if model file exists
            stored_path = Path(metadata.file_path)
            if not stored_path.exists():
                raise FileNotFoundError(f"Model file not found: {stored_path}")
            
            # Determine output path
            if output_path is None:
                output_path = Path(tempfile.mkdtemp()) / f"model_{model_id}"
            
            # Decrypt if necessary
            if metadata.encrypted:
                if not self.cipher:
                    raise RuntimeError("Model is encrypted but no decryption key available")
                
                if not self._decrypt_file(stored_path, output_path):
                    raise RuntimeError("Failed to decrypt model file")
            else:
                shutil.copy2(stored_path, output_path)
            
            # Verify integrity
            retrieved_checksum = self._calculate_checksum(output_path)
            if retrieved_checksum != metadata.checksum:
                logger.error(f"Checksum mismatch for model {model_id}")
                raise RuntimeError("Model integrity check failed")
            
            # Update access tracking
            metadata.access_count += 1
            metadata.last_accessed = datetime.now(timezone.utc)
            metadata.last_accessed_by = user.user_id
            self._save_metadata()
            
            # Audit log
            self.audit_logger.log_audit_event({
                "event_type": "model_retrieved",
                "severity": "info",
                "message": f"Model {metadata.name} retrieved",
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "metadata": {
                    "model_id": model_id,
                    "model_name": metadata.name,
                    "access_count": metadata.access_count
                }
            })
            
            logger.info(f"Model {model_id} retrieved successfully")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to retrieve model {model_id}: {e}")
            raise
    
    async def delete_model(self, model_id: str, user: UserData) -> bool:
        """Delete a model from secure storage."""
        try:
            # Check if model exists
            if model_id not in self.models_metadata:
                raise ValueError(f"Model {model_id} not found")
            
            metadata = self.models_metadata[model_id]
            
            # Check permissions (only admin or creator can delete)
            if metadata.created_by != user.user_id and not user.has_role("admin"):
                raise PermissionError(f"Access denied to delete model {model_id}")
            
            # Remove model file
            stored_path = Path(metadata.file_path)
            if stored_path.exists():
                stored_path.unlink()
            
            # Remove model directory if empty
            model_dir = stored_path.parent
            try:
                model_dir.rmdir()
            except OSError:
                pass  # Directory not empty
            
            # Remove metadata
            del self.models_metadata[model_id]
            if model_id in self.versions_metadata:
                del self.versions_metadata[model_id]
            
            # Save metadata
            self._save_metadata()
            
            # Audit log
            self.audit_logger.log_audit_event({
                "event_type": "model_deleted",
                "severity": "warning",
                "message": f"Model {metadata.name} deleted",
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "metadata": {
                    "model_id": model_id,
                    "model_name": metadata.name,
                    "deleted_by": user.user_id
                }
            })
            
            logger.info(f"Model {model_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_id}: {e}")
            raise
    
    def list_models(
        self,
        user: UserData,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None
    ) -> List[ModelMetadata]:
        """List models accessible to the user."""
        try:
            models = []
            
            for model_id, metadata in self.models_metadata.items():
                # Check tenant access
                if metadata.tenant_id != user.tenant_id and not user.has_role("admin"):
                    continue
                
                # Apply filters
                if model_type and metadata.model_type != model_type:
                    continue
                
                if status and metadata.status != status:
                    continue
                
                models.append(metadata)
            
            return sorted(models, key=lambda m: m.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def get_model_metadata(self, model_id: str, user: UserData) -> Optional[ModelMetadata]:
        """Get metadata for a specific model."""
        try:
            if model_id not in self.models_metadata:
                return None
            
            metadata = self.models_metadata[model_id]
            
            # Check access permissions
            if metadata.tenant_id != user.tenant_id and not user.has_role("admin"):
                return None
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get model metadata {model_id}: {e}")
            return None
    
    def get_model_versions(self, model_id: str, user: UserData) -> List[ModelVersion]:
        """Get version history for a model."""
        try:
            if model_id not in self.models_metadata:
                return []
            
            metadata = self.models_metadata[model_id]
            
            # Check access permissions
            if metadata.tenant_id != user.tenant_id and not user.has_role("admin"):
                return []
            
            return self.versions_metadata.get(model_id, [])
            
        except Exception as e:
            logger.error(f"Failed to get model versions {model_id}: {e}")
            return []


# Global secure model storage instance
_secure_storage: Optional[SecureModelStorage] = None


def get_secure_model_storage() -> SecureModelStorage:
    """Get or create global secure model storage instance."""
    global _secure_storage
    if _secure_storage is None:
        _secure_storage = SecureModelStorage()
    return _secure_storage