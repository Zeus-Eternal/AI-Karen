"""
Extension Marketplace Service

This module provides the core business logic for the extension marketplace,
including search, installation, updates, and dependency resolution.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

import semver
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from .models import (
    ExtensionListing, ExtensionVersion, ExtensionDependency, ExtensionInstallation,
    ExtensionReview, ExtensionListingSchema, ExtensionVersionSchema,
    ExtensionInstallationSchema, ExtensionSearchRequest, ExtensionSearchResponse,
    ExtensionInstallRequest, ExtensionInstallResponse, ExtensionUpdateRequest,
    DependencyResolutionResult, ExtensionStatus, InstallationStatus
)
from ..manager import ExtensionManager
from ..registry import ExtensionRegistry

logger = logging.getLogger(__name__)


class ExtensionMarketplaceService:
    """Service for managing extension marketplace operations."""
    
    def __init__(
        self,
        db_session: Session,
        extension_manager: ExtensionManager,
        extension_registry: ExtensionRegistry
    ):
        self.db = db_session
        self.extension_manager = extension_manager
        self.extension_registry = extension_registry
    
    # Search and Discovery
    
    async def search_extensions(
        self,
        search_request: ExtensionSearchRequest
    ) -> ExtensionSearchResponse:
        """Search for extensions in the marketplace."""
        query = self.db.query(ExtensionListing)
        
        # Apply filters
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    ExtensionListing.name.ilike(search_term),
                    ExtensionListing.display_name.ilike(search_term),
                    ExtensionListing.description.ilike(search_term),
                    ExtensionListing.tags.op('?&')(search_request.query.split())
                )
            )
        
        if search_request.category:
            query = query.filter(ExtensionListing.category == search_request.category)
        
        if search_request.tags:
            query = query.filter(ExtensionListing.tags.op('?&')(search_request.tags))
        
        if search_request.status:
            query = query.filter(ExtensionListing.status == search_request.status)
        else:
            # Default to approved extensions only
            query = query.filter(ExtensionListing.status == ExtensionStatus.APPROVED)
        
        if search_request.price_filter:
            if search_request.price_filter == "free":
                query = query.filter(ExtensionListing.price == "free")
            elif search_request.price_filter == "paid":
                query = query.filter(ExtensionListing.price != "free")
        
        # Apply sorting
        if search_request.sort_by == "popularity":
            sort_column = ExtensionListing.download_count
        elif search_request.sort_by == "rating":
            sort_column = ExtensionListing.rating_average
        elif search_request.sort_by == "newest":
            sort_column = ExtensionListing.published_at
        else:  # name
            sort_column = ExtensionListing.display_name
        
        if search_request.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (search_request.page - 1) * search_request.page_size
        extensions = query.offset(offset).limit(search_request.page_size).all()
        
        # Convert to schemas
        extension_schemas = [
            ExtensionListingSchema.from_orm(ext) for ext in extensions
        ]
        
        total_pages = (total_count + search_request.page_size - 1) // search_request.page_size
        
        return ExtensionSearchResponse(
            extensions=extension_schemas,
            total_count=total_count,
            page=search_request.page,
            page_size=search_request.page_size,
            total_pages=total_pages
        )
    
    async def get_extension_details(
        self,
        extension_name: str
    ) -> Optional[ExtensionListingSchema]:
        """Get detailed information about a specific extension."""
        extension = self.db.query(ExtensionListing).filter(
            ExtensionListing.name == extension_name
        ).first()
        
        if not extension:
            return None
        
        return ExtensionListingSchema.from_orm(extension)
    
    async def get_extension_versions(
        self,
        extension_name: str
    ) -> List[ExtensionVersionSchema]:
        """Get all versions of an extension."""
        extension = self.db.query(ExtensionListing).filter(
            ExtensionListing.name == extension_name
        ).first()
        
        if not extension:
            return []
        
        versions = self.db.query(ExtensionVersion).filter(
            ExtensionVersion.listing_id == extension.id
        ).order_by(desc(ExtensionVersion.created_at)).all()
        
        return [ExtensionVersionSchema.from_orm(version) for version in versions]
    
    # Installation and Updates
    
    async def install_extension(
        self,
        install_request: ExtensionInstallRequest,
        tenant_id: str,
        user_id: str
    ) -> ExtensionInstallResponse:
        """Install an extension for a tenant."""
        try:
            # Get extension listing
            extension = self.db.query(ExtensionListing).filter(
                ExtensionListing.name == install_request.extension_name
            ).first()
            
            if not extension:
                return ExtensionInstallResponse(
                    installation_id=0,
                    status=InstallationStatus.FAILED,
                    message=f"Extension '{install_request.extension_name}' not found"
                )
            
            # Check if already installed
            existing_installation = self.db.query(ExtensionInstallation).filter(
                and_(
                    ExtensionInstallation.listing_id == extension.id,
                    ExtensionInstallation.tenant_id == tenant_id,
                    ExtensionInstallation.status == InstallationStatus.INSTALLED
                )
            ).first()
            
            if existing_installation:
                return ExtensionInstallResponse(
                    installation_id=existing_installation.id,
                    status=InstallationStatus.INSTALLED,
                    message=f"Extension '{install_request.extension_name}' is already installed"
                )
            
            # Get target version
            target_version = await self._get_target_version(
                extension.id,
                install_request.version
            )
            
            if not target_version:
                return ExtensionInstallResponse(
                    installation_id=0,
                    status=InstallationStatus.FAILED,
                    message=f"Version '{install_request.version}' not found for extension '{install_request.extension_name}'"
                )
            
            # Resolve dependencies
            dependency_result = await self._resolve_dependencies(
                target_version,
                tenant_id
            )
            
            if not dependency_result.resolved:
                conflicts_msg = ", ".join(dependency_result.conflicts)
                missing_msg = ", ".join(dependency_result.missing)
                return ExtensionInstallResponse(
                    installation_id=0,
                    status=InstallationStatus.FAILED,
                    message=f"Dependency resolution failed. Conflicts: {conflicts_msg}. Missing: {missing_msg}"
                )
            
            # Create installation record
            installation = ExtensionInstallation(
                listing_id=extension.id,
                version_id=target_version.id,
                tenant_id=tenant_id,
                user_id=user_id,
                status=InstallationStatus.INSTALLING,
                config=install_request.config
            )
            
            self.db.add(installation)
            self.db.commit()
            
            # Perform actual installation asynchronously
            asyncio.create_task(
                self._perform_installation(installation.id)
            )
            
            return ExtensionInstallResponse(
                installation_id=installation.id,
                status=InstallationStatus.INSTALLING,
                message=f"Installation of '{install_request.extension_name}' started"
            )
            
        except Exception as e:
            logger.error(f"Error installing extension: {e}")
            return ExtensionInstallResponse(
                installation_id=0,
                status=InstallationStatus.FAILED,
                message=f"Installation failed: {str(e)}"
            )
    
    async def update_extension(
        self,
        update_request: ExtensionUpdateRequest,
        tenant_id: str,
        user_id: str
    ) -> ExtensionInstallResponse:
        """Update an installed extension."""
        try:
            # Get current installation
            installation = self.db.query(ExtensionInstallation).join(
                ExtensionListing
            ).filter(
                and_(
                    ExtensionListing.name == update_request.extension_name,
                    ExtensionInstallation.tenant_id == tenant_id,
                    ExtensionInstallation.status == InstallationStatus.INSTALLED
                )
            ).first()
            
            if not installation:
                return ExtensionInstallResponse(
                    installation_id=0,
                    status=InstallationStatus.FAILED,
                    message=f"Extension '{update_request.extension_name}' is not installed"
                )
            
            # Get target version
            target_version = await self._get_target_version(
                installation.listing_id,
                update_request.target_version
            )
            
            if not target_version:
                return ExtensionInstallResponse(
                    installation_id=installation.id,
                    status=InstallationStatus.FAILED,
                    message=f"Target version not found for extension '{update_request.extension_name}'"
                )
            
            # Check if already on target version
            if installation.version_id == target_version.id:
                return ExtensionInstallResponse(
                    installation_id=installation.id,
                    status=InstallationStatus.INSTALLED,
                    message=f"Extension '{update_request.extension_name}' is already on target version"
                )
            
            # Update installation record
            installation.version_id = target_version.id
            installation.status = InstallationStatus.UPDATING
            installation.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Perform actual update asynchronously
            asyncio.create_task(
                self._perform_update(installation.id)
            )
            
            return ExtensionInstallResponse(
                installation_id=installation.id,
                status=InstallationStatus.UPDATING,
                message=f"Update of '{update_request.extension_name}' started"
            )
            
        except Exception as e:
            logger.error(f"Error updating extension: {e}")
            return ExtensionInstallResponse(
                installation_id=0,
                status=InstallationStatus.FAILED,
                message=f"Update failed: {str(e)}"
            )
    
    async def uninstall_extension(
        self,
        extension_name: str,
        tenant_id: str,
        user_id: str
    ) -> ExtensionInstallResponse:
        """Uninstall an extension."""
        try:
            # Get current installation
            installation = self.db.query(ExtensionInstallation).join(
                ExtensionListing
            ).filter(
                and_(
                    ExtensionListing.name == extension_name,
                    ExtensionInstallation.tenant_id == tenant_id,
                    ExtensionInstallation.status == InstallationStatus.INSTALLED
                )
            ).first()
            
            if not installation:
                return ExtensionInstallResponse(
                    installation_id=0,
                    status=InstallationStatus.FAILED,
                    message=f"Extension '{extension_name}' is not installed"
                )
            
            # Update status
            installation.status = InstallationStatus.UNINSTALLING
            installation.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Perform actual uninstallation asynchronously
            asyncio.create_task(
                self._perform_uninstallation(installation.id)
            )
            
            return ExtensionInstallResponse(
                installation_id=installation.id,
                status=InstallationStatus.UNINSTALLING,
                message=f"Uninstallation of '{extension_name}' started"
            )
            
        except Exception as e:
            logger.error(f"Error uninstalling extension: {e}")
            return ExtensionInstallResponse(
                installation_id=0,
                status=InstallationStatus.FAILED,
                message=f"Uninstallation failed: {str(e)}"
            )
    
    async def get_installation_status(
        self,
        installation_id: int
    ) -> Optional[ExtensionInstallationSchema]:
        """Get the status of an installation."""
        installation = self.db.query(ExtensionInstallation).filter(
            ExtensionInstallation.id == installation_id
        ).first()
        
        if not installation:
            return None
        
        return ExtensionInstallationSchema.from_orm(installation)
    
    async def get_installed_extensions(
        self,
        tenant_id: str
    ) -> List[ExtensionInstallationSchema]:
        """Get all installed extensions for a tenant."""
        installations = self.db.query(ExtensionInstallation).filter(
            and_(
                ExtensionInstallation.tenant_id == tenant_id,
                ExtensionInstallation.status == InstallationStatus.INSTALLED
            )
        ).all()
        
        return [ExtensionInstallationSchema.from_orm(inst) for inst in installations]
    
    # Version Management and Dependency Resolution
    
    async def _get_target_version(
        self,
        listing_id: int,
        version_constraint: Optional[str] = None
    ) -> Optional[ExtensionVersion]:
        """Get the target version for installation/update."""
        query = self.db.query(ExtensionVersion).filter(
            ExtensionVersion.listing_id == listing_id
        )
        
        if version_constraint:
            # Exact version match
            version = query.filter(
                ExtensionVersion.version == version_constraint
            ).first()
            return version
        else:
            # Latest stable version
            version = query.filter(
                ExtensionVersion.is_stable == True
            ).order_by(desc(ExtensionVersion.created_at)).first()
            return version
    
    async def _resolve_dependencies(
        self,
        version: ExtensionVersion,
        tenant_id: str
    ) -> DependencyResolutionResult:
        """Resolve dependencies for an extension version."""
        dependencies = self.db.query(ExtensionDependency).filter(
            ExtensionDependency.version_id == version.id
        ).all()
        
        resolved_deps = []
        conflicts = []
        missing = []
        
        for dep in dependencies:
            if dep.dependency_type == "extension":
                # Check if extension dependency is satisfied
                result = await self._check_extension_dependency(dep, tenant_id)
                if result["satisfied"]:
                    resolved_deps.append(dep)
                elif result["conflict"]:
                    conflicts.append(f"{dep.dependency_name}: {result['message']}")
                else:
                    if not dep.is_optional:
                        missing.append(f"{dep.dependency_name} {dep.version_constraint}")
            
            elif dep.dependency_type == "plugin":
                # Check if plugin dependency is satisfied
                if self.extension_registry.is_plugin_available(dep.dependency_name):
                    resolved_deps.append(dep)
                elif not dep.is_optional:
                    missing.append(f"Plugin: {dep.dependency_name}")
            
            elif dep.dependency_type == "system_service":
                # Check if system service is available
                if await self._check_system_service(dep.dependency_name):
                    resolved_deps.append(dep)
                elif not dep.is_optional:
                    missing.append(f"System service: {dep.dependency_name}")
        
        return DependencyResolutionResult(
            resolved=len(conflicts) == 0 and len(missing) == 0,
            dependencies=[dep for dep in resolved_deps],
            conflicts=conflicts,
            missing=missing
        )
    
    async def _check_extension_dependency(
        self,
        dependency: ExtensionDependency,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Check if an extension dependency is satisfied."""
        # Get installed version of the dependency
        installation = self.db.query(ExtensionInstallation).join(
            ExtensionListing
        ).filter(
            and_(
                ExtensionListing.name == dependency.dependency_name,
                ExtensionInstallation.tenant_id == tenant_id,
                ExtensionInstallation.status == InstallationStatus.INSTALLED
            )
        ).first()
        
        if not installation:
            return {
                "satisfied": False,
                "conflict": False,
                "message": "Extension not installed"
            }
        
        # Get installed version
        installed_version = self.db.query(ExtensionVersion).filter(
            ExtensionVersion.id == installation.version_id
        ).first()
        
        if not installed_version:
            return {
                "satisfied": False,
                "conflict": True,
                "message": "Installed version not found"
            }
        
        # Check version constraint
        if dependency.version_constraint:
            try:
                if self._satisfies_version_constraint(
                    installed_version.version,
                    dependency.version_constraint
                ):
                    return {
                        "satisfied": True,
                        "conflict": False,
                        "message": "Version constraint satisfied"
                    }
                else:
                    return {
                        "satisfied": False,
                        "conflict": True,
                        "message": f"Version {installed_version.version} does not satisfy {dependency.version_constraint}"
                    }
            except Exception as e:
                return {
                    "satisfied": False,
                    "conflict": True,
                    "message": f"Invalid version constraint: {e}"
                }
        
        return {
            "satisfied": True,
            "conflict": False,
            "message": "Dependency satisfied"
        }
    
    def _satisfies_version_constraint(
        self,
        version: str,
        constraint: str
    ) -> bool:
        """Check if a version satisfies a constraint."""
        try:
            version_info = semver.VersionInfo.parse(version)
            return semver.match(version, constraint)
        except Exception:
            return False
    
    async def _check_system_service(self, service_name: str) -> bool:
        """Check if a system service is available."""
        # This would check if services like postgres, redis, etc. are available
        # For now, return True as a placeholder
        return True
    
    # Installation Implementation
    
    async def _perform_installation(self, installation_id: int) -> None:
        """Perform the actual extension installation."""
        try:
            installation = self.db.query(ExtensionInstallation).filter(
                ExtensionInstallation.id == installation_id
            ).first()
            
            if not installation:
                logger.error(f"Installation {installation_id} not found")
                return
            
            # Get extension and version info
            listing = installation.listing
            version = installation.version
            
            # Download and install the extension package
            success = await self._download_and_install_package(
                listing.name,
                version,
                installation.tenant_id,
                installation.config
            )
            
            if success:
                # Update download count
                listing.download_count += 1
                
                # Update installation status
                installation.status = InstallationStatus.INSTALLED
                installation.updated_at = datetime.utcnow()
                
                logger.info(f"Successfully installed extension {listing.name} for tenant {installation.tenant_id}")
            else:
                installation.status = InstallationStatus.FAILED
                installation.error_message = "Package installation failed"
                installation.updated_at = datetime.utcnow()
                
                logger.error(f"Failed to install extension {listing.name} for tenant {installation.tenant_id}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error during installation {installation_id}: {e}")
            # Update installation status to failed
            installation = self.db.query(ExtensionInstallation).filter(
                ExtensionInstallation.id == installation_id
            ).first()
            if installation:
                installation.status = InstallationStatus.FAILED
                installation.error_message = str(e)
                installation.updated_at = datetime.utcnow()
                self.db.commit()
    
    async def _perform_update(self, installation_id: int) -> None:
        """Perform the actual extension update."""
        try:
            installation = self.db.query(ExtensionInstallation).filter(
                ExtensionInstallation.id == installation_id
            ).first()
            
            if not installation:
                logger.error(f"Installation {installation_id} not found")
                return
            
            # Get extension and version info
            listing = installation.listing
            version = installation.version
            
            # Update the extension package
            success = await self._download_and_install_package(
                listing.name,
                version,
                installation.tenant_id,
                installation.config
            )
            
            if success:
                installation.status = InstallationStatus.INSTALLED
                installation.updated_at = datetime.utcnow()
                
                logger.info(f"Successfully updated extension {listing.name} for tenant {installation.tenant_id}")
            else:
                installation.status = InstallationStatus.FAILED
                installation.error_message = "Package update failed"
                installation.updated_at = datetime.utcnow()
                
                logger.error(f"Failed to update extension {listing.name} for tenant {installation.tenant_id}")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error during update {installation_id}: {e}")
            installation = self.db.query(ExtensionInstallation).filter(
                ExtensionInstallation.id == installation_id
            ).first()
            if installation:
                installation.status = InstallationStatus.FAILED
                installation.error_message = str(e)
                installation.updated_at = datetime.utcnow()
                self.db.commit()
    
    async def _perform_uninstallation(self, installation_id: int) -> None:
        """Perform the actual extension uninstallation."""
        try:
            installation = self.db.query(ExtensionInstallation).filter(
                ExtensionInstallation.id == installation_id
            ).first()
            
            if not installation:
                logger.error(f"Installation {installation_id} not found")
                return
            
            # Get extension info
            listing = installation.listing
            
            # Unload extension from manager
            await self.extension_manager.unload_extension(listing.name)
            
            # Remove installation record
            self.db.delete(installation)
            self.db.commit()
            
            logger.info(f"Successfully uninstalled extension {listing.name} for tenant {installation.tenant_id}")
            
        except Exception as e:
            logger.error(f"Error during uninstallation {installation_id}: {e}")
            installation = self.db.query(ExtensionInstallation).filter(
                ExtensionInstallation.id == installation_id
            ).first()
            if installation:
                installation.status = InstallationStatus.FAILED
                installation.error_message = str(e)
                installation.updated_at = datetime.utcnow()
                self.db.commit()
    
    async def _download_and_install_package(
        self,
        extension_name: str,
        version: ExtensionVersion,
        tenant_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Download and install an extension package."""
        try:
            # This would implement the actual package download and installation
            # For now, we'll simulate the process
            
            # 1. Download package from package_url
            # 2. Verify package hash
            # 3. Extract package to extensions directory
            # 4. Load extension via extension manager
            # 5. Apply configuration
            
            # Simulate installation delay
            await asyncio.sleep(2)
            
            # Load extension via manager
            await self.extension_manager.load_extension(extension_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading/installing package for {extension_name}: {e}")
            return False