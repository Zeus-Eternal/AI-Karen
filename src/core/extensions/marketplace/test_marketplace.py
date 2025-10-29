"""
Extension Marketplace Tests

Test suite for the extension marketplace functionality.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, AsyncMock

from .models import (
    Base, ExtensionListing, ExtensionVersion, ExtensionDependency,
    ExtensionInstallation, ExtensionSearchRequest, ExtensionInstallRequest,
    ExtensionStatus, InstallationStatus
)
from .service import ExtensionMarketplaceService
from .version_manager import VersionManager
from .database import MarketplaceDatabaseManager


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_extension_listing(db_session):
    """Create a sample extension listing."""
    listing = ExtensionListing(
        name="test-extension",
        display_name="Test Extension",
        description="A test extension for unit testing",
        author="Test Author",
        category="testing",
        tags=["test", "unit-test"],
        status=ExtensionStatus.APPROVED,
        license="MIT",
        published_at=datetime.utcnow()
    )
    
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    
    return listing


@pytest.fixture
def sample_extension_version(db_session, sample_extension_listing):
    """Create a sample extension version."""
    version = ExtensionVersion(
        listing_id=sample_extension_listing.id,
        version="1.0.0",
        manifest={
            "name": "test-extension",
            "version": "1.0.0",
            "api_version": "1.0"
        },
        is_stable=True
    )
    
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    
    return version


@pytest.fixture
def marketplace_service(db_session):
    """Create a marketplace service instance."""
    extension_manager = Mock()
    extension_registry = Mock()
    
    return ExtensionMarketplaceService(
        db_session, extension_manager, extension_registry
    )


class TestExtensionMarketplaceService:
    """Test the ExtensionMarketplaceService."""
    
    @pytest.mark.asyncio
    async def test_search_extensions_basic(self, marketplace_service, sample_extension_listing):
        """Test basic extension search."""
        search_request = ExtensionSearchRequest(
            query="test",
            page=1,
            page_size=10
        )
        
        result = await marketplace_service.search_extensions(search_request)
        
        assert result.total_count == 1
        assert len(result.extensions) == 1
        assert result.extensions[0].name == "test-extension"
    
    @pytest.mark.asyncio
    async def test_search_extensions_by_category(self, marketplace_service, sample_extension_listing):
        """Test extension search by category."""
        search_request = ExtensionSearchRequest(
            category="testing",
            page=1,
            page_size=10
        )
        
        result = await marketplace_service.search_extensions(search_request)
        
        assert result.total_count == 1
        assert result.extensions[0].category == "testing"
    
    @pytest.mark.asyncio
    async def test_search_extensions_no_results(self, marketplace_service):
        """Test extension search with no results."""
        search_request = ExtensionSearchRequest(
            query="nonexistent",
            page=1,
            page_size=10
        )
        
        result = await marketplace_service.search_extensions(search_request)
        
        assert result.total_count == 0
        assert len(result.extensions) == 0
    
    @pytest.mark.asyncio
    async def test_get_extension_details(self, marketplace_service, sample_extension_listing):
        """Test getting extension details."""
        extension = await marketplace_service.get_extension_details("test-extension")
        
        assert extension is not None
        assert extension.name == "test-extension"
        assert extension.display_name == "Test Extension"
    
    @pytest.mark.asyncio
    async def test_get_extension_details_not_found(self, marketplace_service):
        """Test getting details for non-existent extension."""
        extension = await marketplace_service.get_extension_details("nonexistent")
        
        assert extension is None
    
    @pytest.mark.asyncio
    async def test_install_extension_success(self, marketplace_service, sample_extension_version):
        """Test successful extension installation."""
        # Mock the extension manager
        marketplace_service.extension_manager.load_extension = AsyncMock(return_value=True)
        
        install_request = ExtensionInstallRequest(
            extension_name="test-extension"
        )
        
        result = await marketplace_service.install_extension(
            install_request, "tenant1", "user1"
        )
        
        assert result.status == InstallationStatus.INSTALLING
        assert "started" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_install_extension_not_found(self, marketplace_service):
        """Test installing non-existent extension."""
        install_request = ExtensionInstallRequest(
            extension_name="nonexistent"
        )
        
        result = await marketplace_service.install_extension(
            install_request, "tenant1", "user1"
        )
        
        assert result.status == InstallationStatus.FAILED
        assert "not found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_install_extension_already_installed(
        self, marketplace_service, sample_extension_version, db_session
    ):
        """Test installing already installed extension."""
        # Create existing installation
        installation = ExtensionInstallation(
            listing_id=sample_extension_version.listing_id,
            version_id=sample_extension_version.id,
            tenant_id="tenant1",
            user_id="user1",
            status=InstallationStatus.INSTALLED
        )
        db_session.add(installation)
        db_session.commit()
        
        install_request = ExtensionInstallRequest(
            extension_name="test-extension"
        )
        
        result = await marketplace_service.install_extension(
            install_request, "tenant1", "user1"
        )
        
        assert result.status == InstallationStatus.INSTALLED
        assert "already installed" in result.message.lower()


class TestVersionManager:
    """Test the VersionManager."""
    
    def test_parse_version_valid(self):
        """Test parsing valid semantic versions."""
        version_manager = VersionManager(None)
        
        version = version_manager.parse_version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_parse_version_invalid(self):
        """Test parsing invalid versions."""
        version_manager = VersionManager(None)
        
        with pytest.raises(ValueError):
            version_manager.parse_version("invalid")
    
    def test_satisfies_constraint_exact(self):
        """Test exact version constraint."""
        version_manager = VersionManager(None)
        
        assert version_manager.satisfies_constraint("1.2.3", "1.2.3")
        assert not version_manager.satisfies_constraint("1.2.4", "1.2.3")
    
    def test_satisfies_constraint_range(self):
        """Test version range constraints."""
        version_manager = VersionManager(None)
        
        assert version_manager.satisfies_constraint("1.2.3", ">=1.2.0")
        assert version_manager.satisfies_constraint("1.2.3", "^1.2.0")
        assert not version_manager.satisfies_constraint("2.0.0", "^1.2.0")
    
    def test_compare_versions(self):
        """Test version comparison."""
        version_manager = VersionManager(None)
        
        assert version_manager.compare_versions("1.2.3", "1.2.4") < 0
        assert version_manager.compare_versions("1.2.4", "1.2.3") > 0
        assert version_manager.compare_versions("1.2.3", "1.2.3") == 0
    
    def test_is_upgrade(self):
        """Test upgrade detection."""
        version_manager = VersionManager(None)
        
        assert version_manager.is_upgrade("1.2.3", "1.2.4")
        assert version_manager.is_upgrade("1.2.3", "2.0.0")
        assert not version_manager.is_upgrade("1.2.4", "1.2.3")
    
    def test_is_compatible_upgrade(self):
        """Test compatible upgrade detection."""
        version_manager = VersionManager(None)
        
        assert version_manager.is_compatible_upgrade("1.2.3", "1.2.4")
        assert version_manager.is_compatible_upgrade("1.2.3", "1.3.0")
        assert not version_manager.is_compatible_upgrade("1.2.3", "2.0.0")
        assert version_manager.is_compatible_upgrade("1.2.3", "2.0.0", allow_major=True)
    
    def test_validate_manifest_version(self):
        """Test manifest version validation."""
        version_manager = VersionManager(None)
        
        # Valid manifest
        valid_manifest = {
            "version": "1.2.3",
            "api_version": "1.0",
            "kari_min_version": "0.4.0"
        }
        
        errors = version_manager.validate_manifest_version(valid_manifest)
        assert len(errors) == 0
        
        # Invalid manifest
        invalid_manifest = {
            "version": "invalid",
            "kari_min_version": "also-invalid"
        }
        
        errors = version_manager.validate_manifest_version(invalid_manifest)
        assert len(errors) > 0


class TestMarketplaceDatabaseManager:
    """Test the MarketplaceDatabaseManager."""
    
    def test_create_tables(self):
        """Test table creation."""
        db_manager = MarketplaceDatabaseManager("sqlite:///:memory:")
        
        assert db_manager.create_tables()
        assert db_manager.health_check()
    
    def test_health_check_success(self):
        """Test successful health check."""
        db_manager = MarketplaceDatabaseManager("sqlite:///:memory:")
        db_manager.create_tables()
        
        assert db_manager.health_check()
    
    def test_health_check_failure(self):
        """Test failed health check."""
        db_manager = MarketplaceDatabaseManager("invalid://connection")
        
        assert not db_manager.health_check()
    
    def test_get_session(self):
        """Test getting database session."""
        db_manager = MarketplaceDatabaseManager("sqlite:///:memory:")
        db_manager.create_tables()
        
        session = db_manager.get_session()
        assert session is not None
        session.close()


if __name__ == "__main__":
    pytest.main([__file__])