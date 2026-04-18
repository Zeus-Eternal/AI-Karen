"""
Token Manager for Advanced Token Operations

This module provides comprehensive token management capabilities including:
- Token blacklisting and revocation
- Token validation with enhanced security checks
- Token refresh and rotation
- Token analytics and monitoring
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
import hashlib
import jwt

logger = logging.getLogger(__name__)


@dataclass
class TokenRecord:
    """Token record for tracking token state."""

    token_hash: str
    user_id: str
    tenant_id: str
    token_type: str
    created_at: datetime
    expires_at: datetime
    revoked: bool = False
    last_used: Optional[datetime] = None
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TokenManager:
    """Advanced token manager with blacklist and analytics capabilities."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize token manager with configuration."""
        self.config = config
        self.blacklist: Set[str] = set()
        self.token_records: Dict[str, TokenRecord] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

        # Load existing blacklist and records
        self._load_token_data()

        # Start cleanup task
        self._start_cleanup_task()

    def _hash_token(self, token: str) -> str:
        """Create SHA256 hash of token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _load_token_data(self):
        """Load token blacklist and records from storage."""
        try:
            data_dir = Path("token_data")
            data_dir.mkdir(exist_ok=True)

            # Load blacklist
            blacklist_file = data_dir / "blacklist.json"
            if blacklist_file.exists():
                with open(blacklist_file, "r") as f:
                    self.blacklist = set(json.load(f))
                logger.info(f"Loaded {len(self.blacklist)} blacklisted tokens")

            # Load token records
            records_file = data_dir / "records.json"
            if records_file.exists():
                with open(records_file, "r") as f:
                    records_data = json.load(f)
                    for record_data in records_data:
                        record = TokenRecord(
                            token_hash=record_data["token_hash"],
                            user_id=record_data["user_id"],
                            tenant_id=record_data["tenant_id"],
                            token_type=record_data["token_type"],
                            created_at=datetime.fromisoformat(
                                record_data["created_at"]
                            ),
                            expires_at=datetime.fromisoformat(
                                record_data["expires_at"]
                            ),
                            revoked=record_data.get("revoked", False),
                            last_used=datetime.fromisoformat(record_data["last_used"])
                            if record_data.get("last_used")
                            else None,
                            usage_count=record_data.get("usage_count", 0),
                            metadata=record_data.get("metadata", {}),
                        )
                        self.token_records[record.token_hash] = record
                logger.info(f"Loaded {len(self.token_records)} token records")

        except Exception as e:
            logger.error(f"Failed to load token data: {e}")

    def _save_token_data(self):
        """Save token blacklist and records to storage."""
        try:
            data_dir = Path("token_data")
            data_dir.mkdir(exist_ok=True)

            # Save blacklist
            blacklist_file = data_dir / "blacklist.json"
            with open(blacklist_file, "w") as f:
                json.dump(list(self.blacklist), f)

            # Save token records
            records_file = data_dir / "records.json"
            records_data = []
            for record in self.token_records.values():
                records_data.append(
                    {
                        "token_hash": record.token_hash,
                        "user_id": record.user_id,
                        "tenant_id": record.tenant_id,
                        "token_type": record.token_type,
                        "created_at": record.created_at.isoformat(),
                        "expires_at": record.expires_at.isoformat(),
                        "revoked": record.revoked,
                        "last_used": record.last_used.isoformat()
                        if record.last_used
                        else None,
                        "usage_count": record.usage_count,
                        "metadata": record.metadata,
                    }
                )
            with open(records_file, "w") as f:
                json.dump(records_data, f)

        except Exception as e:
            logger.error(f"Failed to save token data: {e}")

    def _start_cleanup_task(self):
        """Start background task to clean up expired tokens."""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_tokens())

    async def _cleanup_expired_tokens(self):
        """Clean up expired tokens from storage."""
        while True:
            try:
                async with self._lock:
                    now = datetime.now(timezone.utc)
                    expired_tokens = []

                    for token_hash, record in self.token_records.items():
                        if record.expires_at < now:
                            expired_tokens.append(token_hash)

                    for token_hash in expired_tokens:
                        del self.token_records[token_hash]
                        if token_hash in self.blacklist:
                            self.blacklist.remove(token_hash)

                    if expired_tokens:
                        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
                        self._save_token_data()

                # Wait for 1 hour before next cleanup
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Token cleanup error: {e}")
                await asyncio.sleep(3600)

    async def create_token_record(
        self,
        token: str,
        user_id: str,
        tenant_id: str,
        token_type: str,
        expires_at: datetime,
    ) -> TokenRecord:
        """Create a token record for tracking."""
        token_hash = self._hash_token(token)

        async with self._lock:
            record = TokenRecord(
                token_hash=token_hash,
                user_id=user_id,
                tenant_id=tenant_id,
                token_type=token_type,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
            )
            self.token_records[token_hash] = record
            self._save_token_data()

        return record

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token with enhanced security checks."""
        token_hash = self._hash_token(token)

        # Check if token is blacklisted
        if token_hash in self.blacklist:
            return {"valid": False, "reason": "token_blacklisted", "payload": None}

        # Check if token exists in records
        if token_hash not in self.token_records:
            return {"valid": False, "reason": "token_not_found", "payload": None}

        record = self.token_records[token_hash]

        # Check if token is revoked
        if record.revoked:
            return {"valid": False, "reason": "token_revoked", "payload": None}

        # Check if token is expired
        now = datetime.now(timezone.utc)
        if record.expires_at < now:
            return {"valid": False, "reason": "token_expired", "payload": None}

        # Update token usage
        async with self._lock:
            record.usage_count += 1
            record.last_used = now
            self._save_token_data()

        # Decode token to get payload
        try:
            secret_key = self.config.get("secret_key")
            algorithm = self.config.get("algorithm", "HS256")
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])

            return {
                "valid": True,
                "reason": "token_valid",
                "payload": payload,
                "record": record,
            }

        except jwt.PyJWTError as e:
            return {"valid": False, "reason": f"jwt_error: {str(e)}", "payload": None}

    async def revoke_token(self, token: str) -> bool:
        """Revoke a specific token."""
        token_hash = self._hash_token(token)

        async with self._lock:
            if token_hash in self.token_records:
                self.token_records[token_hash].revoked = True
                self.blacklist.add(token_hash)
                self._save_token_data()
                logger.info(
                    f"Token revoked for user: {self.token_records[token_hash].user_id}"
                )
                return True

            # If token not in records, add to blacklist directly
            self.blacklist.add(token_hash)
            self._save_token_data()
            return True

    async def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a specific user."""
        revoked_count = 0

        async with self._lock:
            for token_hash, record in self.token_records.items():
                if record.user_id == user_id and not record.revoked:
                    record.revoked = True
                    self.blacklist.add(token_hash)
                    revoked_count += 1

            if revoked_count > 0:
                self._save_token_data()
                logger.info(f"Revoked {revoked_count} tokens for user: {user_id}")

        return revoked_count

    async def get_user_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tokens for a specific user."""
        user_tokens = []

        for record in self.token_records.values():
            if record.user_id == user_id:
                user_tokens.append(
                    {
                        "token_hash": record.token_hash,
                        "tenant_id": record.tenant_id,
                        "token_type": record.token_type,
                        "created_at": record.created_at.isoformat(),
                        "expires_at": record.expires_at.isoformat(),
                        "revoked": record.revoked,
                        "last_used": record.last_used.isoformat()
                        if record.last_used
                        else None,
                        "usage_count": record.usage_count,
                        "metadata": record.metadata,
                    }
                )

        return user_tokens

    async def get_token_statistics(self) -> Dict[str, Any]:
        """Get token statistics and analytics."""
        total_tokens = len(self.token_records)
        active_tokens = sum(
            1 for record in self.token_records.values() if not record.revoked
        )
        revoked_tokens = sum(
            1 for record in self.token_records.values() if record.revoked
        )
        blacklisted_tokens = len(self.blacklist)

        # Token type distribution
        token_types = {}
        for record in self.token_records.values():
            token_types[record.token_type] = token_types.get(record.token_type, 0) + 1

        # Usage statistics
        total_usage = sum(record.usage_count for record in self.token_records.values())
        avg_usage = total_usage / total_tokens if total_tokens > 0 else 0

        return {
            "total_tokens": total_tokens,
            "active_tokens": active_tokens,
            "revoked_tokens": revoked_tokens,
            "blacklisted_tokens": blacklisted_tokens,
            "token_types": token_types,
            "total_usage": total_usage,
            "average_usage": avg_usage,
            "blacklist_size": len(self.blacklist),
        }

    async def cleanup_expired_tokens(self) -> int:
        """Manually trigger cleanup of expired tokens."""
        cleaned_count = 0

        async with self._lock:
            now = datetime.now(timezone.utc)
            expired_tokens = []

            for token_hash, record in self.token_records.items():
                if record.expires_at < now:
                    expired_tokens.append(token_hash)

            for token_hash in expired_tokens:
                del self.token_records[token_hash]
                if token_hash in self.blacklist:
                    self.blacklist.remove(token_hash)

            cleaned_count = len(expired_tokens)

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired tokens")
                self._save_token_data()

        return cleaned_count

    async def shutdown(self):
        """Shutdown token manager and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Save final state
        self._save_token_data()
        logger.info("Token manager shutdown completed")
