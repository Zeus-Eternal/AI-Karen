"""
Remote Package Discovery Service - Discovers plugins from remote sources.

This service:
- Discovers plugins from remote registries
- Validates remote plugin packages
- Caches discovery results
- Provides marketplace metadata
- Supports multiple registry sources
"""

import logging
import hashlib
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp

from ai_karen_engine.extensions.platform.core.manifest import ExtensionManifest
from ai_karen_engine.extensions.platform.core.registry.plugin_registry import get_registry

logger = logging.getLogger("kari.marketplace_discovery")


class RegistrySource(Enum):
    """Supported registry sources."""

    LOCAL = "local"
    GITHUB = "github"
    GITLAB = "gitlab"
    NPM = "npm"
    PYPI = "pypi"
    CUSTOM = "custom"


@dataclass
class RemotePlugin:
    """Represents a plugin discovered from a remote source."""

    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    source: RegistrySource
    download_url: str
    manifest_url: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    download_count: int = 0
    last_updated: Optional[datetime] = None
    verified: bool = False
    signature: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegistryConfig:
    """Configuration for a remote registry."""

    source: RegistrySource
    name: str
    base_url: str
    enabled: bool = True
    priority: int = 0
    auth_token: Optional[str] = None
    cache_ttl: int = 3600  # 1 hour default
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """Search query for plugin discovery."""

    query: str = ""
    category: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    sort_by: str = "relevance"  # relevance, popularity, updated, name
    limit: int = 20
    offset: int = 0


class MarketplaceDiscoveryService:
    """
    Discovers plugins from remote registries and provides marketplace functionality.

    Features:
    - Multiple registry source support
    - Plugin search and filtering
    - Manifest validation
    - Result caching
    - Metadata enrichment
    """

    DEFAULT_REGISTRIES = [
        RegistryConfig(
            source=RegistrySource.LOCAL,
            name="Local Registry",
            base_url="/api/extensions",
            enabled=True,
            priority=100,
        ),
    ]

    def __init__(self):
        self._registries: List[RegistryConfig] = []
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._session: Optional[aiohttp.ClientSession] = None

        # Initialize with default registries
        self._registries.extend(self.DEFAULT_REGISTRIES)

        logger.info(
            f"MarketplaceDiscoveryService initialized with {len(self._registries)} registries"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def add_registry(self, config: RegistryConfig):
        """Add a registry source."""
        self._registries.append(config)
        logger.info(f"Added registry: {config.name} ({config.source.value})")

    def remove_registry(self, name: str) -> bool:
        """Remove a registry source."""
        initial_len = len(self._registries)
        self._registries = [r for r in self._registries if r.name != name]
        return len(self._registries) < initial_len

    def get_registries(self) -> List[Dict[str, Any]]:
        """Get all configured registries."""
        return [
            {
                "name": r.name,
                "source": r.source.value,
                "base_url": r.base_url,
                "enabled": r.enabled,
                "priority": r.priority,
            }
            for r in sorted(self._registries, key=lambda x: x.priority, reverse=True)
        ]

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key."""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached(self, cache_key: str, ttl: int) -> Optional[Any]:
        """Get cached result if not expired."""
        if cache_key not in self._cache:
            return None

        timestamp = self._cache_timestamps.get(cache_key)
        if not timestamp:
            return None

        if datetime.utcnow() - timestamp > timedelta(seconds=ttl):
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None

        return self._cache[cache_key]

    def _set_cached(self, cache_key: str, data: Any):
        """Set cache entry."""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.utcnow()

    async def discover_local_plugins(self) -> List[RemotePlugin]:
        """Discover plugins from local registry."""
        try:
            registry = get_registry()
            discovered = registry.list_discovered()

            plugins = []
            for plugin_id in discovered:
                metadata = registry.get_metadata(plugin_id)
                if metadata:
                    plugin = RemotePlugin(
                        plugin_id=plugin_id,
                        name=plugin_id,
                        version=metadata.version,
                        description=metadata.description or "",
                        author=metadata.author or "Unknown",
                        source=RegistrySource.LOCAL,
                        download_url=f"/api/extensions/{plugin_id}/download",
                        manifest_url=f"/api/extensions/{plugin_id}/manifest",
                        category=metadata.category or "general",
                        tags=metadata.tags or [],
                        last_updated=datetime.utcnow(),
                        verified=True,
                    )
                    plugins.append(plugin)

            logger.info(f"Discovered {len(plugins)} local plugins")
            return plugins

        except Exception as e:
            logger.error(f"Failed to discover local plugins: {e}")
            return []

    async def discover_github_plugins(
        self, repo_owner: str, repo_name: str
    ) -> List[RemotePlugin]:
        """Discover plugins from a GitHub repository."""
        try:
            session = await self._get_session()

            # Fetch repository contents
            api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"

            headers = {}
            if any(
                r.source == RegistrySource.GITHUB and r.auth_token
                for r in self._registries
            ):
                github_config = next(
                    r
                    for r in self._registries
                    if r.source == RegistrySource.GITHUB and r.auth_token
                )
                headers["Authorization"] = f"token {github_config.auth_token}"

            async with session.get(api_url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"GitHub API returned status {response.status}")
                    return []

                contents = await response.json()

            plugins = []

            # Look for plugin directories (containing plugin_manifest.json)
            for item in contents:
                if item.get("type") == "dir":
                    dir_name = item["name"]

                    # Check if this directory contains a plugin manifest
                    manifest_url = f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{dir_name}/plugin_manifest.json"

                    async with session.get(
                        manifest_url, headers=headers
                    ) as manifest_response:
                        if manifest_response.status == 200:
                            manifest_data = await manifest_response.json()

                            try:
                                plugin = self._parse_github_manifest(
                                    manifest_data, dir_name, repo_owner, repo_name
                                )
                                plugins.append(plugin)
                            except Exception as e:
                                logger.warning(
                                    f"Failed to parse manifest from {dir_name}: {e}"
                                )

            logger.info(
                f"Discovered {len(plugins)} plugins from GitHub: {repo_owner}/{repo_name}"
            )
            return plugins

        except Exception as e:
            logger.error(f"Failed to discover GitHub plugins: {e}")
            return []

    def _parse_github_manifest(
        self,
        manifest_data: Dict[str, Any],
        dir_name: str,
        repo_owner: str,
        repo_name: str,
    ) -> RemotePlugin:
        """Parse a GitHub manifest into a RemotePlugin."""
        version = manifest_data.get("version", "0.0.1")

        return RemotePlugin(
            plugin_id=manifest_data.get("id", manifest_data.get("name", dir_name)),
            name=manifest_data.get("display_name", manifest_data.get("name", dir_name)),
            version=version,
            description=manifest_data.get("description", ""),
            author=manifest_data.get("author", repo_owner),
            source=RegistrySource.GITHUB,
            download_url=f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/main.tar.gz",
            manifest_url=f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/main/{dir_name}/plugin_manifest.json",
            homepage=f"https://github.com/{repo_owner}/{repo_name}/tree/main/{dir_name}",
            license=manifest_data.get("license"),
            category=manifest_data.get("category", "general"),
            tags=manifest_data.get("tags", []),
            last_updated=datetime.utcnow(),
            verified=False,
            metadata={
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "dir_name": dir_name,
                "manifest": manifest_data,
            },
        )

    async def search_plugins(self, query: SearchQuery) -> List[RemotePlugin]:
        """
        Search for plugins across all enabled registries.

        Args:
            query: Search query parameters

        Returns:
            List of matching plugins
        """
        all_plugins: List[RemotePlugin] = []

        # Discover from all enabled registries
        for registry in self._registries:
            if not registry.enabled:
                continue

            try:
                if registry.source == RegistrySource.LOCAL:
                    plugins = await self.discover_local_plugins()
                elif registry.source == RegistrySource.GITHUB:
                    # GitHub discovery requires specific repo info
                    # This would be configured in registry metadata
                    repo_info = registry.metadata.get("repo")
                    if repo_info:
                        parts = repo_info.split("/")
                        if len(parts) == 2:
                            plugins = await self.discover_github_plugins(
                                parts[0], parts[1]
                            )
                    else:
                        plugins = []
                else:
                    # Custom registry discovery
                    plugins = await self._discover_custom_registry(registry)

                all_plugins.extend(plugins)

            except Exception as e:
                logger.warning(f"Failed to discover from {registry.name}: {e}")

        # Filter and sort results
        filtered = self._filter_plugins(all_plugins, query)

        return filtered

    def _filter_plugins(
        self, plugins: List[RemotePlugin], query: SearchQuery
    ) -> List[RemotePlugin]:
        """Filter and sort plugins based on query."""
        filtered = plugins

        # Text search
        if query.query:
            search_terms = query.query.lower().split()
            filtered = [
                p
                for p in filtered
                if any(
                    term in p.name.lower()
                    or term in p.description.lower()
                    or term in p.plugin_id.lower()
                    or term in p.author.lower()
                    for term in search_terms
                )
            ]

        # Category filter
        if query.category:
            filtered = [p for p in filtered if p.category == query.category]

        # Author filter
        if query.author:
            filtered = [p for p in filtered if query.author.lower() in p.author.lower()]

        # Tags filter
        if query.tags:
            filtered = [
                p
                for p in filtered
                if any(tag.lower() in [t.lower() for t in p.tags] for tag in query.tags)
            ]

        # Sort
        sort_key = query.sort_by
        if sort_key == "relevance":
            # Keep original order (most relevant first)
            pass
        elif sort_key == "popularity":
            filtered.sort(key=lambda p: p.download_count, reverse=True)
        elif sort_key == "updated":
            filtered.sort(key=lambda p: p.last_updated or datetime.min, reverse=True)
        elif sort_key == "name":
            filtered.sort(key=lambda p: p.name.lower())

        # Paginate
        offset = query.offset
        limit = query.limit
        filtered = filtered[offset : offset + limit]

        return filtered

    async def _discover_custom_registry(
        self, config: RegistryConfig
    ) -> List[RemotePlugin]:
        """Discover plugins from a custom registry."""
        try:
            session = await self._get_session()

            cache_key = self._get_cache_key(f"custom:{config.name}", {})
            cached = self._get_cached(cache_key, config.cache_ttl)
            if cached:
                return cached

            headers = {}
            if config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"

            async with session.get(
                f"{config.base_url}/plugins", headers=headers
            ) as response:
                if response.status != 200:
                    logger.warning(
                        f"Custom registry {config.name} returned status {response.status}"
                    )
                    return []

                data = await response.json()

            plugins = []
            for item in data.get("plugins", []):
                plugin = RemotePlugin(
                    plugin_id=item.get("id", item.get("name")),
                    name=item.get("display_name", item.get("name")),
                    version=item.get("version", "0.0.0"),
                    description=item.get("description", ""),
                    author=item.get("author", "Unknown"),
                    source=RegistrySource.CUSTOM,
                    download_url=item.get("download_url"),
                    manifest_url=item.get("manifest_url"),
                    homepage=item.get("homepage"),
                    license=item.get("license"),
                    category=item.get("category", "general"),
                    tags=item.get("tags", []),
                    rating=item.get("rating"),
                    download_count=item.get("download_count", 0),
                    last_updated=datetime.fromisoformat(item["last_updated"])
                    if item.get("last_updated")
                    else None,
                    verified=item.get("verified", False),
                )
                plugins.append(plugin)

            self._set_cached(cache_key, plugins)
            return plugins

        except Exception as e:
            logger.error(f"Failed to discover from custom registry {config.name}: {e}")
            return []

    async def get_plugin_details(
        self, plugin_id: str, source: Optional[RegistrySource] = None
    ) -> Optional[RemotePlugin]:
        """
        Get detailed information about a specific plugin.

        Args:
            plugin_id: Plugin identifier
            source: Optional source filter

        Returns:
            Plugin details or None if not found
        """
        query = SearchQuery(query=plugin_id, limit=1)
        plugins = await self.search_plugins(query)

        if source:
            plugins = [p for p in plugins if p.source == source]

        return plugins[0] if plugins else None

    async def get_categories(self) -> Dict[str, int]:
        """Get all available plugin categories with counts."""
        query = SearchQuery(limit=1000)
        plugins = await self.search_plugins(query)

        categories: Dict[str, int] = {}
        for plugin in plugins:
            categories[plugin.category] = categories.get(plugin.category, 0) + 1

        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

    async def get_popular_plugins(self, limit: int = 10) -> List[RemotePlugin]:
        """Get most popular plugins by download count."""
        query = SearchQuery(sort_by="popularity", limit=limit)
        return await self.search_plugins(query)

    async def get_recently_updated(self, limit: int = 10) -> List[RemotePlugin]:
        """Get recently updated plugins."""
        query = SearchQuery(sort_by="updated", limit=limit)
        return await self.search_plugins(query)


# Singleton instance
_discovery_service: Optional[MarketplaceDiscoveryService] = None


def get_discovery_service() -> MarketplaceDiscoveryService:
    """Get the singleton discovery service instance."""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = MarketplaceDiscoveryService()
    return _discovery_service
