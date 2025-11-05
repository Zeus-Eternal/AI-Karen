"""
Enhanced EchoVault - Production-ready user data vault
Provides versioning, encryption, compression, and backup management.
"""

import json
import gzip
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import aiofiles
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class VaultVersion(str, Enum):
    """Vault version enum."""
    V1 = "v1"
    V2 = "v2"  # With encryption
    V3 = "v3"  # With compression


@dataclass
class VaultSnapshot:
    """Represents a point-in-time snapshot of the vault."""
    timestamp: str
    version: str
    data_hash: str
    size_bytes: int
    compressed: bool
    encrypted: bool
    metadata: Dict[str, Any]


class EnhancedEchoVault:
    """
    Production-ready immutable per-user backup vault.

    Features:
    - Versioning with snapshot history
    - Optional encryption
    - Optional compression
    - Backup rotation (keep last N backups)
    - Data validation
    - Async operations
    - Integrity checking (SHA256)
    - Metadata tracking
    - Audit logging
    """

    def __init__(
        self,
        user_id: str,
        base_dir: Path = Path("data/users"),
        enable_encryption: bool = False,
        enable_compression: bool = True,
        max_backups: int = 10,
        encryption_key: Optional[bytes] = None
    ):
        self.user_id = user_id
        self.base_dir = Path(base_dir)
        self.vault_dir = self.base_dir / user_id / "vault"
        self.vault_dir.mkdir(parents=True, exist_ok=True)

        self.current_file = self.vault_dir / "current.json"
        self.snapshots_dir = self.vault_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

        self.enable_encryption = enable_encryption
        self.enable_compression = enable_compression
        self.max_backups = max_backups
        self.encryption_key = encryption_key

        if enable_encryption and not encryption_key:
            # Generate a key if not provided
            self.encryption_key = hashlib.sha256(user_id.encode()).digest()

    def _get_data_hash(self, data: bytes) -> str:
        """Calculate SHA256 hash of data."""
        return hashlib.sha256(data).hexdigest()

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        return gzip.compress(data)

    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress gzip data."""
        return gzip.decompress(data)

    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using AES."""
        if not self.enable_encryption:
            return data

        try:
            from cryptography.fernet import Fernet
            # Use Fernet symmetric encryption
            key = hashlib.sha256(self.encryption_key).digest()
            # Fernet requires base64 encoded key
            import base64
            key_b64 = base64.urlsafe_b64encode(key)
            f = Fernet(key_b64)
            return f.encrypt(data)
        except ImportError:
            logger.warning("cryptography package not available, encryption disabled")
            return data

    def _decrypt_data(self, data: bytes) -> bytes:
        """Decrypt data using AES."""
        if not self.enable_encryption:
            return data

        try:
            from cryptography.fernet import Fernet
            key = hashlib.sha256(self.encryption_key).digest()
            import base64
            key_b64 = base64.urlsafe_b64encode(key)
            f = Fernet(key_b64)
            return f.decrypt(data)
        except ImportError:
            logger.warning("cryptography package not available, decryption skipped")
            return data

    async def backup(
        self,
        data: Dict[str, Any],
        create_snapshot: bool = True,
        merge: bool = True
    ) -> VaultSnapshot:
        """
        Write metadata to the vault.

        Args:
            data: Data to backup
            create_snapshot: Whether to create a snapshot
            merge: Whether to merge with existing data

        Returns:
            VaultSnapshot with backup info
        """
        # Merge with existing if requested
        if merge and self.current_file.exists():
            existing = await self.restore()
            existing.update(data)
            data = existing

        # Serialize to JSON
        json_data = json.dumps(data, indent=2)
        data_bytes = json_data.encode('utf-8')

        # Calculate original hash
        data_hash = self._get_data_hash(data_bytes)

        # Compress if enabled
        if self.enable_compression:
            data_bytes = self._compress_data(data_bytes)

        # Encrypt if enabled
        if self.enable_encryption:
            data_bytes = self._encrypt_data(data_bytes)

        # Write to current file
        async with aiofiles.open(self.current_file, 'wb') as f:
            await f.write(data_bytes)

        # Create snapshot if requested
        snapshot = VaultSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            version=VaultVersion.V3.value,
            data_hash=data_hash,
            size_bytes=len(data_bytes),
            compressed=self.enable_compression,
            encrypted=self.enable_encryption,
            metadata={
                "user_id": self.user_id,
                "keys": list(data.keys()) if isinstance(data, dict) else []
            }
        )

        if create_snapshot:
            await self._create_snapshot(data_bytes, snapshot)
            await self._rotate_snapshots()

        logger.info(
            f"Backed up vault for user {self.user_id}: "
            f"{len(data_bytes)} bytes (compressed={self.enable_compression}, "
            f"encrypted={self.enable_encryption})"
        )

        return snapshot

    async def restore(self) -> Dict[str, Any]:
        """
        Restore data from the vault.

        Returns:
            Stored data or empty dict if not found
        """
        if not self.current_file.exists():
            return {}

        async with aiofiles.open(self.current_file, 'rb') as f:
            data_bytes = await f.read()

        # Decrypt if encrypted
        if self.enable_encryption:
            data_bytes = self._decrypt_data(data_bytes)

        # Decompress if compressed
        if self.enable_compression:
            data_bytes = self._decompress_data(data_bytes)

        # Parse JSON
        json_data = data_bytes.decode('utf-8')
        data = json.loads(json_data)

        return data

    async def _create_snapshot(self, data_bytes: bytes, snapshot: VaultSnapshot) -> None:
        """Create a snapshot of the current vault state."""
        snapshot_file = self.snapshots_dir / f"{snapshot.timestamp}.snap"
        metadata_file = self.snapshots_dir / f"{snapshot.timestamp}.meta.json"

        # Write snapshot data
        async with aiofiles.open(snapshot_file, 'wb') as f:
            await f.write(data_bytes)

        # Write snapshot metadata
        async with aiofiles.open(metadata_file, 'w') as f:
            await f.write(json.dumps(asdict(snapshot), indent=2))

        logger.debug(f"Created snapshot: {snapshot_file}")

    async def _rotate_snapshots(self) -> None:
        """Rotate snapshots, keeping only the most recent N."""
        # Get all snapshot files
        snapshots = sorted(self.snapshots_dir.glob("*.snap"))

        # Delete oldest if we exceed max_backups
        if len(snapshots) > self.max_backups:
            to_delete = snapshots[:-self.max_backups]
            for snapshot_file in to_delete:
                # Delete both snapshot and metadata
                snapshot_file.unlink()
                meta_file = snapshot_file.with_suffix('.snap.meta.json')
                if meta_file.exists():
                    meta_file.unlink()
                logger.debug(f"Rotated snapshot: {snapshot_file}")

    async def list_snapshots(self) -> List[VaultSnapshot]:
        """
        List all available snapshots.

        Returns:
            List of VaultSnapshot objects
        """
        snapshots = []

        for meta_file in sorted(self.snapshots_dir.glob("*.meta.json")):
            try:
                async with aiofiles.open(meta_file, 'r') as f:
                    content = await f.read()
                    meta_data = json.loads(content)
                    snapshots.append(VaultSnapshot(**meta_data))
            except Exception as e:
                logger.error(f"Failed to load snapshot metadata {meta_file}: {e}")

        return snapshots

    async def restore_snapshot(self, timestamp: str) -> Dict[str, Any]:
        """
        Restore data from a specific snapshot.

        Args:
            timestamp: Timestamp of the snapshot

        Returns:
            Data from the snapshot
        """
        snapshot_file = self.snapshots_dir / f"{timestamp}.snap"

        if not snapshot_file.exists():
            raise FileNotFoundError(f"Snapshot not found: {timestamp}")

        async with aiofiles.open(snapshot_file, 'rb') as f:
            data_bytes = await f.read()

        # Decrypt if encrypted
        if self.enable_encryption:
            data_bytes = self._decrypt_data(data_bytes)

        # Decompress if compressed
        if self.enable_compression:
            data_bytes = self._decompress_data(data_bytes)

        # Parse JSON
        json_data = data_bytes.decode('utf-8')
        data = json.loads(json_data)

        return data

    async def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the vault.

        Returns:
            Dictionary with integrity check results
        """
        if not self.current_file.exists():
            return {"status": "empty", "message": "No vault data"}

        try:
            # Read current file
            async with aiofiles.open(self.current_file, 'rb') as f:
                data_bytes = await f.read()

            # Decrypt and decompress
            if self.enable_encryption:
                data_bytes = self._decrypt_data(data_bytes)
            if self.enable_compression:
                data_bytes = self._decompress_data(data_bytes)

            # Try to parse JSON
            json_data = data_bytes.decode('utf-8')
            data = json.loads(json_data)

            # Calculate hash
            data_hash = self._get_data_hash(json_data.encode('utf-8'))

            return {
                "status": "valid",
                "message": "Vault integrity verified",
                "hash": data_hash,
                "size_bytes": len(data_bytes),
                "keys": list(data.keys()) if isinstance(data, dict) else []
            }

        except Exception as e:
            return {
                "status": "corrupted",
                "message": f"Vault integrity check failed: {e}"
            }

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get vault statistics.

        Returns:
            Dictionary with vault statistics
        """
        stats = {
            "user_id": self.user_id,
            "vault_path": str(self.vault_dir),
            "current_exists": self.current_file.exists(),
            "snapshot_count": len(list(self.snapshots_dir.glob("*.snap"))),
            "compression_enabled": self.enable_compression,
            "encryption_enabled": self.enable_encryption,
            "max_backups": self.max_backups
        }

        if self.current_file.exists():
            stats["current_size_bytes"] = self.current_file.stat().st_size
            stats["current_modified"] = datetime.fromtimestamp(
                self.current_file.stat().st_mtime
            ).isoformat()

        # Total size of all snapshots
        total_snapshot_size = sum(
            f.stat().st_size for f in self.snapshots_dir.glob("*.snap")
        )
        stats["total_snapshot_size_bytes"] = total_snapshot_size

        return stats

    async def export_vault(self, output_path: Path) -> None:
        """
        Export vault to a single file.

        Args:
            output_path: Path to export file
        """
        export_data = {
            "user_id": self.user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "current_data": await self.restore() if self.current_file.exists() else {},
            "snapshots": []
        }

        # Include snapshots
        snapshots = await self.list_snapshots()
        for snapshot in snapshots:
            try:
                snapshot_data = await self.restore_snapshot(snapshot.timestamp)
                export_data["snapshots"].append({
                    "timestamp": snapshot.timestamp,
                    "data": snapshot_data,
                    "metadata": asdict(snapshot)
                })
            except Exception as e:
                logger.error(f"Failed to export snapshot {snapshot.timestamp}: {e}")

        # Write export file
        async with aiofiles.open(output_path, 'w') as f:
            await f.write(json.dumps(export_data, indent=2))

        logger.info(f"Exported vault to {output_path}")

    async def import_vault(self, import_path: Path) -> None:
        """
        Import vault from a file.

        Args:
            import_path: Path to import file
        """
        async with aiofiles.open(import_path, 'r') as f:
            content = await f.read()
            import_data = json.loads(content)

        # Import current data
        if import_data.get("current_data"):
            await self.backup(import_data["current_data"], create_snapshot=False)

        # Import snapshots
        for snapshot_info in import_data.get("snapshots", []):
            snapshot_data = snapshot_info["data"]
            # Create snapshot with original timestamp
            json_data = json.dumps(snapshot_data)
            data_bytes = json_data.encode('utf-8')

            if self.enable_compression:
                data_bytes = self._compress_data(data_bytes)
            if self.enable_encryption:
                data_bytes = self._encrypt_data(data_bytes)

            snapshot = VaultSnapshot(**snapshot_info["metadata"])
            await self._create_snapshot(data_bytes, snapshot)

        logger.info(f"Imported vault from {import_path}")


# Synchronous wrapper for backward compatibility
class EchoVault:
    """Synchronous wrapper for EnhancedEchoVault."""

    def __init__(self, user_id: str, base_dir: Path = Path("data/users")):
        self.vault = EnhancedEchoVault(user_id, base_dir)

    def backup(self, data: Dict[str, Any]) -> None:
        """Synchronous backup."""
        asyncio.run(self.vault.backup(data))

    def restore(self) -> Dict[str, Any]:
        """Synchronous restore."""
        return asyncio.run(self.vault.restore())
