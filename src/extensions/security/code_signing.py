"""
Extension code signing and verification system
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from sqlalchemy.orm import Session

from .models import ExtensionSignature, ExtensionSignatureCreate, ExtensionSignatureResponse
from ..base.exceptions import ExtensionSecurityError


class ExtensionCodeSigner:
    """Handles extension code signing operations"""
    
    def __init__(self, private_key_path: Optional[str] = None, key_id: Optional[str] = None):
        self.private_key_path = private_key_path
        self.key_id = key_id or "default"
        self._private_key = None
        
    def _load_private_key(self, password: Optional[bytes] = None) -> rsa.RSAPrivateKey:
        """Load private key for signing"""
        if self._private_key is None:
            if not self.private_key_path or not os.path.exists(self.private_key_path):
                raise ExtensionSecurityError("Private key not found for signing")
                
            with open(self.private_key_path, 'rb') as key_file:
                self._private_key = load_pem_private_key(
                    key_file.read(),
                    password=password
                )
        return self._private_key
    
    def _calculate_extension_hash(self, extension_path: Path) -> str:
        """Calculate hash of extension files"""
        hasher = hashlib.sha256()
        
        # Get all files in extension directory
        files_to_hash = []
        for root, dirs, files in os.walk(extension_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    files_to_hash.append(os.path.join(root, file))
        
        # Sort files for consistent hashing
        files_to_hash.sort()
        
        # Hash each file's content
        for file_path in files_to_hash:
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                # Also hash the relative path for integrity
                rel_path = os.path.relpath(file_path, extension_path)
                hasher.update(rel_path.encode('utf-8'))
            except (IOError, OSError) as e:
                raise ExtensionSecurityError(f"Error reading file {file_path}: {e}")
        
        return hasher.hexdigest()
    
    def sign_extension(
        self, 
        extension_path: Path, 
        extension_name: str,
        extension_version: str,
        signer_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Sign an extension and return signature hash"""
        try:
            # Calculate extension hash
            extension_hash = self._calculate_extension_hash(extension_path)
            
            # Load private key
            private_key = self._load_private_key()
            
            # Create signature payload
            signature_data = {
                'extension_name': extension_name,
                'extension_version': extension_version,
                'extension_hash': extension_hash,
                'key_id': self.key_id,
                'signed_at': datetime.utcnow().isoformat(),
                'signer_id': signer_id,
                'metadata': metadata or {}
            }
            
            # Sign the payload
            payload_bytes = json.dumps(signature_data, sort_keys=True).encode('utf-8')
            signature = private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Create signature hash
            signature_hash = hashlib.sha256(signature).hexdigest()
            
            # Store signature file
            signature_file = extension_path / '.signature'
            with open(signature_file, 'w') as f:
                json.dump({
                    'signature_data': signature_data,
                    'signature': signature.hex(),
                    'signature_hash': signature_hash
                }, f, indent=2)
            
            return signature_hash
            
        except Exception as e:
            raise ExtensionSecurityError(f"Failed to sign extension: {e}")
    
    def generate_key_pair(self, output_dir: Path, key_id: str) -> Tuple[str, str]:
        """Generate a new RSA key pair for signing"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serialize public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Save keys
            private_key_path = output_dir / f"{key_id}_private.pem"
            public_key_path = output_dir / f"{key_id}_public.pem"
            
            with open(private_key_path, 'wb') as f:
                f.write(private_pem)
            
            with open(public_key_path, 'wb') as f:
                f.write(public_pem)
            
            # Set secure permissions
            os.chmod(private_key_path, 0o600)
            os.chmod(public_key_path, 0o644)
            
            return str(private_key_path), str(public_key_path)
            
        except Exception as e:
            raise ExtensionSecurityError(f"Failed to generate key pair: {e}")


class ExtensionVerifier:
    """Handles extension signature verification"""
    
    def __init__(self, public_keys_dir: Path):
        self.public_keys_dir = public_keys_dir
        self._public_keys = {}
    
    def _load_public_key(self, key_id: str) -> rsa.RSAPublicKey:
        """Load public key for verification"""
        if key_id not in self._public_keys:
            key_path = self.public_keys_dir / f"{key_id}_public.pem"
            if not key_path.exists():
                raise ExtensionSecurityError(f"Public key not found: {key_id}")
            
            with open(key_path, 'rb') as key_file:
                self._public_keys[key_id] = load_pem_public_key(key_file.read())
        
        return self._public_keys[key_id]
    
    def verify_extension(self, extension_path: Path) -> Tuple[bool, Dict[str, Any]]:
        """Verify extension signature"""
        try:
            signature_file = extension_path / '.signature'
            if not signature_file.exists():
                return False, {'error': 'No signature file found'}
            
            # Load signature data
            with open(signature_file, 'r') as f:
                signature_info = json.load(f)
            
            signature_data = signature_info['signature_data']
            signature_bytes = bytes.fromhex(signature_info['signature'])
            
            # Load public key
            key_id = signature_data['key_id']
            public_key = self._load_public_key(key_id)
            
            # Verify signature
            payload_bytes = json.dumps(signature_data, sort_keys=True).encode('utf-8')
            
            try:
                public_key.verify(
                    signature_bytes,
                    payload_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                signature_valid = True
            except Exception:
                signature_valid = False
            
            # Verify extension hash
            current_hash = self._calculate_extension_hash(extension_path)
            hash_valid = current_hash == signature_data['extension_hash']
            
            verification_result = {
                'signature_valid': signature_valid,
                'hash_valid': hash_valid,
                'overall_valid': signature_valid and hash_valid,
                'signature_data': signature_data,
                'current_hash': current_hash,
                'signed_hash': signature_data['extension_hash']
            }
            
            return verification_result['overall_valid'], verification_result
            
        except Exception as e:
            return False, {'error': f'Verification failed: {e}'}
    
    def _calculate_extension_hash(self, extension_path: Path) -> str:
        """Calculate hash of extension files (same as signer)"""
        hasher = hashlib.sha256()
        
        files_to_hash = []
        for root, dirs, files in os.walk(extension_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if not file.startswith('.') and not file.endswith('.pyc'):
                    files_to_hash.append(os.path.join(root, file))
        
        files_to_hash.sort()
        
        for file_path in files_to_hash:
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                rel_path = os.path.relpath(file_path, extension_path)
                hasher.update(rel_path.encode('utf-8'))
            except (IOError, OSError):
                continue  # Skip files that can't be read
        
        return hasher.hexdigest()
    
    def batch_verify_extensions(self, extensions_dir: Path) -> Dict[str, Dict[str, Any]]:
        """Verify multiple extensions in batch"""
        results = {}
        
        for extension_dir in extensions_dir.iterdir():
            if extension_dir.is_dir():
                try:
                    is_valid, verification_data = self.verify_extension(extension_dir)
                    results[extension_dir.name] = {
                        'valid': is_valid,
                        'verification_data': verification_data
                    }
                except Exception as e:
                    results[extension_dir.name] = {
                        'valid': False,
                        'verification_data': {'error': str(e)}
                    }
        
        return results


class ExtensionSignatureManager:
    """Manages extension signatures in database"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def store_signature(self, signature_data: ExtensionSignatureCreate) -> ExtensionSignatureResponse:
        """Store extension signature in database"""
        try:
            signature = ExtensionSignature(**signature_data.dict())
            self.db_session.add(signature)
            self.db_session.commit()
            self.db_session.refresh(signature)
            
            return ExtensionSignatureResponse.from_orm(signature)
            
        except Exception as e:
            self.db_session.rollback()
            raise ExtensionSecurityError(f"Failed to store signature: {e}")
    
    def get_signature(self, extension_name: str, extension_version: str) -> Optional[ExtensionSignatureResponse]:
        """Get extension signature from database"""
        signature = self.db_session.query(ExtensionSignature).filter(
            ExtensionSignature.extension_name == extension_name,
            ExtensionSignature.extension_version == extension_version
        ).first()
        
        if signature:
            return ExtensionSignatureResponse.from_orm(signature)
        return None
    
    def invalidate_signature(self, extension_name: str, extension_version: str) -> bool:
        """Mark extension signature as invalid"""
        try:
            signature = self.db_session.query(ExtensionSignature).filter(
                ExtensionSignature.extension_name == extension_name,
                ExtensionSignature.extension_version == extension_version
            ).first()
            
            if signature:
                signature.is_valid = False
                self.db_session.commit()
                return True
            return False
            
        except Exception as e:
            self.db_session.rollback()
            raise ExtensionSecurityError(f"Failed to invalidate signature: {e}")
    
    def list_signatures(self, extension_name: Optional[str] = None) -> List[ExtensionSignatureResponse]:
        """List extension signatures"""
        query = self.db_session.query(ExtensionSignature)
        
        if extension_name:
            query = query.filter(ExtensionSignature.extension_name == extension_name)
        
        signatures = query.all()
        return [ExtensionSignatureResponse.from_orm(sig) for sig in signatures]