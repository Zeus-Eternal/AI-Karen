"""
Extension Marketplace Module

This module provides the extension marketplace functionality including
search, installation, updates, and dependency resolution.
"""

from .models import (
    ExtensionListing,
    ExtensionVersion,
    ExtensionDependency,
    ExtensionInstallation,
    ExtensionReview,
    ExtensionListingSchema,
    ExtensionVersionSchema,
    ExtensionInstallationSchema,
    ExtensionSearchRequest,
    ExtensionSearchResponse,
    ExtensionInstallRequest,
    ExtensionInstallResponse,
    ExtensionUpdateRequest,
    DependencyResolutionResult,
    ExtensionStatus,
    InstallationStatus
)

from .service import ExtensionMarketplaceService
from .routes import router as marketplace_router
from .version_manager import VersionManager

__all__ = [
    # Models
    'ExtensionListing',
    'ExtensionVersion', 
    'ExtensionDependency',
    'ExtensionInstallation',
    'ExtensionReview',
    'ExtensionListingSchema',
    'ExtensionVersionSchema',
    'ExtensionInstallationSchema',
    'ExtensionSearchRequest',
    'ExtensionSearchResponse',
    'ExtensionInstallRequest',
    'ExtensionInstallResponse',
    'ExtensionUpdateRequest',
    'DependencyResolutionResult',
    'ExtensionStatus',
    'InstallationStatus',
    
    # Services
    'ExtensionMarketplaceService',
    'VersionManager',
    
    # Routes
    'marketplace_router'
]