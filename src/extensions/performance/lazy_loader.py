"""
Extension Lazy Loader

Implements lazy loading strategies for extensions to improve startup performance.
"""

import asyncio
import importlib
import sys
import time
from typing import Any, Dict, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import logging

from ..models import ExtensionManifest, ExtensionRecord
from ..base import BaseExtension
from .cache_manager import ExtensionCacheManager


class LoadingStrategy(Enum):
    """Extension loading strategies."""
    EAGER = "eager"          # Load immediately
    LAZY = "lazy"            # Load on first access
    ON_DEMAND = "on_demand"  # Load when explicitly requested
    BACKGROUND = "background" # Load in background after startup


@dataclass
class LoadingPriority:
    """Extension loading priority configuration."""
    priority: int  # Lower numbers = higher priority
    strategy: LoadingStrategy
    dependencies: List[str]
    conditions: List[str]  # Conditions that must be met to load


@dataclass
class LoadingMetrics:
    """Metrics for extension loading performance."""
    extension_name: str
    load_start_time: float
    load_end_time: float
    initialization_time: float
    memory_usage_mb: float
    strategy_used: LoadingStrategy
    
    @property
    def total_load_time(self) -> float:
        return self.load_end_time - self.load_start_time


class ExtensionProxy:
    """Proxy object for lazy-loaded extensions."""
    
    def __init__(
        self,
        name: str,
        manifest: ExtensionManifest,
        loader: 'ExtensionLazyLoader'
    ):
        self.name = name
        self.manifest = manifest
        self._loader = loader
        self._extension: Optional[BaseExtension] = None
        self._loading = False
        self._load_event = asyncio.Event()
        
    async def _ensure_loaded(self) -> BaseExtension:
        """Ensure the extension is loaded."""
        if self._extension is not None:
            return self._extension
        
        if self._loading:
            await self._load_event.wait()
            if self._extension is None:
                raise RuntimeError(f"Failed to load extension {self.name}")
            return self._extension
        
        self._loading = True
        try:
            self._extension = await self._loader._load_extension_instance(
                self.name, self.manifest
            )
            self._load_event.set()
            return self._extension
        finally:
            self._loading = False
    
    async def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the loaded extension."""
        extension = await self._ensure_loaded()
        return getattr(extension, name)
    
    async def __call__(self, *args, **kwargs) -> Any:
        """Proxy method calls to the loaded extension."""
        extension = await self._ensure_loaded()
        if callable(extension):
            return await extension(*args, **kwargs)
        raise TypeError(f"Extension {self.name} is not callable")


class ExtensionLazyLoader:
    """
    Implements lazy loading strategies for extensions to improve startup performance.
    
    Features:
    - Multiple loading strategies (eager, lazy, on-demand, background)
    - Dependency-aware loading order
    - Conditional loading based on system state
    - Performance metrics and monitoring
    - Graceful fallback for loading failures
    """
    
    def __init__(
        self,
        extension_root: Path,
        cache_manager: ExtensionCacheManager,
        max_concurrent_loads: int = 5
    ):
        self.extension_root = extension_root
        self.cache_manager = cache_manager
        self.max_concurrent_loads = max_concurrent_loads
        
        self._loaded_extensions: Dict[str, BaseExtension] = {}
        self._extension_proxies: Dict[str, ExtensionProxy] = {}
        self._loading_priorities: Dict[str, LoadingPriority] = {}
        self._loading_semaphore = asyncio.Semaphore(max_concurrent_loads)
        self._loading_metrics: List[LoadingMetrics] = []
        self._background_tasks: Set[asyncio.Task] = set()
        
        self.logger = logging.getLogger(__name__)
    
    async def configure_loading_strategy(
        self,
        extension_name: str,
        strategy: LoadingStrategy,
        priority: int = 100,
        dependencies: Optional[List[str]] = None,
        conditions: Optional[List[str]] = None
    ) -> None:
        """Configure loading strategy for an extension."""
        self._loading_priorities[extension_name] = LoadingPriority(
            priority=priority,
            strategy=strategy,
            dependencies=dependencies or [],
            conditions=conditions or []
        )
    
    async def load_extensions(
        self,
        manifests: Dict[str, ExtensionManifest]
    ) -> Dict[str, BaseExtension]:
        """Load extensions according to their configured strategies."""
        self.logger.info(f"Starting lazy loading for {len(manifests)} extensions")
        
        # Separate extensions by loading strategy
        eager_extensions = []
        lazy_extensions = []
        background_extensions = []
        
        for name, manifest in manifests.items():
            priority = self._loading_priorities.get(name)
            if priority is None:
                # Default strategy based on extension characteristics
                strategy = self._determine_default_strategy(manifest)
                priority = LoadingPriority(
                    priority=100,
                    strategy=strategy,
                    dependencies=[],
                    conditions=[]
                )
                self._loading_priorities[name] = priority
            
            if priority.strategy == LoadingStrategy.EAGER:
                eager_extensions.append((name, manifest, priority))
            elif priority.strategy == LoadingStrategy.LAZY:
                lazy_extensions.append((name, manifest, priority))
            elif priority.strategy == LoadingStrategy.BACKGROUND:
                background_extensions.append((name, manifest, priority))
            # ON_DEMAND extensions are not loaded automatically
        
        # Load eager extensions first (sorted by priority)
        eager_extensions.sort(key=lambda x: x[2].priority)
        for name, manifest, priority in eager_extensions:
            if await self._check_loading_conditions(priority.conditions):
                await self._load_extension_with_deps(name, manifest, manifests)
        
        # Create proxies for lazy extensions
        for name, manifest, priority in lazy_extensions:
            self._extension_proxies[name] = ExtensionProxy(name, manifest, self)
        
        # Start background loading tasks
        for name, manifest, priority in background_extensions:
            if await self._check_loading_conditions(priority.conditions):
                task = asyncio.create_task(
                    self._background_load_extension(name, manifest, manifests)
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
        
        # Return loaded extensions and proxies
        result = dict(self._loaded_extensions)
        result.update(self._extension_proxies)
        
        self.logger.info(
            f"Lazy loading completed: "
            f"{len(self._loaded_extensions)} loaded, "
            f"{len(self._extension_proxies)} proxied, "
            f"{len(self._background_tasks)} background tasks"
        )
        
        return result
    
    async def load_extension_on_demand(
        self,
        name: str,
        manifests: Dict[str, ExtensionManifest]
    ) -> Optional[BaseExtension]:
        """Load a specific extension on demand."""
        if name in self._loaded_extensions:
            return self._loaded_extensions[name]
        
        if name in self._extension_proxies:
            proxy = self._extension_proxies[name]
            extension = await proxy._ensure_loaded()
            self._loaded_extensions[name] = extension
            del self._extension_proxies[name]
            return extension
        
        manifest = manifests.get(name)
        if manifest is None:
            self.logger.warning(f"Extension {name} not found for on-demand loading")
            return None
        
        return await self._load_extension_with_deps(name, manifest, manifests)
    
    async def get_loading_metrics(self) -> List[LoadingMetrics]:
        """Get loading performance metrics."""
        return list(self._loading_metrics)
    
    async def shutdown(self) -> None:
        """Shutdown the lazy loader and cancel background tasks."""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        self._background_tasks.clear()
        self.logger.info("Extension lazy loader shutdown completed")
    
    def _determine_default_strategy(self, manifest: ExtensionManifest) -> LoadingStrategy:
        """Determine default loading strategy based on extension characteristics."""
        # Critical system extensions should load eagerly
        if manifest.category in ['security', 'auth', 'core']:
            return LoadingStrategy.EAGER
        
        # UI-heavy extensions can be lazy loaded
        if manifest.capabilities.get('provides_ui', False):
            return LoadingStrategy.LAZY
        
        # Background service extensions can load in background
        if manifest.capabilities.get('provides_background_tasks', False):
            return LoadingStrategy.BACKGROUND
        
        # Default to lazy loading
        return LoadingStrategy.LAZY
    
    async def _check_loading_conditions(self, conditions: List[str]) -> bool:
        """Check if loading conditions are met."""
        for condition in conditions:
            if not await self._evaluate_condition(condition):
                return False
        return True
    
    async def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a loading condition."""
        # Simple condition evaluation - can be extended
        if condition == "system_ready":
            return True  # Assume system is ready
        elif condition == "user_authenticated":
            return True  # Simplified check
        elif condition.startswith("extension_loaded:"):
            ext_name = condition.split(":", 1)[1]
            return ext_name in self._loaded_extensions
        else:
            self.logger.warning(f"Unknown loading condition: {condition}")
            return True
    
    async def _load_extension_with_deps(
        self,
        name: str,
        manifest: ExtensionManifest,
        all_manifests: Dict[str, ExtensionManifest]
    ) -> BaseExtension:
        """Load extension with dependency resolution."""
        if name in self._loaded_extensions:
            return self._loaded_extensions[name]
        
        # Load dependencies first
        priority = self._loading_priorities.get(name)
        if priority:
            for dep_name in priority.dependencies:
                if dep_name not in self._loaded_extensions:
                    dep_manifest = all_manifests.get(dep_name)
                    if dep_manifest:
                        await self._load_extension_with_deps(
                            dep_name, dep_manifest, all_manifests
                        )
        
        # Load the extension
        extension = await self._load_extension_instance(name, manifest)
        self._loaded_extensions[name] = extension
        return extension
    
    async def _load_extension_instance(
        self,
        name: str,
        manifest: ExtensionManifest
    ) -> BaseExtension:
        """Load a single extension instance."""
        async with self._loading_semaphore:
            start_time = time.time()
            
            try:
                # Check cache first
                cache_key = f"extension_class:{name}"
                extension_class = await self.cache_manager.get(cache_key)
                
                if extension_class is None:
                    # Load extension module
                    extension_path = self.extension_root / name
                    spec = importlib.util.spec_from_file_location(
                        f"extensions.{name}",
                        extension_path / "__init__.py"
                    )
                    
                    if spec is None or spec.loader is None:
                        raise ImportError(f"Cannot load extension {name}")
                    
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"extensions.{name}"] = module
                    spec.loader.exec_module(module)
                    
                    # Get extension class
                    extension_class = getattr(module, 'Extension', None)
                    if extension_class is None:
                        raise AttributeError(f"Extension {name} has no Extension class")
                    
                    # Cache the class
                    await self.cache_manager.set(cache_key, extension_class)
                
                # Initialize extension
                init_start = time.time()
                extension = extension_class(manifest)
                await extension.initialize()
                init_time = time.time() - init_start
                
                end_time = time.time()
                
                # Record metrics
                metrics = LoadingMetrics(
                    extension_name=name,
                    load_start_time=start_time,
                    load_end_time=end_time,
                    initialization_time=init_time,
                    memory_usage_mb=self._estimate_memory_usage(extension),
                    strategy_used=self._loading_priorities[name].strategy
                )
                self._loading_metrics.append(metrics)
                
                self.logger.info(
                    f"Loaded extension {name} in {metrics.total_load_time:.2f}s "
                    f"(init: {init_time:.2f}s)"
                )
                
                return extension
                
            except Exception as e:
                self.logger.error(f"Failed to load extension {name}: {e}")
                raise
    
    async def _background_load_extension(
        self,
        name: str,
        manifest: ExtensionManifest,
        all_manifests: Dict[str, ExtensionManifest]
    ) -> None:
        """Load extension in background."""
        try:
            # Add small delay to avoid overwhelming system during startup
            await asyncio.sleep(1.0)
            
            extension = await self._load_extension_with_deps(
                name, manifest, all_manifests
            )
            self._loaded_extensions[name] = extension
            
        except Exception as e:
            self.logger.error(f"Background loading failed for extension {name}: {e}")
    
    def _estimate_memory_usage(self, extension: BaseExtension) -> float:
        """Estimate memory usage of an extension in MB."""
        # Simplified memory estimation
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0  # psutil not available