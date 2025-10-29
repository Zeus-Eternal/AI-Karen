"""
Extension Marketplace Data Models

This module defines the database models and Pydantic schemas for the extension marketplace.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import semver

Base = declarative_base()


class ExtensionStatus(str, Enum):
    """Extension status in marketplace."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"


class InstallationStatus(str, Enum):
    """Extension installation status."""
    PENDING = "pending"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    UPDATING = "updating"
    UNINSTALLING = "uninstalling"


# Database Models

class ExtensionListing(Base):
    """Extension listing in marketplace."""
    __tablename__ = "extension_listings"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    author = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(JSON, default=list)
    
    # Marketplace metadata
    status = Column(String(50), default=ExtensionStatus.PENDING, index=True)
    price = Column(String(50), default="free")  # "free", "paid", "$9.99"
    license = Column(String(100), nullable=False)
    support_url = Column(String(500))
    documentation_url = Column(String(500))
    repository_url = Column(String(500))
    
    # Statistics
    download_count = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relationships
    versions = relationship("ExtensionVersion", back_populates="listing", cascade="all, delete-orphan")
    installations = relationship("ExtensionInstallation", back_populates="listing")
    reviews = relationship("ExtensionReview", back_populates="listing")


class ExtensionVersion(Base):
    """Extension version information."""
    __tablename__ = "extension_versions"
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("extension_listings.id"), nullable=False)
    version = Column(String(50), nullable=False)
    manifest = Column(JSON, nullable=False)
    
    # Version metadata
    changelog = Column(Text)
    is_stable = Column(Boolean, default=True)
    min_kari_version = Column(String(50))
    max_kari_version = Column(String(50))
    
    # Package information
    package_url = Column(String(500))
    package_size = Column(Integer)  # Size in bytes
    package_hash = Column(String(128))  # SHA-256 hash
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relationships
    listing = relationship("ExtensionListing", back_populates="versions")
    dependencies = relationship("ExtensionDependency", back_populates="version", cascade="all, delete-orphan")
    installations = relationship("ExtensionInstallation", back_populates="version")


class ExtensionDependency(Base):
    """Extension dependency information."""
    __tablename__ = "extension_dependencies"
    
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("extension_versions.id"), nullable=False)
    
    # Dependency details
    dependency_type = Column(String(50), nullable=False)  # "extension", "plugin", "system_service"
    dependency_name = Column(String(255), nullable=False)
    version_constraint = Column(String(100))  # e.g., "^1.0.0", ">=2.0.0"
    is_optional = Column(Boolean, default=False)
    
    # Relationships
    version = relationship("ExtensionVersion", back_populates="dependencies")


class ExtensionInstallation(Base):
    """Extension installation record."""
    __tablename__ = "extension_installations"
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("extension_listings.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("extension_versions.id"), nullable=False)
    
    # Installation context
    tenant_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    
    # Installation status
    status = Column(String(50), default=InstallationStatus.PENDING)
    error_message = Column(Text)
    
    # Configuration
    config = Column(JSON, default=dict)
    
    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    listing = relationship("ExtensionListing", back_populates="installations")
    version = relationship("ExtensionVersion", back_populates="installations")


class ExtensionReview(Base):
    """Extension review and rating."""
    __tablename__ = "extension_reviews"
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("extension_listings.id"), nullable=False)
    
    # Review details
    user_id = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255))
    comment = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    listing = relationship("ExtensionListing", back_populates="reviews")


# Pydantic Schemas

class ExtensionDependencySchema(BaseModel):
    """Extension dependency schema."""
    dependency_type: str
    dependency_name: str
    version_constraint: Optional[str] = None
    is_optional: bool = False
    
    class Config:
        from_attributes = True


class ExtensionVersionSchema(BaseModel):
    """Extension version schema."""
    id: Optional[int] = None
    version: str
    manifest: Dict[str, Any]
    changelog: Optional[str] = None
    is_stable: bool = True
    min_kari_version: Optional[str] = None
    max_kari_version: Optional[str] = None
    package_url: Optional[str] = None
    package_size: Optional[int] = None
    package_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    dependencies: List[ExtensionDependencySchema] = []
    
    @validator('version')
    def validate_version(cls, v):
        """Validate semantic version format."""
        try:
            semver.VersionInfo.parse(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid semantic version: {v}")
    
    class Config:
        from_attributes = True


class ExtensionListingSchema(BaseModel):
    """Extension listing schema."""
    id: Optional[int] = None
    name: str
    display_name: str
    description: str
    author: str
    category: str
    tags: List[str] = []
    status: ExtensionStatus = ExtensionStatus.PENDING
    price: str = "free"
    license: str
    support_url: Optional[str] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    download_count: int = 0
    rating_average: float = 0.0
    rating_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    versions: List[ExtensionVersionSchema] = []
    
    @validator('name')
    def validate_name(cls, v):
        """Validate extension name format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Extension name must contain only alphanumeric characters, hyphens, and underscores")
        return v.lower()
    
    class Config:
        from_attributes = True


class ExtensionInstallationSchema(BaseModel):
    """Extension installation schema."""
    id: Optional[int] = None
    listing_id: int
    version_id: int
    tenant_id: str
    user_id: str
    status: InstallationStatus = InstallationStatus.PENDING
    error_message: Optional[str] = None
    config: Dict[str, Any] = {}
    installed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExtensionReviewSchema(BaseModel):
    """Extension review schema."""
    id: Optional[int] = None
    listing_id: int
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Request/Response Models

class ExtensionSearchRequest(BaseModel):
    """Extension search request."""
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[ExtensionStatus] = None
    price_filter: Optional[str] = None  # "free", "paid", "all"
    sort_by: str = "popularity"  # "popularity", "rating", "newest", "name"
    sort_order: str = "desc"  # "asc", "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ExtensionSearchResponse(BaseModel):
    """Extension search response."""
    extensions: List[ExtensionListingSchema]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ExtensionInstallRequest(BaseModel):
    """Extension installation request."""
    extension_name: str
    version: Optional[str] = None  # If not specified, install latest stable
    config: Dict[str, Any] = {}


class ExtensionInstallResponse(BaseModel):
    """Extension installation response."""
    installation_id: int
    status: InstallationStatus
    message: str


class ExtensionUpdateRequest(BaseModel):
    """Extension update request."""
    extension_name: str
    target_version: Optional[str] = None  # If not specified, update to latest stable


class DependencyResolutionResult(BaseModel):
    """Dependency resolution result."""
    resolved: bool
    dependencies: List[ExtensionDependencySchema]
    conflicts: List[str] = []
    missing: List[str] = []