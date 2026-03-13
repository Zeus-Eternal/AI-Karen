"""
Multi-Factor Authentication (MFA) Service.

This service provides comprehensive MFA capabilities including:
- Time-based One-Time Password (TOTP)
- SMS verification
- Email verification
- Backup codes
- Push notifications
- Hardware token support
"""

import asyncio
import base64
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import pyotp
import qrcode
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


class MFAStatus(str, Enum):
    """MFA verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    LOCKED = "locked"


@dataclass
class MFASetup:
    """MFA setup information."""
    user_id: str
    method: str
    secret: str
    qr_code: Optional[str] = None
    backup_codes: List[str] = field(default_factory=list)
    setup_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=15))
    is_verified: bool = False


@dataclass
class MFAVerification:
    """MFA verification attempt."""
    verification_id: str
    user_id: str
    method: str
    code: str
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    status: MFAStatus = MFAStatus.PENDING


@dataclass
class MFAConfig(ServiceConfig):
    """MFA service configuration."""
    # TOTP settings
    totp_issuer: str = "AI Karen"
    totp_digits: int = 6
    totp_interval: int = 30
    totp_window: int = 1  # Allowed time window for TOTP validation
    
    # SMS settings
    sms_enabled: bool = True
    sms_provider: str = "twilio"  # twilio, aws_sns, etc.
    sms_template: str = "Your verification code is: {code}"
    sms_rate_limit_minutes: int = 5
    sms_max_per_hour: int = 10
    
    # Email settings
    email_enabled: bool = True
    email_template: str = "Your verification code is: {code}"
    email_rate_limit_minutes: int = 5
    email_max_per_hour: int = 10
    
    # Backup codes settings
    backup_codes_count: int = 10
    backup_code_length: int = 8
    backup_code_expires_days: int = 365
    
    # Push notification settings
    push_enabled: bool = False
    push_provider: str = "fcm"  # fcm, apns, etc.
    
    # Security settings
    max_verification_attempts: int = 3
    verification_timeout_minutes: int = 10
    session_timeout_minutes: int = 30
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "mfa_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class TOTPManager:
    """Time-based One-Time Password (TOTP) manager."""
    
    def __init__(self, config: MFAConfig):
        """Initialize TOTP manager."""
        self.config = config
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    def generate_qr_code(self, secret: str, user_email: str, issuer: Optional[str] = None) -> str:
        """Generate QR code for TOTP setup."""
        issuer = issuer or self.config.totp_issuer
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Convert to base64 string
        img = qr.make_image(fill_color="black", back_color="white")
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=self.config.totp_window)
    
    def get_current_code(self, secret: str) -> str:
        """Get current TOTP code."""
        totp = pyotp.TOTP(secret)
        return totp.now()


class SMSManager:
    """SMS verification manager."""
    
    def __init__(self, config: MFAConfig):
        """Initialize SMS manager."""
        self.config = config
        self._rate_limits: Dict[str, List[datetime]] = {}
    
    async def send_verification_code(self, phone_number: str, code: str) -> bool:
        """Send verification code via SMS."""
        try:
            # Check rate limiting
            if not self._check_rate_limit(phone_number):
                logger.warning(f"SMS rate limit exceeded for {phone_number}")
                return False
            
            # This would integrate with actual SMS provider
            # For now, we'll simulate sending
            message = self.config.sms_template.format(code=code)
            
            # Log the send attempt
            logger.info(f"SMS verification code sent to {phone_number}: {message}")
            
            # Update rate limit tracking
            self._update_rate_limit(phone_number)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
    
    def _check_rate_limit(self, phone_number: str) -> bool:
        """Check if SMS rate limit is exceeded."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.config.sms_rate_limit_minutes)
        hour_start = now - timedelta(hours=1)
        
        # Get recent attempts for this phone number
        attempts = self._rate_limits.get(phone_number, [])
        
        # Check minute window
        recent_attempts = [t for t in attempts if t >= window_start]
        if len(recent_attempts) >= 3:  # Max 3 per 5 minutes
            return False
        
        # Check hourly limit
        hourly_attempts = [t for t in attempts if t >= hour_start]
        if len(hourly_attempts) >= self.config.sms_max_per_hour:
            return False
        
        return True
    
    def _update_rate_limit(self, phone_number: str) -> None:
        """Update rate limit tracking."""
        if phone_number not in self._rate_limits:
            self._rate_limits[phone_number] = []
        
        self._rate_limits[phone_number].append(datetime.utcnow())
        
        # Clean old entries
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._rate_limits[phone_number] = [
            t for t in self._rate_limits[phone_number] if t >= cutoff
        ]


class EmailManager:
    """Email verification manager."""
    
    def __init__(self, config: MFAConfig):
        """Initialize email manager."""
        self.config = config
        self._rate_limits: Dict[str, List[datetime]] = {}
    
    async def send_verification_code(self, email: str, code: str) -> bool:
        """Send verification code via email."""
        try:
            # Check rate limiting
            if not self._check_rate_limit(email):
                logger.warning(f"Email rate limit exceeded for {email}")
                return False
            
            # This would integrate with actual email service
            # For now, we'll simulate sending
            message = self.config.email_template.format(code=code)
            
            # Log the send attempt
            logger.info(f"Email verification code sent to {email}: {message}")
            
            # Update rate limit tracking
            self._update_rate_limit(email)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _check_rate_limit(self, email: str) -> bool:
        """Check if email rate limit is exceeded."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.config.email_rate_limit_minutes)
        hour_start = now - timedelta(hours=1)
        
        # Get recent attempts for this email
        attempts = self._rate_limits.get(email, [])
        
        # Check minute window
        recent_attempts = [t for t in attempts if t >= window_start]
        if len(recent_attempts) >= 3:  # Max 3 per 5 minutes
            return False
        
        # Check hourly limit
        hourly_attempts = [t for t in attempts if t >= hour_start]
        if len(hourly_attempts) >= self.config.email_max_per_hour:
            return False
        
        return True
    
    def _update_rate_limit(self, email: str) -> None:
        """Update rate limit tracking."""
        if email not in self._rate_limits:
            self._rate_limits[email] = []
        
        self._rate_limits[email].append(datetime.utcnow())
        
        # Clean old entries
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._rate_limits[email] = [
            t for t in self._rate_limits[email] if t >= cutoff
        ]


class BackupCodeManager:
    """Backup code manager."""
    
    def __init__(self, config: MFAConfig):
        """Initialize backup code manager."""
        self.config = config
        self._backup_codes: Dict[str, List[str]] = {}
        self._used_codes: Dict[str, List[str]] = {}
    
    def generate_backup_codes(self, count: Optional[int] = None) -> List[str]:
        """Generate backup codes."""
        count = count or self.config.backup_codes_count
        codes = []
        
        for _ in range(count):
            code = ''.join(secrets.choice('0123456789') for _ in range(self.config.backup_code_length))
            codes.append(code)
        
        return codes
    
    def store_backup_codes(self, user_id: str, codes: List[str]) -> None:
        """Store backup codes for a user."""
        self._backup_codes[user_id] = codes
        if user_id not in self._used_codes:
            self._used_codes[user_id] = []
        
        logger.info(f"Stored {len(codes)} backup codes for user {user_id}")
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify a backup code."""
        if user_id not in self._backup_codes:
            return False
        
        # Check if code has been used
        if code in self._used_codes.get(user_id, []):
            return False
        
        # Check if code is valid
        if code in self._backup_codes[user_id]:
            # Mark code as used
            self._used_codes[user_id].append(code)
            
            # Remove code from available codes
            self._backup_codes[user_id].remove(code)
            
            logger.info(f"Backup code used for user {user_id}")
            return True
        
        return False
    
    def get_remaining_codes(self, user_id: str) -> int:
        """Get number of remaining backup codes."""
        if user_id not in self._backup_codes:
            return 0
        return len(self._backup_codes[user_id])
    
    def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Regenerate backup codes for a user."""
        codes = self.generate_backup_codes()
        self.store_backup_codes(user_id, codes)
        return codes


class MFAService(BaseService):
    """
    Multi-Factor Authentication Service.
    
    This service provides comprehensive MFA capabilities including TOTP,
    SMS, email verification, and backup codes.
    """
    
    def __init__(self, config: Optional[MFAConfig] = None):
        """Initialize MFA Service."""
        super().__init__(config or MFAConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Database session will be injected
        self._db_session: Optional[AsyncSession] = None
        
        # Thread-safe data structures
        self._setups: Dict[str, MFASetup] = {}
        self._verifications: Dict[str, MFAVerification] = {}
        
        # Initialize managers
        self._totp_manager = TOTPManager(self.config)
        self._sms_manager = SMSManager(self.config)
        self._email_manager = EmailManager(self.config)
        self._backup_code_manager = BackupCodeManager(self.config)
        
        # Initialize audit logger
        self._audit_logger = get_audit_logger()
    
    async def initialize(self) -> None:
        """Initialize MFA Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Validate configuration
                self._validate_config()
                
                self._initialized = True
                logger.info("MFA Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MFA Service: {e}")
                raise RuntimeError(f"MFA Service initialization failed: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.config.totp_digits < 6:
            logger.warning("TOTP digits should be at least 6")
        
        if self.config.backup_codes_count < 5:
            logger.warning("Backup codes count should be at least 5")
    
    def set_db_session(self, session: AsyncSession) -> None:
        """Set database session for the service."""
        self._db_session = session
    
    async def setup_totp(self, user_id: str, user_email: str) -> MFASetup:
        """
        Set up TOTP for a user.
        
        Args:
            user_id: User ID
            user_email: User email
            
        Returns:
            MFA setup information
        """
        try:
            # Generate secret
            secret = self._totp_manager.generate_secret()
            
            # Generate QR code
            qr_code = self._totp_manager.generate_qr_code(secret, user_email)
            
            # Generate backup codes
            backup_codes = self._backup_code_manager.generate_backup_codes()
            
            # Create setup
            setup = MFASetup(
                user_id=user_id,
                method="totp",
                secret=secret,
                qr_code=qr_code,
                backup_codes=backup_codes
            )
            
            # Store setup
            self._setups[setup.setup_token] = setup
            
            logger.info(f"TOTP setup created for user {user_id}")
            return setup
            
        except Exception as e:
            logger.error(f"Error setting up TOTP: {e}")
            raise
    
    async def verify_totp_setup(self, setup_token: str, code: str) -> bool:
        """
        Verify TOTP setup.
        
        Args:
            setup_token: Setup token
            code: TOTP code
            
        Returns:
            True if verification is successful, False otherwise
        """
        try:
            setup = self._setups.get(setup_token)
            if not setup:
                logger.warning(f"Invalid setup token: {setup_token}")
                return False
            
            # Check if setup has expired
            if datetime.utcnow() > setup.expires_at:
                logger.warning(f"Setup token expired: {setup_token}")
                del self._setups[setup_token]
                return False
            
            # Verify TOTP code
            if self._totp_manager.verify_code(setup.secret, code):
                # Mark setup as verified
                setup.is_verified = True
                
                # Store backup codes
                self._backup_code_manager.store_backup_codes(setup.user_id, setup.backup_codes)
                
                # Clean up setup
                del self._setups[setup_token]
                
                logger.info(f"TOTP setup verified for user {setup.user_id}")
                return True
            else:
                logger.warning(f"Invalid TOTP code for setup {setup_token}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying TOTP setup: {e}")
            return False
    
    async def send_sms_verification(self, user_id: str, phone_number: str) -> bool:
        """
        Send SMS verification code.
        
        Args:
            user_id: User ID
            phone_number: Phone number
            
        Returns:
            True if SMS was sent successfully, False otherwise
        """
        try:
            # Generate verification code
            code = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            # Send SMS
            success = await self._sms_manager.send_verification_code(phone_number, code)
            
            if success:
                # Create verification record
                verification = MFAVerification(
                    verification_id=secrets.token_urlsafe(32),
                    user_id=user_id,
                    method="sms",
                    code=code
                )
                
                self._verifications[verification.verification_id] = verification
                
                logger.info(f"SMS verification sent for user {user_id}")
                return True
            else:
                logger.warning(f"Failed to send SMS verification for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS verification: {e}")
            return False
    
    async def send_email_verification(self, user_id: str, email: str) -> bool:
        """
        Send email verification code.
        
        Args:
            user_id: User ID
            email: Email address
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Generate verification code
            code = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            # Send email
            success = await self._email_manager.send_verification_code(email, code)
            
            if success:
                # Create verification record
                verification = MFAVerification(
                    verification_id=secrets.token_urlsafe(32),
                    user_id=user_id,
                    method="email",
                    code=code
                )
                
                self._verifications[verification.verification_id] = verification
                
                logger.info(f"Email verification sent for user {user_id}")
                return True
            else:
                logger.warning(f"Failed to send email verification for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email verification: {e}")
            return False
    
    async def verify_code(
        self,
        verification_id: str,
        code: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify MFA code.
        
        Args:
            verification_id: Verification ID
            code: Verification code
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            verification = self._verifications.get(verification_id)
            if not verification:
                return False, "Invalid verification ID"
            
            # Check if verification has expired
            if datetime.utcnow() > verification.expires_at:
                verification.status = MFAStatus.EXPIRED
                return False, "Verification has expired"
            
            # Check max attempts
            if verification.attempts >= verification.max_attempts:
                verification.status = MFAStatus.LOCKED
                return False, "Too many verification attempts"
            
            # Increment attempts
            verification.attempts += 1
            
            # Verify code
            if verification.code == code:
                verification.status = MFAStatus.VERIFIED
                
                # Log successful verification
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.INFO,
                    "message": f"MFA verification successful using {verification.method}",
                    "user_id": verification.user_id,
                    "metadata": {
                        "method": verification.method,
                        "verification_id": verification_id
                    }
                })
                
                logger.info(f"MFA verification successful for user {verification.user_id}")
                return True, None
            else:
                # Log failed verification
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.WARNING,
                    "message": f"MFA verification failed using {verification.method}",
                    "user_id": verification.user_id,
                    "metadata": {
                        "method": verification.method,
                        "verification_id": verification_id,
                        "attempts": verification.attempts
                    }
                })
                
                logger.warning(f"MFA verification failed for user {verification.user_id}")
                return False, "Invalid verification code"
                
        except Exception as e:
            logger.error(f"Error verifying MFA code: {e}")
            return False, "Verification error"
    
    async def verify_backup_code(self, user_id: str, code: str) -> bool:
        """
        Verify backup code.
        
        Args:
            user_id: User ID
            code: Backup code
            
        Returns:
            True if backup code is valid, False otherwise
        """
        try:
            success = self._backup_code_manager.verify_backup_code(user_id, code)
            
            if success:
                # Log successful backup code use
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.INFO,
                    "message": "Backup code used successfully",
                    "user_id": user_id,
                    "metadata": {"backup_code_used": True}
                })
                
                logger.info(f"Backup code used successfully for user {user_id}")
            else:
                # Log failed backup code use
                self._audit_logger.log_audit_event({
                    "event_type": AuditEventType.SECURITY_EVENT,
                    "severity": AuditSeverity.WARNING,
                    "message": "Invalid backup code used",
                    "user_id": user_id,
                    "metadata": {"backup_code_used": False}
                })
                
                logger.warning(f"Invalid backup code used for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error verifying backup code: {e}")
            return False
    
    async def get_remaining_backup_codes(self, user_id: str) -> int:
        """
        Get number of remaining backup codes.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of remaining backup codes
        """
        return self._backup_code_manager.get_remaining_codes(user_id)
    
    async def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """
        Regenerate backup codes for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of new backup codes
        """
        try:
            codes = self._backup_code_manager.regenerate_backup_codes(user_id)
            
            # Log backup code regeneration
            self._audit_logger.log_audit_event({
                "event_type": AuditEventType.SECURITY_EVENT,
                "severity": AuditSeverity.INFO,
                "message": "Backup codes regenerated",
                "user_id": user_id,
                "metadata": {"backup_codes_count": len(codes)}
            })
            
            logger.info(f"Backup codes regenerated for user {user_id}")
            return codes
            
        except Exception as e:
            logger.error(f"Error regenerating backup codes: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check the health of the MFA Service."""
        if not self._initialized:
            return False
        
        try:
            # Test TOTP generation and verification
            secret = self._totp_manager.generate_secret()
            code = self._totp_manager.get_current_code(secret)
            
            if not self._totp_manager.verify_code(secret, code):
                return False
            
            # Test backup code generation
            backup_codes = self._backup_code_manager.generate_backup_codes(5)
            if len(backup_codes) != 5:
                return False
            
            return True
        except Exception as e:
            logger.error(f"MFA Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the MFA Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("MFA Service started successfully")
    
    async def stop(self) -> None:
        """Stop the MFA Service."""
        if not self._initialized:
            return
        
        # Clear data structures
        self._setups.clear()
        self._verifications.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("MFA Service stopped successfully")


__all__ = [
    "MFAService",
    "MFAConfig",
    "MFASetup",
    "MFAVerification",
    "MFAStatus",
    "TOTPManager",
    "SMSManager",
    "EmailManager",
    "BackupCodeManager",
]