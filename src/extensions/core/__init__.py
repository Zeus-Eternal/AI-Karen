"""
Extension Framework Core Module

This module contains the core framework code for the extension system.
It provides the base classes, managers, and utilities needed to build
and manage extensions.

Key Components:
- BaseExtension: Base class for all extensions
- ExtensionManager: Manages extension lifecycle
- ExtensionRegistry: Registry for tracking loaded extensions
- ExtensionModels: Data models for extensions
- Security: Security framework for extensions
- API Integration: FastAPI integration utilities
- Background Tasks: Background task support
"""

from .base import BaseExtension
from .manager import ExtensionManager
from .registry import ExtensionRegistry
from .models import (
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
    ExtensionMetadata,
    ExtensionPermissions,
    ExtensionDependency
)

__all__ = [
    'BaseExtension',
    'ExtensionManager', 
    'ExtensionRegistry',
    'ExtensionManifest',
    'ExtensionRecord',
    'ExtensionStatus',
    'ExtensionMetadata',
    'ExtensionPermissions',
    'ExtensionDependency'
]