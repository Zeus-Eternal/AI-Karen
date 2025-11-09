"""
Extension Performance Optimization Module

This module provides performance optimization and scaling capabilities for the extension system.
"""

from .cache_manager import ExtensionCacheManager
from .lazy_loader import ExtensionLazyLoader
from .resource_optimizer import ExtensionResourceOptimizer
from .scaling_manager import ExtensionScalingManager
from .performance_monitor import ExtensionPerformanceMonitor

__all__ = [
    'ExtensionCacheManager',
    'ExtensionLazyLoader', 
    'ExtensionResourceOptimizer',
    'ExtensionScalingManager',
    'ExtensionPerformanceMonitor'
]