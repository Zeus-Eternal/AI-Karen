"""
Cache backend implementations for the integrated cache system.
"""

from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ai_karen_engine.infra.integrated_cache_system import CacheEntry


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional["CacheEntry"]:
        raise NotImplementedError

    @abstractmethod
    async def set(self, entry: "CacheEntry") -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def cleanup_expired(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class MemoryBackend(CacheBackend):
    """Simple in-memory cache backend."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._store: Dict[str, "CacheEntry"] = {}

    def _is_expired(self, entry: "CacheEntry") -> bool:
        return entry.ttl is not None and (entry.created_at + entry.ttl) <= time.time()

    async def get(self, key: str) -> Optional["CacheEntry"]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if self._is_expired(entry):
            self._store.pop(key, None)
            return None
        return entry

    async def set(self, entry: "CacheEntry") -> bool:
        self._store[entry.key] = entry
        return True

    async def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> None:
        self._store.clear()

    async def cleanup_expired(self) -> None:
        expired_keys = [
            key for key, entry in self._store.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            self._store.pop(key, None)

    async def get_stats(self) -> Dict[str, Any]:
        await self.cleanup_expired()
        return {
            "backend": "memory",
            "entry_count": len(self._store),
        }

    async def close(self) -> None:
        await self.clear()


class DiskBackend(CacheBackend):
    """Disk-backed cache using JSON files."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        from ai_karen_engine.infra.integrated_cache_system import CacheEntry

        self.config = config or {}
        self.CacheEntry = CacheEntry
        self.base_dir = Path(self.config.get("path", "/tmp/ai_karen_cache"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        safe_name = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self.base_dir / f"{safe_name}.json"

    def _is_expired(self, entry: "CacheEntry") -> bool:
        return entry.ttl is not None and (entry.created_at + entry.ttl) <= time.time()

    async def get(self, key: str) -> Optional["CacheEntry"]:
        path = self._path_for_key(key)
        if not path.exists():
            return None

        try:
            payload = json.loads(path.read_text())
            entry = self.CacheEntry(
                key=payload["key"],
                value=payload["value"],
                ttl=payload.get("ttl"),
                created_at=payload.get("created_at", 0.0),
                access_count=payload.get("access_count", 0),
                metadata=payload.get("metadata") or {},
            )
        except Exception:
            path.unlink(missing_ok=True)
            return None

        if self._is_expired(entry):
            path.unlink(missing_ok=True)
            return None

        return entry

    async def set(self, entry: "CacheEntry") -> bool:
        path = self._path_for_key(entry.key)
        path.write_text(json.dumps({
            "key": entry.key,
            "value": entry.value,
            "ttl": entry.ttl,
            "created_at": entry.created_at,
            "access_count": entry.access_count,
            "metadata": entry.metadata,
        }))
        return True

    async def delete(self, key: str) -> bool:
        path = self._path_for_key(key)
        if not path.exists():
            return False
        path.unlink(missing_ok=True)
        return True

    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None

    async def clear(self) -> None:
        for child in self.base_dir.glob("*.json"):
            child.unlink(missing_ok=True)

    async def cleanup_expired(self) -> None:
        for child in self.base_dir.glob("*.json"):
            key = child.stem
            await self.get(key)

    async def get_stats(self) -> Dict[str, Any]:
        await self.cleanup_expired()
        return {
            "backend": "disk",
            "path": str(self.base_dir),
            "entry_count": len(list(self.base_dir.glob("*.json"))),
        }

    async def close(self) -> None:
        await asyncio.sleep(0)


class RedisBackend(CacheBackend):
    """Redis cache backend with graceful in-memory fallback when Redis is unavailable."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._fallback = MemoryBackend(config)
        self._client: Any = None

        try:
            import redis.asyncio as redis  # type: ignore

            self._client = redis.Redis(
                host=self.config.get("host", "localhost"),
                port=int(self.config.get("port", 6379)),
                db=int(self.config.get("db", 0)),
                decode_responses=True,
            )
        except Exception:
            self._client = None

    async def get(self, key: str) -> Optional["CacheEntry"]:
        if self._client is None:
            return await self._fallback.get(key)

        from ai_karen_engine.infra.integrated_cache_system import CacheEntry

        raw = await self._client.get(key)
        if raw is None:
            return None

        payload = json.loads(raw)
        return CacheEntry(
            key=payload["key"],
            value=payload["value"],
            ttl=payload.get("ttl"),
            created_at=payload.get("created_at", 0.0),
            access_count=payload.get("access_count", 0),
            metadata=payload.get("metadata") or {},
        )

    async def set(self, entry: "CacheEntry") -> bool:
        if self._client is None:
            return await self._fallback.set(entry)

        payload = json.dumps({
            "key": entry.key,
            "value": entry.value,
            "ttl": entry.ttl,
            "created_at": entry.created_at,
            "access_count": entry.access_count,
            "metadata": entry.metadata,
        })
        if entry.ttl is not None:
            await self._client.set(entry.key, payload, ex=entry.ttl)
        else:
            await self._client.set(entry.key, payload)
        return True

    async def delete(self, key: str) -> bool:
        if self._client is None:
            return await self._fallback.delete(key)
        return bool(await self._client.delete(key))

    async def exists(self, key: str) -> bool:
        if self._client is None:
            return await self._fallback.exists(key)
        return bool(await self._client.exists(key))

    async def clear(self) -> None:
        if self._client is None:
            await self._fallback.clear()
            return
        await self._client.flushdb()

    async def cleanup_expired(self) -> None:
        if self._client is None:
            await self._fallback.cleanup_expired()
            return
        await asyncio.sleep(0)

    async def get_stats(self) -> Dict[str, Any]:
        if self._client is None:
            stats = await self._fallback.get_stats()
            stats["backend"] = "redis-fallback"
            return stats

        size = await self._client.dbsize()
        return {
            "backend": "redis",
            "entry_count": size,
        }

    async def close(self) -> None:
        if self._client is None:
            await self._fallback.close()
            return
        await self._client.aclose()
