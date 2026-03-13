"""
Device Verification and Fingerprinting Service.

This service provides comprehensive device verification capabilities including:
- Device fingerprinting
- Trust management
- Anomaly detection
- Device reputation scoring
"""

import asyncio
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.audit_logging import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
)

logger = get_logger(__name__)


class DeviceTrustLevel(str, Enum):
    """Device trust levels."""
    UNKNOWN = "unknown"
    UNTRUSTED = "untrusted"
    PENDING = "pending"
    TRUSTED = "trusted"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


class DeviceRisk(str, Enum):
    """Device risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DeviceFingerprint:
    """Device fingerprint data."""
    fingerprint_id: str
    user_agent: str
    screen_resolution: str = ""
    color_depth: str = ""
    timezone: str = ""
    language: str = ""
    platform: str = ""
    cookies_enabled: bool = False
    do_not_track: bool = False
    canvas_fingerprint: str = ""
    webgl_fingerprint: str = ""
    fonts: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    ip_address: str = ""
    ip_country: str = ""
    ip_isp: str = ""
    connection_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_hash(self) -> str:
        """Convert fingerprint to hash."""
        fingerprint_data = {
            "user_agent": self.user_agent,
            "screen_resolution": self.screen_resolution,
            "color_depth": self.color_depth,
            "timezone": self.timezone,
            "language": self.language,
            "platform": self.platform,
            "cookies_enabled": self.cookies_enabled,
            "do_not_track": self.do_not_track,
            "canvas_fingerprint": self.canvas_fingerprint,
            "webgl_fingerprint": self.webgl_fingerprint,
            "fonts": sorted(self.fonts),
            "plugins": sorted(self.plugins),
        }
        
        fingerprint_json = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_json.encode()).hexdigest()


@dataclass
class DeviceInfo:
    """Device information with trust and risk assessment."""
    device_id: str
    user_id: str
    fingerprint: DeviceFingerprint
    fingerprint_hash: str
    trust_level: DeviceTrustLevel = DeviceTrustLevel.UNKNOWN
    risk_level: DeviceRisk = DeviceRisk.LOW
    risk_score: float = 0.0
    is_trusted: bool = False
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    failed_attempts: int = 0
    location_changes: int = 0
    ip_changes: int = 0
    suspicious_activities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceVerificationConfig(ServiceConfig):
    """Device verification service configuration."""
    # Trust settings
    auto_trust_threshold: int = 5  # Number of successful logins to auto-trust
    max_trusted_devices: int = 5
    trust_duration_days: int = 30
    
    # Risk assessment
    risk_threshold_high: float = 0.7
    risk_threshold_medium: float = 0.4
    suspicious_activities_threshold: int = 3
    
    # Fingerprinting settings
    enable_advanced_fingerprinting: bool = True
    enable_canvas_fingerprinting: bool = True
    enable_webgl_fingerprinting: bool = True
    enable_font_detection: bool = True
    enable_plugin_detection: bool = True
    
    # Anomaly detection
    enable_location_anomaly_detection: bool = True
    enable_ip_anomaly_detection: bool = True
    enable_behavioral_anomaly_detection: bool = True
    anomaly_detection_window_hours: int = 24
    
    # Security settings
    block_suspicious_devices: bool = True
    require_verification_for_new_devices: bool = True
    device_timeout_days: int = 90
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "device_verification_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class DeviceVerificationService(BaseService):
    """
    Device Verification and Fingerprinting Service.
    
    This service provides comprehensive device verification capabilities including
    fingerprinting, trust management, and anomaly detection.
    """
    
    def __init__(self, config: Optional[DeviceVerificationConfig] = None):
        """Initialize Device Verification Service."""
        super().__init__(config or DeviceVerificationConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Database session will be injected
        self._db_session: Optional[AsyncSession] = None
        
        # Thread-safe data structures
        self._devices: Dict[str, DeviceInfo] = {}
        self._fingerprints: Dict[str, DeviceFingerprint] = {}
        self._user_devices: Dict[str, List[str]] = {}
        
        # Initialize audit logger
        self._audit_logger = get_audit_logger()
    
    async def initialize(self) -> None:
        """Initialize Device Verification Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Validate configuration
                self._validate_config()
                
                self._initialized = True
                logger.info("Device Verification Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Device Verification Service: {e}")
                raise RuntimeError(f"Device Verification Service initialization failed: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.config.auto_trust_threshold < 1:
            logger.warning("Auto-trust threshold should be at least 1")
        
        if self.config.max_trusted_devices < 1:
            logger.warning("Max trusted devices should be at least 1")
    
    def set_db_session(self, session: AsyncSession) -> None:
        """Set database session for the service."""
        self._db_session = session
    
    async def create_device_fingerprint(
        self,
        request_data: Dict[str, Any]
    ) -> DeviceFingerprint:
        """
        Create device fingerprint from request data.
        
        Args:
            request_data: Request data including headers, client info, etc.
            
        Returns:
            Device fingerprint
        """
        try:
            # Extract basic information
            user_agent = request_data.get("user_agent", "")
            ip_address = request_data.get("ip_address", "")
            
            # Extract advanced fingerprinting data if enabled
            fingerprint_data = {
                "user_agent": user_agent,
                "screen_resolution": request_data.get("screen_resolution", ""),
                "color_depth": request_data.get("color_depth", ""),
                "timezone": request_data.get("timezone", ""),
                "language": request_data.get("language", ""),
                "platform": request_data.get("platform", ""),
                "cookies_enabled": request_data.get("cookies_enabled", False),
                "do_not_track": request_data.get("do_not_track", False),
                "ip_address": ip_address,
                "ip_country": request_data.get("ip_country", ""),
                "ip_isp": request_data.get("ip_isp", ""),
                "connection_type": request_data.get("connection_type", ""),
            }
            
            # Add advanced fingerprinting data if enabled
            if self.config.enable_advanced_fingerprinting:
                if self.config.enable_canvas_fingerprinting:
                    fingerprint_data["canvas_fingerprint"] = request_data.get("canvas_fingerprint", "")
                
                if self.config.enable_webgl_fingerprinting:
                    fingerprint_data["webgl_fingerprint"] = request_data.get("webgl_fingerprint", "")
                
                if self.config.enable_font_detection:
                    fingerprint_data["fonts"] = request_data.get("fonts", [])
                
                if self.config.enable_plugin_detection:
                    fingerprint_data["plugins"] = request_data.get("plugins", [])
            
            # Create fingerprint object
            fingerprint = DeviceFingerprint(
                fingerprint_id=secrets.token_urlsafe(32),
                **fingerprint_data
            )
            
            # Store fingerprint
            self._fingerprints[fingerprint.fingerprint_id] = fingerprint
            
            logger.debug(f"Created device fingerprint: {fingerprint.fingerprint_id}")
            return fingerprint
            
        except Exception as e:
            logger.error(f"Error creating device fingerprint: {e}")
            raise
    
    async def register_device(
        self,
        user_id: str,
        fingerprint: DeviceFingerprint,
        *,
        trust_device: bool = False
    ) -> DeviceInfo:
        """
        Register a device for a user.
        
        Args:
            user_id: User ID
            fingerprint: Device fingerprint
            trust_device: Whether to automatically trust the device
            
        Returns:
            Device information
        """
        try:
            # Generate device ID
            device_id = secrets.token_urlsafe(32)
            fingerprint_hash = fingerprint.to_hash()
            
            # Check if device already exists
            existing_device = await self._get_device_by_fingerprint(fingerprint_hash)
            if existing_device and existing_device.user_id == user_id:
                # Update existing device
                existing_device.last_seen = datetime.utcnow()
                existing_device.usage_count += 1
                
                # Update device in storage
                self._devices[existing_device.device_id] = existing_device
                
                logger.info(f"Updated existing device for user {user_id}: {existing_device.device_id}")
                return existing_device
            
            # Assess device risk
            risk_score, risk_level = await self._assess_device_risk(fingerprint, user_id)
            
            # Determine trust level
            trust_level = DeviceTrustLevel.UNTRUSTED
            is_trusted = False
            
            if trust_device:
                trust_level = DeviceTrustLevel.TRUSTED
                is_trusted = True
            elif risk_score < self.config.risk_threshold_medium:
                trust_level = DeviceTrustLevel.PENDING
            
            # Create device info
            device_info = DeviceInfo(
                device_id=device_id,
                user_id=user_id,
                fingerprint=fingerprint,
                fingerprint_hash=fingerprint_hash,
                trust_level=trust_level,
                risk_level=risk_level,
                risk_score=risk_score,
                is_trusted=is_trusted,
                usage_count=1
            )
            
            # Store device
            self._devices[device_id] = device_info
            
            # Update user devices mapping
            if user_id not in self._user_devices:
                self._user_devices[user_id] = []
            self._user_devices[user_id].append(device_id)
            
            # Log device registration
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Device registered for user {user_id}",
                "user_id": user_id,
                "metadata": {
                    "device_id": device_id,
                    "trust_level": trust_level.value,
                    "risk_level": risk_level.value,
                    "risk_score": risk_score,
                    "auto_trusted": trust_device
                }
            })
            
            logger.info(f"Device registered for user {user_id}: {device_id}")
            return device_info
            
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            raise
    
    async def verify_device(
        self,
        user_id: str,
        fingerprint_hash: str,
        *,
        ip_address: str = ""
    ) -> Tuple[bool, Optional[DeviceInfo], Optional[str]]:
        """
        Verify a device for a user.
        
        Args:
            user_id: User ID
            fingerprint_hash: Device fingerprint hash
            ip_address: IP address
            
        Returns:
            Tuple of (is_valid, device_info, error_message)
        """
        try:
            # Get device by fingerprint
            device = await self._get_device_by_fingerprint(fingerprint_hash)
            
            if not device:
                return False, None, "Device not found"
            
            if device.user_id != user_id:
                return False, None, "Device not associated with user"
            
            # Check if device is blocked
            if device.trust_level == DeviceTrustLevel.BLOCKED:
                return False, device, "Device is blocked"
            
            # Check for anomalies
            anomaly_detected, anomaly_reason = await self._detect_anomalies(device, ip_address)
            
            if anomaly_detected and anomaly_reason:
                # Update suspicious activities
                device.suspicious_activities.append(anomaly_reason)
                device.risk_score = min(1.0, device.risk_score + 0.2)
                
                # Update risk level
                if device.risk_score >= self.config.risk_threshold_high:
                    device.risk_level = DeviceRisk.HIGH
                    device.trust_level = DeviceTrustLevel.SUSPICIOUS
                    
                    if self.config.block_suspicious_devices:
                        device.trust_level = DeviceTrustLevel.BLOCKED
                
                # Log anomaly
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.WARNING,
                    "message": f"Device anomaly detected: {anomaly_reason}",
                    "user_id": user_id,
                    "metadata": {
                        "device_id": device.device_id,
                        "anomaly": anomaly_reason,
                        "risk_score": device.risk_score,
                        "risk_level": device.risk_level.value
                    }
                })
                
                logger.warning(f"Device anomaly detected for user {user_id}: {anomaly_reason}")
            
            # Update device usage
            device.last_seen = datetime.utcnow()
            device.usage_count += 1
            
            # Check for auto-trust
            if (not device.is_trusted and 
                device.usage_count >= self.config.auto_trust_threshold and
                device.risk_score < self.config.risk_threshold_medium):
                
                device.trust_level = DeviceTrustLevel.TRUSTED
                device.is_trusted = True
                
                # Log device trust
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.INFO,
                    "message": f"Device auto-trusted for user {user_id}",
                    "user_id": user_id,
                    "metadata": {
                        "device_id": device.device_id,
                        "usage_count": device.usage_count,
                        "risk_score": device.risk_score
                    }
                })
                
                logger.info(f"Device auto-trusted for user {user_id}: {device.device_id}")
            
            # Update device in storage
            self._devices[device.device_id] = device
            
            is_valid = device.trust_level != DeviceTrustLevel.BLOCKED
            error_message = None if is_valid else "Device is blocked"
            
            return is_valid, device, error_message
            
        except Exception as e:
            logger.error(f"Error verifying device: {e}")
            return False, None, "Device verification error"
    
    async def trust_device(
        self,
        user_id: str,
        device_id: str,
        *,
        ip_address: str = ""
    ) -> bool:
        """
        Manually trust a device for a user.
        
        Args:
            user_id: User ID
            device_id: Device ID
            ip_address: IP address
            
        Returns:
            True if device was trusted successfully, False otherwise
        """
        try:
            # Get device
            device = self._devices.get(device_id)
            if not device:
                logger.warning(f"Device not found: {device_id}")
                return False
            
            if device.user_id != user_id:
                logger.warning(f"Device not associated with user {user_id}: {device_id}")
                return False
            
            # Check user's trusted devices limit
            trusted_devices = await self._get_trusted_devices(user_id)
            if len(trusted_devices) >= self.config.max_trusted_devices:
                logger.warning(f"User {user_id} has reached maximum trusted devices")
                return False
            
            # Trust the device
            device.trust_level = DeviceTrustLevel.TRUSTED
            device.is_trusted = True
            
            # Update device in storage
            self._devices[device_id] = device
            
            # Log device trust
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Device manually trusted for user {user_id}",
                "user_id": user_id,
                "metadata": {
                    "device_id": device_id,
                    "ip_address": ip_address
                }
            })
            
            logger.info(f"Device manually trusted for user {user_id}: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error trusting device: {e}")
            return False
    
    async def revoke_device_trust(
        self,
        user_id: str,
        device_id: str
    ) -> bool:
        """
        Revoke trust for a device.
        
        Args:
            user_id: User ID
            device_id: Device ID
            
        Returns:
            True if trust was revoked successfully, False otherwise
        """
        try:
            # Get device
            device = self._devices.get(device_id)
            if not device:
                logger.warning(f"Device not found: {device_id}")
                return False
            
            if device.user_id != user_id:
                logger.warning(f"Device not associated with user {user_id}: {device_id}")
                return False
            
            # Revoke trust
            device.trust_level = DeviceTrustLevel.UNTRUSTED
            device.is_trusted = False
            
            # Update device in storage
            self._devices[device_id] = device
            
            # Log trust revocation
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": f"Device trust revoked for user {user_id}",
                "user_id": user_id,
                "metadata": {
                    "device_id": device_id
                }
            })
            
            logger.info(f"Device trust revoked for user {user_id}: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking device trust: {e}")
            return False
    
    async def block_device(
        self,
        user_id: str,
        device_id: str,
        *,
        reason: str = ""
    ) -> bool:
        """
        Block a device for a user.
        
        Args:
            user_id: User ID
            device_id: Device ID
            reason: Reason for blocking
            
        Returns:
            True if device was blocked successfully, False otherwise
        """
        try:
            # Get device
            device = self._devices.get(device_id)
            if not device:
                logger.warning(f"Device not found: {device_id}")
                return False
            
            if device.user_id != user_id:
                logger.warning(f"Device not associated with user {user_id}: {device_id}")
                return False
            
            # Block device
            device.trust_level = DeviceTrustLevel.BLOCKED
            device.is_trusted = False
            device.risk_level = DeviceRisk.CRITICAL
            device.risk_score = 1.0
            
            # Add reason to suspicious activities
            if reason:
                device.suspicious_activities.append(f"Blocked: {reason}")
            
            # Update device in storage
            self._devices[device_id] = device
            
            # Log device block
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.WARNING,
                "message": f"Device blocked for user {user_id}",
                "user_id": user_id,
                "metadata": {
                    "device_id": device_id,
                    "reason": reason
                }
            })
            
            logger.warning(f"Device blocked for user {user_id}: {device_id} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error blocking device: {e}")
            return False
    
    async def get_user_devices(
        self,
        user_id: str,
        *,
        include_blocked: bool = False
    ) -> List[DeviceInfo]:
        """
        Get all devices for a user.
        
        Args:
            user_id: User ID
            include_blocked: Whether to include blocked devices
            
        Returns:
            List of device information
        """
        try:
            device_ids = self._user_devices.get(user_id, [])
            devices = []
            
            for device_id in device_ids:
                device = self._devices.get(device_id)
                if device and (include_blocked or device.trust_level != DeviceTrustLevel.BLOCKED):
                    devices.append(device)
            
            return devices
            
        except Exception as e:
            logger.error(f"Error getting user devices: {e}")
            return []
    
    async def get_device_by_id(self, device_id: str) -> Optional[DeviceInfo]:
        """
        Get device information by ID.
        
        Args:
            device_id: Device ID
            
        Returns:
            Device information or None if not found
        """
        return self._devices.get(device_id)
    
    async def _get_device_by_fingerprint(self, fingerprint_hash: str) -> Optional[DeviceInfo]:
        """Get device by fingerprint hash."""
        for device in self._devices.values():
            if device.fingerprint_hash == fingerprint_hash:
                return device
        return None
    
    async def _get_trusted_devices(self, user_id: str) -> List[DeviceInfo]:
        """Get trusted devices for a user."""
        device_ids = self._user_devices.get(user_id, [])
        trusted_devices = []
        
        for device_id in device_ids:
            device = self._devices.get(device_id)
            if device and device.is_trusted:
                trusted_devices.append(device)
        
        return trusted_devices
    
    async def _assess_device_risk(
        self,
        fingerprint: DeviceFingerprint,
        user_id: str
    ) -> Tuple[float, DeviceRisk]:
        """
        Assess device risk based on fingerprint and user history.
        
        Args:
            fingerprint: Device fingerprint
            user_id: User ID
            
        Returns:
            Tuple of (risk_score, risk_level)
        """
        try:
            risk_score = 0.0
            
            # Check for known suspicious indicators
            if not fingerprint.cookies_enabled:
                risk_score += 0.1
            
            if fingerprint.do_not_track:
                risk_score += 0.05
            
            # Check user agent for suspicious patterns
            user_agent = fingerprint.user_agent.lower()
            if any(bot in user_agent for bot in ["bot", "crawler", "spider", "scraper"]):
                risk_score += 0.3
            
            # Check IP geolocation if available
            if self.config.enable_location_anomaly_detection:
                # This would compare with user's typical locations
                pass
            
            # Cap risk score at 1.0
            risk_score = min(1.0, risk_score)
            
            # Determine risk level
            if risk_score >= self.config.risk_threshold_high:
                risk_level = DeviceRisk.HIGH
            elif risk_score >= self.config.risk_threshold_medium:
                risk_level = DeviceRisk.MEDIUM
            else:
                risk_level = DeviceRisk.LOW
            
            return risk_score, risk_level
            
        except Exception as e:
            logger.error(f"Error assessing device risk: {e}")
            return 0.5, DeviceRisk.MEDIUM
    
    async def _detect_anomalies(
        self,
        device: DeviceInfo,
        current_ip: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect anomalies in device usage.
        
        Args:
            device: Device information
            current_ip: Current IP address
            
        Returns:
            Tuple of (anomaly_detected, anomaly_reason)
        """
        try:
            # Check IP changes
            if self.config.enable_ip_anomaly_detection:
                if current_ip and current_ip != device.fingerprint.ip_address:
                    device.ip_changes += 1
                    
                    # If too many IP changes, flag as anomaly
                    if device.ip_changes > 3:
                        return True, "Multiple IP changes detected"
            
            # Check for suspicious activities
            if len(device.suspicious_activities) >= self.config.suspicious_activities_threshold:
                return True, "Multiple suspicious activities detected"
            
            # Check behavioral anomalies if enabled
            if self.config.enable_behavioral_anomaly_detection:
                # This would analyze usage patterns, timing, etc.
                pass
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return False, None
    
    async def health_check(self) -> bool:
        """Check the health of the Device Verification Service."""
        if not self._initialized:
            return False
        
        try:
            # Test fingerprint creation
            test_fingerprint = DeviceFingerprint(
                fingerprint_id=secrets.token_urlsafe(32),
                user_agent="test-agent",
                ip_address="127.0.0.1"
            )
            
            # Test hash generation
            hash_value = test_fingerprint.to_hash()
            if not hash_value:
                return False
            
            # Test device registration
            test_device = DeviceInfo(
                device_id=secrets.token_urlsafe(32),
                user_id="test-user",
                fingerprint=test_fingerprint,
                fingerprint_hash=hash_value
            )
            
            if not test_device.device_id:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Device Verification Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Device Verification Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Device Verification Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Device Verification Service."""
        if not self._initialized:
            return
        
        # Clear data structures
        self._devices.clear()
        self._fingerprints.clear()
        self._user_devices.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Device Verification Service stopped successfully")


__all__ = [
    "DeviceVerificationService",
    "DeviceVerificationConfig",
    "DeviceFingerprint",
    "DeviceInfo",
    "DeviceTrustLevel",
    "DeviceRisk",
]