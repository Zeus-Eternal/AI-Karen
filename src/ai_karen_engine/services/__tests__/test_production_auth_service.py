"""
Unit tests for Production Authentication Service
"""

import pytest
import tempfile
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from ..production_auth_service import AuthService, UserAccount
from ..auth_data_cleanup_service import AuthDataCleanupService
from ...core.services.base import ServiceConfig


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.fixture
    def temp_users_file(self):
        """Create a temporary users file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_users = {
                "admin@kari.ai": {
                    "user_id": "admin",
                    "email": "admin@kari.ai",
                    "password_hash": "salt123:hashedpassword123",
                    "full_name": "Admin User",
                    "roles": ["admin", "user"],
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_login": None,
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "tenant_id": "default",
                    "two_factor_enabled": False,
                    "preferences": {}
                },
                "admin@example.com": {
                    "user_id": "demo_admin",
                    "email": "admin@example.com",
                    "password_hash": "demo_hash",
                    "full_name": "Demo Admin",
                    "roles": ["admin"],
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_login": None,
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "tenant_id": "default",
                    "two_factor_enabled": False,
                    "preferences": {}
                }
            }
            json.dump(test_users, f)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def auth_service(self, temp_users_file):
        """Create a test authentication service."""
        config = ServiceConfig(
            name="test_auth",
            enabled=True,
            config={
                "users_file": str(temp_users_file),
                "jwt_secret": "test_secret_key_for_testing_only",
                "access_token_expire_minutes": 30,
                "max_failed_attempts": 3,
                "lockout_duration_minutes": 5,
                "require_strong_passwords": False  # Disable for testing
            }
        )
        return AuthService(config)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, auth_service):
        """Test service initialization."""
        await auth_service.initialize()
        
        # Should load users from file
        assert len(auth_service.users) == 1  # Only non-demo account
        assert "admin@kari.ai" in auth_service.users
        assert "admin@example.com" not in auth_service.users  # Demo account filtered
    
    @pytest.mark.asyncio
    async def test_health_check(self, auth_service):
        """Test health check functionality."""
        await auth_service.initialize()
        health_status = await auth_service.health_check()
        assert health_status is True
    
    @pytest.mark.asyncio
    async def test_first_run_detection(self, auth_service):
        """Test first-run detection."""
        # Clear users to simulate first run
        auth_service.users = {}
        
        is_first_run = await auth_service.is_first_run()
        assert is_first_run is True
        
        # Add admin user
        admin_user = UserAccount(
            user_id="admin",
            email="admin@test.com",
            password_hash="hash",
            full_name="Admin",
            roles=["admin"]
        )
        auth_service.users["admin@test.com"] = admin_user
        
        is_first_run = await auth_service.is_first_run()
        assert is_first_run is False
    
    @pytest.mark.asyncio
    async def test_create_first_admin(self, auth_service):
        """Test creating first admin user."""
        # Clear users to simulate first run
        auth_service.users = {}
        
        user = await auth_service.create_first_admin(
            email="admin@test.com",
            password="TestPassword123!",
            full_name="Test Admin"
        )
        
        assert user.email == "admin@test.com"
        assert user.full_name == "Test Admin"
        assert "super_admin" in user.roles
        assert "admin" in user.roles
        assert user.is_active is True
    
    def test_password_hashing(self, auth_service):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        
        # Hash password
        password_hash = auth_service._hash_password(password)
        assert ":" in password_hash  # Should contain salt
        
        # Verify correct password
        assert auth_service._verify_password(password, password_hash) is True
        
        # Verify incorrect password
        assert auth_service._verify_password("WrongPassword", password_hash) is False
    
    def test_password_strength_validation(self, auth_service):
        """Test password strength validation."""
        # Enable strong password requirement
        auth_service.require_strong_passwords = True
        
        # Test weak passwords
        weak_passwords = [
            "123456",
            "password",
            "Password",
            "Password123",
            "password123!"
        ]
        
        for password in weak_passwords:
            is_strong, issues = auth_service._validate_password_strength(password)
            assert is_strong is False
            assert len(issues) > 0
        
        # Test strong password
        strong_password = "StrongPassword123!"
        is_strong, issues = auth_service._validate_password_strength(strong_password)
        assert is_strong is True
        assert len(issues) == 0
    
    def test_rate_limiting(self, auth_service):
        """Test rate limiting functionality."""
        ip_address = "192.168.1.1"
        email = "test@test.com"
        
        # Add multiple failed attempts
        for _ in range(auth_service.max_attempts_per_window):
            auth_service._record_auth_attempt(ip_address, email, False)
        
        # Should be rate limited
        assert auth_service._is_rate_limited(ip_address, email) is True
        
        # Different IP should not be rate limited
        assert auth_service._is_rate_limited("192.168.1.2", email) is False
    
    def test_account_lockout(self, auth_service):
        """Test account lockout functionality."""
        user = UserAccount(
            user_id="test",
            email="test@test.com",
            password_hash="hash",
            full_name="Test User",
            roles=["user"]
        )
        
        # Simulate failed attempts
        user.failed_login_attempts = auth_service.max_failed_attempts
        
        # Should be locked
        assert auth_service._is_account_locked(user) is True
        assert user.locked_until is not None
    
    @pytest.mark.asyncio
    async def test_user_authentication_success(self, auth_service):
        """Test successful user authentication."""
        await auth_service.initialize()
        
        # Create a test user with known password
        test_password = "TestPassword123"
        user = UserAccount(
            user_id="test",
            email="test@test.com",
            password_hash=auth_service._hash_password(test_password),
            full_name="Test User",
            roles=["user"],
            is_active=True
        )
        auth_service.users["test@test.com"] = user
        
        # Authenticate
        auth_user, access_token, refresh_token = await auth_service.authenticate_user(
            email="test@test.com",
            password=test_password,
            ip_address="192.168.1.1",
            user_agent="test-agent"
        )
        
        assert auth_user is not None
        assert auth_user.email == "test@test.com"
        assert access_token is not None
        assert refresh_token is not None
        assert user.failed_login_attempts == 0
        assert user.last_login is not None
    
    @pytest.mark.asyncio
    async def test_user_authentication_failure(self, auth_service):
        """Test failed user authentication."""
        await auth_service.initialize()
        
        # Try to authenticate non-existent user
        auth_user, access_token, error = await auth_service.authenticate_user(
            email="nonexistent@test.com",
            password="password",
            ip_address="192.168.1.1",
            user_agent="test-agent"
        )
        
        assert auth_user is None
        assert access_token is None
        assert error == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_token_validation(self, auth_service):
        """Test JWT token validation."""
        await auth_service.initialize()
        
        # Create a test user
        user = UserAccount(
            user_id="test",
            email="test@test.com",
            password_hash="hash",
            full_name="Test User",
            roles=["user"],
            is_active=True
        )
        auth_service.users["test@test.com"] = user
        
        # Create token
        access_token, _ = auth_service._create_jwt_token(user, "access")
        
        # Validate token
        validated_user = await auth_service.validate_token(access_token)
        assert validated_user is not None
        assert validated_user.email == "test@test.com"
        
        # Test invalid token
        invalid_user = await auth_service.validate_token("invalid_token")
        assert invalid_user is None
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, auth_service):
        """Test token refresh functionality."""
        await auth_service.initialize()
        
        # Create a test user
        user = UserAccount(
            user_id="test",
            email="test@test.com",
            password_hash="hash",
            full_name="Test User",
            roles=["user"],
            is_active=True
        )
        auth_service.users["test@test.com"] = user
        
        # Create refresh token
        refresh_token, expires_at = auth_service._create_jwt_token(user, "refresh")
        auth_service.refresh_tokens[refresh_token] = {
            "user_email": "test@test.com",
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Refresh access token
        new_access_token, error = await auth_service.refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        assert error is None
        
        # Test invalid refresh token
        invalid_token, error = await auth_service.refresh_access_token("invalid_token")
        assert invalid_token is None
        assert error is not None


class TestAuthDataCleanupService:
    """Test cases for AuthDataCleanupService."""
    
    @pytest.fixture
    def temp_users_file(self):
        """Create a temporary users file with demo accounts."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_users = {
                "admin@kari.ai": {
                    "user_id": "admin",
                    "email": "admin@kari.ai",
                    "password_hash": "real_hash",
                    "full_name": "Real Admin",
                    "roles": ["admin"],
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                "admin@example.com": {
                    "user_id": "demo_admin",
                    "email": "admin@example.com",
                    "password_hash": "demo_hash",
                    "full_name": "Demo Admin",
                    "roles": ["admin"],
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                "test@example.com": {
                    "user_id": "test_user",
                    "email": "test@example.com",
                    "password_hash": "test_hash",
                    "full_name": "Test User",
                    "roles": ["user"],
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }
            json.dump(test_users, f)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def cleanup_service(self, temp_users_file):
        """Create a test cleanup service."""
        config = ServiceConfig(
            name="test_cleanup",
            enabled=True,
            config={
                "users_file": str(temp_users_file),
                "backup_directory": str(Path(temp_users_file).parent / "backups"),
                "preserve_accounts": ["admin@kari.ai"]
            }
        )
        return AuthDataCleanupService(config)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, cleanup_service):
        """Test cleanup service initialization."""
        await cleanup_service.initialize()
        assert cleanup_service.backup_directory.exists()
    
    @pytest.mark.asyncio
    async def test_health_check(self, cleanup_service):
        """Test health check functionality."""
        await cleanup_service.initialize()
        health_status = await cleanup_service.health_check()
        assert health_status is True
    
    def test_demo_account_detection(self, cleanup_service):
        """Test demo account detection."""
        # Demo accounts
        assert cleanup_service._is_demo_account("admin@example.com") is True
        assert cleanup_service._is_demo_account("test@example.com") is True
        assert cleanup_service._is_demo_account("demo@example.com") is True
        
        # Production accounts
        assert cleanup_service._is_demo_account("admin@kari.ai") is False
        assert cleanup_service._is_demo_account("user@company.com") is False
    
    def test_account_preservation(self, cleanup_service):
        """Test account preservation logic."""
        assert cleanup_service._should_preserve_account("admin@kari.ai") is True
        assert cleanup_service._should_preserve_account("admin@example.com") is False
    
    def test_user_data_validation(self, cleanup_service):
        """Test user data validation."""
        # Valid user data
        valid_user = {
            "user_id": "test",
            "email": "test@test.com",
            "password_hash": "long_secure_hash_here_123456789",
            "full_name": "Test User",
            "roles": ["user"]
        }
        issues = cleanup_service._validate_user_data("test@test.com", valid_user)
        assert len(issues) == 0
        
        # Invalid user data
        invalid_user = {
            "user_id": "",
            "email": "wrong@email.com",
            "password_hash": "short",
            "full_name": "Test Demo User",
            "roles": []
        }
        issues = cleanup_service._validate_user_data("test@test.com", invalid_user)
        assert len(issues) > 0
        assert any("Empty required field" in issue for issue in issues)
        assert any("Email mismatch" in issue for issue in issues)
        assert any("Password hash appears too short" in issue for issue in issues)
        assert any("placeholder value" in issue for issue in issues)
        assert any("Roles must be a non-empty list" in issue for issue in issues)
    
    @pytest.mark.asyncio
    async def test_clean_demo_accounts_dry_run(self, cleanup_service):
        """Test cleaning demo accounts in dry run mode."""
        await cleanup_service.initialize()
        
        report = await cleanup_service.clean_demo_accounts(dry_run=True)
        
        assert report["dry_run"] is True
        assert report["original_user_count"] == 3
        assert len(report["removed_accounts"]) == 2  # admin@example.com and test@example.com
        assert len(report["preserved_accounts"]) == 1  # admin@kari.ai
        assert report["backup_created"] is not None
        
        # File should not be modified in dry run
        with open(cleanup_service.users_file, 'r') as f:
            users_data = json.load(f)
        assert len(users_data) == 3  # Original count
    
    @pytest.mark.asyncio
    async def test_clean_demo_accounts_real(self, cleanup_service):
        """Test cleaning demo accounts for real."""
        await cleanup_service.initialize()
        
        report = await cleanup_service.clean_demo_accounts(dry_run=False)
        
        assert report["dry_run"] is False
        assert report["original_user_count"] == 3
        assert report["cleaned_user_count"] == 1
        assert len(report["removed_accounts"]) == 2
        assert len(report["preserved_accounts"]) == 1
        
        # File should be modified
        with open(cleanup_service.users_file, 'r') as f:
            users_data = json.load(f)
        assert len(users_data) == 1  # Only preserved account
        assert "admin@kari.ai" in users_data
        assert "admin@example.com" not in users_data
        assert "test@example.com" not in users_data
    
    @pytest.mark.asyncio
    async def test_validate_production_data(self, cleanup_service):
        """Test production data validation."""
        await cleanup_service.initialize()
        
        # Before cleanup - should have issues
        report = await cleanup_service.validate_production_data()
        assert report["is_production_ready"] is False
        assert report["total_users"] == 3
        assert len(report["issues"]) > 0
        assert any("Demo account found" in issue for issue in report["issues"])
        
        # After cleanup
        await cleanup_service.clean_demo_accounts(dry_run=False)
        report = await cleanup_service.validate_production_data()
        assert report["is_production_ready"] is True
        assert report["total_users"] == 1
        assert report["admin_users"] == 1
        assert report["active_users"] == 1
    
    def test_generate_cleanup_report(self, cleanup_service):
        """Test cleanup report generation."""
        # Before any cleanup
        report_text = cleanup_service.generate_cleanup_report()
        assert "No cleanup has been performed yet" in report_text
        
        # After setting up report data
        cleanup_service.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "original_user_count": 3,
            "cleaned_user_count": 1,
            "removed_accounts": [{"email": "demo@example.com", "full_name": "Demo", "reason": "demo account"}],
            "preserved_accounts": [{"email": "admin@kari.ai", "full_name": "Admin", "reason": "production account"}],
            "validation_issues": ["Some issue"],
            "backup_created": "/path/to/backup.json",
            "dry_run": False
        }
        
        report_text = cleanup_service.generate_cleanup_report()
        assert "Authentication Data Cleanup Report" in report_text
        assert "Original users: 3" in report_text
        assert "Cleaned users: 1" in report_text
        assert "demo@example.com" in report_text
        assert "admin@kari.ai" in report_text


if __name__ == "__main__":
    pytest.main([__file__])