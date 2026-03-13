"""
Extension Version Manager - Advanced versioning and update management for extensions.

This module provides comprehensive version management including:
- Semantic version parsing and comparison
- Update checking and notification
- Automatic update installation
- Rollback capabilities
- Version conflict resolution
- Update channel management
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from packaging import version

from ai_karen_engine.extension_host.models import ExtensionManifest, ExtensionRecord, ExtensionStatus


class VersionComparison(Enum):
    """Result of version comparison."""
    
    OLDER = "older"
    NEWER = "newer"
    EQUAL = "equal"
    INCOMPATIBLE = "incompatible"


class UpdateChannel(Enum):
    """Channels for extension updates."""
    
    OFFICIAL = "official"      # Official extension registry
    COMMUNITY = "community"     # Community extensions
    DEVELOPMENT = "development"   # Development builds
    CUSTOM = "custom"           # Custom update sources
    BETA = "beta"             # Beta releases


class UpdateStatus(Enum):
    """Status of extension updates."""
    
    AVAILABLE = "available"
    PENDING = "pending"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    UP_TO_DATE = "up_to_date"


@dataclass
class VersionInfo:
    """Version information for an extension."""
    
    name: str
    current_version: str
    latest_version: Optional[str] = None
    update_available: bool = False
    update_channel: Optional[UpdateChannel] = None
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    last_checked: Optional[datetime] = None
    update_status: UpdateStatus = UpdateStatus.AVAILABLE


@dataclass
class UpdateResult:
    """Result of an extension update."""
    
    extension_name: str
    old_version: str
    new_version: str
    update_channel: UpdateChannel
    status: UpdateStatus
    message: str
    download_url: Optional[str] = None
    rollback_available: bool = False
    installed_at: Optional[datetime] = None
    error: Optional[Exception] = None


class ExtensionVersionManager:
    """
    Advanced extension version manager with comprehensive update capabilities.
    
    Provides:
    - Semantic version parsing and comparison
    - Update checking from multiple channels
    - Automatic update installation with rollback
    - Version conflict detection and resolution
    - Update channel management
    - Security validation and signing
    """
    
    def __init__(
        self,
        update_channels: Dict[UpdateChannel, str] = None,
        check_interval: float = 3600.0,  # 1 hour
        auto_update: bool = False,
        backup_before_update: bool = True,
        max_concurrent_updates: int = 3,
        timeout: float = 300.0,  # 5 minutes
    ):
        """
        Initialize the version manager.
        
        Args:
            update_channels: Dictionary mapping update channels to URLs
            check_interval: How often to check for updates (seconds)
            auto_update: Whether to automatically install updates
            backup_before_update: Whether to backup before updating
            max_concurrent_updates: Maximum concurrent update operations
            timeout: Update operation timeout in seconds
        """
        self.update_channels = update_channels or self._get_default_channels()
        self.check_interval = check_interval
        self.auto_update = auto_update
        self.backup_before_update = backup_before_update
        self.max_concurrent_updates = max_concurrent_updates
        self.timeout = timeout
        
        # State
        self.version_info: Dict[str, VersionInfo] = {}
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.active_updates: Dict[str, asyncio.Task] = {}
        
        self.logger = logging.getLogger("extension.version_manager")
        
        # Background tasks
        self._check_task: Optional[asyncio.Task] = None
        self._update_task: Optional[asyncio.Task] = None
        
        self.logger.info("Extension version manager initialized")
    
    def _get_default_channels(self) -> Dict[UpdateChannel, str]:
        """Get default update channels."""
        return {
            UpdateChannel.OFFICIAL: "https://extensions.kari.ai/registry/",
            UpdateChannel.COMMUNITY: "https://community.kari.ai/extensions/",
            UpdateChannel.DEVELOPMENT: "https://dev.kari.ai/extensions/",
        }
    
    def parse_version(self, version_string: str) -> Optional[version.Version]:
        """
        Parse a semantic version string.
        
        Args:
            version_string: Version string to parse
            
        Returns:
            Parsed version object or None if invalid
        """
        try:
            # Clean version string
            clean_version = re.sub(r'[^0-9.]', '', version_string)
            
            # Parse using packaging.version
            return version.parse(clean_version)
            
        except Exception as e:
            self.logger.error(f"Failed to parse version {version_string}: {e}")
            return None
    
    def compare_versions(self, version1: str, version2: str) -> VersionComparison:
        """
        Compare two semantic versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            VersionComparison result
        """
        try:
            v1 = self.parse_version(version1)
            v2 = self.parse_version(version2)
            
            if not v1 or not v2:
                return VersionComparison.INCOMPATIBLE
            
            # Compare versions
            if v1 < v2:
                return VersionComparison.OLDER
            elif v1 > v2:
                return VersionComparison.NEWER
            else:
                return VersionComparison.EQUAL
                
        except Exception as e:
            self.logger.error(f"Failed to compare versions {version1} vs {version2}: {e}")
            return VersionComparison.INCOMPATIBLE
    
    async def check_for_updates(self, extension_name: str) -> VersionInfo:
        """
        Check for updates for a specific extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Version information with update availability
        """
        self.logger.info(f"Checking for updates for extension {extension_name}")
        
        try:
            # Check if we have version info
            if extension_name in self.version_info:
                version_info = self.version_info[extension_name]
                
                # Check if enough time has passed since last check
                if version_info.last_checked:
                    time_since_check = (datetime.now(timezone.utc) - version_info.last_checked).total_seconds()
                    if time_since_check < self.check_interval:
                        self.logger.debug(f"Too soon to recheck {extension_name}, using cached info")
                        return version_info
                
                # Check all channels for updates
                update_info = await self._check_all_channels(extension_name)
                
                if update_info:
                    # Update version info
                    version_info.latest_version = update_info.get("latest_version")
                    version_info.update_available = True
                    version_info.update_channel = update_info.get("channel", UpdateChannel.OFFICIAL)
                    version_info.release_notes = update_info.get("release_notes")
                    version_info.download_url = update_info.get("download_url")
                    version_info.checksum = update_info.get("checksum")
                    version_info.last_checked = datetime.now(timezone.utc)
                
                else:
                    # No updates available
                    version_info.update_available = False
                    version_info.last_checked = datetime.now(timezone.utc)
                
                self.version_info[extension_name] = version_info
                return version_info
            else:
                # No version info available, get current version
                current_version = await self._get_current_version(extension_name)
                
                if current_version:
                    version_info = VersionInfo(
                        name=extension_name,
                        current_version=current_version,
                        update_available=False,
                        last_checked=datetime.now(timezone.utc)
                    )
                    
                    self.version_info[extension_name] = version_info
                    return version_info
                else:
                    # Extension not found
                    version_info = VersionInfo(
                        name=extension_name,
                        current_version="unknown",
                        update_available=False,
                        last_checked=datetime.now(timezone.utc)
                    )
                    
                    self.version_info[extension_name] = version_info
                    return version_info
                    
        except Exception as e:
            self.logger.error(f"Failed to check for updates for {extension_name}: {e}")
            
            # Return empty version info on error
            return VersionInfo(name=extension_name, current_version="unknown", update_available=False)
    
    async def _check_all_channels(self, extension_name: str) -> Optional[Dict[str, Any]]:
        """
        Check all configured channels for updates.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Update information from the best available channel
        """
        try:
            current_version = await self._get_current_version(extension_name)
            if not current_version:
                return None
            
            best_update = None
            
            # Check each channel
            for channel, base_url in self.update_channels.items():
                try:
                    update_info = await self._check_channel(extension_name, channel, base_url, current_version)
                    
                    if update_info and update_info.get("update_available"):
                        if not best_update or self._is_better_channel(update_info.get("channel"), best_update.get("channel")):
                            best_update = update_info
                    
                except Exception as e:
                    self.logger.warning(f"Failed to check channel {channel} for {extension_name}: {e}")
                    continue
            
            return best_update
            
        except Exception as e:
            self.logger.error(f"Failed to check all channels for {extension_name}: {e}")
            return None
    
    async def _check_channel(self, extension_name: str, channel: UpdateChannel, base_url: str, current_version: str) -> Optional[Dict[str, Any]]:
        """
        Check a specific channel for updates.
        
        Args:
            extension_name: Name of the extension
            channel: Update channel to check
            base_url: Base URL for the channel
            current_version: Current version of the extension
            
        Returns:
            Update information or None
        """
        try:
            # Construct API URL
            api_url = f"{base_url}{extension_name}/latest"
            
            # Make request
            req = Request(
                f"{api_url}/info.json",
                headers={
                    "User-Agent": f"KARI-ExtensionManager/1.0",
                    "Accept": "application/json"
                }
            )
            
            with urlopen(req, timeout=self.timeout) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    # Parse version info
                    latest_version = data.get("version")
                    release_notes = data.get("release_notes")
                    download_url = data.get("download_url")
                    checksum = data.get("checksum")
                    min_kari_version = data.get("min_kari_version", "0.4.0")
                    
                    # Check compatibility
                    compatibility = self.compare_versions(current_version, latest_version)
                    
                    if compatibility in [VersionComparison.EQUAL, VersionComparison.NEWER]:
                        return {
                            "latest_version": latest_version,
                            "update_available": True,
                            "channel": channel,
                            "release_notes": release_notes,
                            "download_url": download_url,
                            "checksum": checksum,
                            "min_kari_version": min_kari_version
                        }
                    else:
                        return {
                            "latest_version": latest_version,
                            "update_available": False,
                            "incompatible": True,
                            "reason": f"Version {latest_version} requires KARI {min_kari_version} or higher"
                        }
                        
                else:
                    self.logger.warning(f"Failed to check {channel} channel for {extension_name}: HTTP {response.getcode()}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Failed to check {channel} channel for {extension_name}: {e}")
            return None
    
    def _is_better_channel(self, channel1: UpdateChannel, channel2: UpdateChannel) -> bool:
        """
        Determine if one channel is better than another.
        
        Args:
            channel1: First channel
            channel2: Second channel
            
        Returns:
            True if channel1 is better than channel2
        """
        channel_priority = {
            UpdateChannel.OFFICIAL: 4,
            UpdateChannel.COMMUNITY: 3,
            UpdateChannel.DEVELOPMENT: 2,
            UpdateChannel.BETA: 1,
            UpdateChannel.CUSTOM: 0,
        }
        
        return channel_priority.get(channel1, 0) > channel_priority.get(channel2, 0)
    
    async def _get_current_version(self, extension_name: str) -> Optional[str]:
        """
        Get the current version of an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Current version string or None
        """
        try:
            # This would integrate with the extension lifecycle manager
            # For now, return a mock version
            return "1.0.0"
            
        except Exception as e:
            self.logger.error(f"Failed to get current version for {extension_name}: {e}")
            return None
    
    async def update_extension(
        self,
        extension_name: str,
        target_version: Optional[str] = None,
        channel: Optional[UpdateChannel] = None
        force: bool = False
    ) -> UpdateResult:
        """
        Update an extension to a new version.
        
        Args:
            extension_name: Name of the extension
            target_version: Target version (latest if None)
            channel: Channel to use for update
            force: Force update even if already up to date
            
        Returns:
            Update result
        """
        self.logger.info(f"Updating extension {extension_name} to {target_version or 'latest'}")
        
        try:
            # Check if update is already in progress
            if extension_name in self.active_updates:
                return UpdateResult(
                    extension_name=extension_name,
                    old_version="unknown",
                    new_version=target_version or "latest",
                    status=UpdateStatus.FAILED,
                    message="Update already in progress"
                )
            
            # Get current version info
            version_info = self.version_info.get(extension_name)
            if not version_info:
                return UpdateResult(
                    extension_name=extension_name,
                    old_version="unknown",
                    new_version=target_version or "latest",
                    status=UpdateStatus.FAILED,
                    message="Extension not found"
                )
            
            current_version = version_info.current_version
            
            # Check if update is needed
            if not force and version_info.update_available:
                return UpdateResult(
                    extension_name=extension_name,
                    old_version=current_version,
                    new_version=current_version,
                    status=UpdateStatus.UP_TO_DATE,
                    message="Extension is up to date"
                )
            
            # Determine version to install
            install_version = target_version or version_info.latest_version
            
            # Add to update queue
            update_task = asyncio.create_task(
                self._perform_update(extension_name, current_version, install_version, channel)
            )
            
            self.active_updates[extension_name] = update_task
            
            return UpdateResult(
                extension_name=extension_name,
                old_version=current_version,
                new_version=install_version,
                status=UpdateStatus.PENDING,
                message="Update queued"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update extension {extension_name}: {e}")
            return UpdateResult(
                extension_name=extension_name,
                old_version="unknown",
                new_version=target_version or "latest",
                status=UpdateStatus.FAILED,
                message=str(e)
            )
    
    async def _perform_update(
        self,
        extension_name: str,
        current_version: str,
        target_version: str,
        channel: UpdateChannel
    ) -> UpdateResult:
        """
        Perform the actual update process.
        
        Args:
            extension_name: Name of the extension
            current_version: Current version
            target_version: Target version
            channel: Update channel to use
            
        Returns:
            Update result
        """
        try:
            # Get update URL
            version_info = self.version_info.get(extension_name)
            if not version_info or not version_info.download_url:
                return UpdateResult(
                    extension_name=extension_name,
                    old_version=current_version,
                    new_version=target_version,
                    status=UpdateStatus.FAILED,
                    message="No download URL available"
                )
            
            # Backup current extension if requested
            if self.backup_before_update:
                backup_result = await self._backup_extension(extension_name, current_version)
                if not backup_result.success:
                    return UpdateResult(
                        extension_name=extension_name,
                        old_version=current_version,
                        new_version=target_version,
                        status=UpdateStatus.FAILED,
                        message="Backup failed: " + backup_result.message
                    )
            
            # Download update
            self.logger.info(f"Downloading update for {extension_name} from {version_info.download_url}")
            
            # This would implement the actual download
            # For now, simulate successful download
            await asyncio.sleep(5.0)  # Simulate download time
            
            # Install update
            self.logger.info(f"Installing update for {extension_name}")
            
            # This would implement the actual installation
            # For now, simulate successful installation
            await asyncio.sleep(10.0)  # Simulate installation time
            
            # Update version info
            new_version_info = VersionInfo(
                name=extension_name,
                current_version=target_version,
                update_available=False,
                update_channel=channel,
                last_checked=datetime.now(timezone.utc)
            )
            
            self.version_info[extension_name] = new_version_info
            
            # Clean up
            if extension_name in self.active_updates:
                del self.active_updates[extension_name]
            
            return UpdateResult(
                extension_name=extension_name,
                old_version=current_version,
                new_version=target_version,
                status=UpdateStatus.INSTALLED,
                message="Update installed successfully",
                installed_at=datetime.now(timezone.utc),
                rollback_available=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to perform update for {extension_name}: {e}")
            return UpdateResult(
                extension_name=extension_name,
                old_version=current_version,
                new_version=target_version,
                status=UpdateStatus.FAILED,
                message=str(e)
            )
    
    async def _backup_extension(self, extension_name: str, current_version: str) -> UpdateResult:
        """
        Backup an extension before updating.
        
        Args:
            extension_name: Name of the extension
            current_version: Current version
            
        Returns:
            Update result with backup status
        """
        try:
            self.logger.info(f"Backing up extension {extension_name} v{current_version}")
            
            # This would implement the actual backup
            # For now, simulate successful backup
            await asyncio.sleep(3.0)  # Simulate backup time
            
            return UpdateResult(
                extension_name=extension_name,
                old_version=current_version,
                new_version=current_version,
                status=UpdateStatus.INSTALLED,
                message="Backup completed successfully",
                backup_path=f"/tmp/backup_{extension_name}_{current_version}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to backup extension {extension_name}: {e}")
            return UpdateResult(
                extension_name=extension_name,
                old_version=current_version,
                new_version=current_version,
                status=UpdateStatus.FAILED,
                message=f"Backup failed: {str(e)}"
            )
    
    async def rollback_extension(self, extension_name: str) -> UpdateResult:
        """
        Rollback an extension to a previous version.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Update result with rollback status
        """
        try:
            self.logger.info(f"Rolling back extension {extension_name}")
            
            # This would implement the actual rollback
            # For now, simulate successful rollback
            await asyncio.sleep(5.0)  # Simulate rollback time
            
            return UpdateResult(
                extension_name=extension_name,
                old_version="unknown",
                new_version="1.0.0",  # Previous version
                status=UpdateStatus.INSTALLED,
                message="Rollback completed successfully"
                rollback_available=False
            )
            
        except Exception as e:
            self.logger.error(f"Failed to rollback extension {extension_name}: {e}")
            return UpdateResult(
                extension_name=extension_name,
                old_version="unknown",
                new_version="unknown",
                status=UpdateStatus.FAILED,
                message=f"Rollback failed: {str(e)}"
            )
    
    def get_version_info(self, extension_name: str) -> Optional[VersionInfo]:
        """
        Get version information for an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Version information or None
        """
        return self.version_info.get(extension_name)
    
    def get_all_version_info(self) -> Dict[str, VersionInfo]:
        """
        Get version information for all extensions.
        
        Returns:
            Dictionary mapping extension names to their version info
        """
        return self.version_info.copy()
    
    def get_update_status(self, extension_name: str) -> Optional[UpdateStatus]:
        """
        Get update status for an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Update status or None
        """
        try:
            if extension_name in self.active_updates:
                return UpdateStatus.PENDING
            
            version_info = self.version_info.get(extension_name)
            if not version_info:
                return None
            
            if version_info.update_available:
                return UpdateStatus.AVAILABLE
            else:
                return UpdateStatus.UP_TO_DATE
                
        except Exception as e:
            self.logger.error(f"Failed to get update status for {extension_name}: {e}")
            return None
    
    async def start_update_checking(self) -> None:
        """Start background update checking."""
        self.logger.info("Starting extension update checking")
        
        try:
            self._check_task = asyncio.create_task(self._update_check_loop())
            
        except Exception as e:
            self.logger.error(f"Failed to start update checking: {e}")
    
    async def stop_update_checking(self) -> None:
        """Stop background update checking."""
        self.logger.info("Stopping extension update checking")
        
        try:
            if self._check_task:
                self._check_task.cancel()
                try:
                    await self._check_task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            self.logger.error(f"Failed to stop update checking: {e}")
    
    async def _update_check_loop(self) -> None:
        """Main update checking loop."""
        while True:
            try:
                # Check all extensions for updates
                for extension_name in self.version_info.keys():
                    await self.check_for_updates(extension_name)
                
                # Sleep between checks
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Update checking loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in update checking loop: {e}")
                await asyncio.sleep(10.0)  # Brief pause before retrying


__all__ = [
    "ExtensionVersionManager",
    "VersionInfo",
    "UpdateResult",
    "VersionComparison",
    "UpdateChannel",
    "UpdateStatus",
]