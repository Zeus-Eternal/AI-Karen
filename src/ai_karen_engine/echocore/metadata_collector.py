"""
Metadata Collector - User data collection and management

Provides structured user metadata collection with opt-in mechanisms.
Stores data in persistent memory with privacy controls.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ConsentLevel(str, Enum):
    """User consent levels for data collection."""
    NONE = "none"  # No data collection
    BASIC = "basic"  # Name, preferences only
    STANDARD = "standard"  # Basic + age, location
    FULL = "full"  # All metadata including behavioral patterns


@dataclass
class UserMetadata:
    """Structured user metadata."""
    # Core identity
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None

    # Demographics
    location: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

    # Preferences
    communication_style: Optional[str] = None  # "formal", "casual", "technical"
    response_length: Optional[str] = None  # "brief", "detailed", "adaptive"
    topics_of_interest: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None

    # Behavioral patterns (with consent)
    interaction_frequency: Optional[str] = None  # "daily", "weekly", "occasional"
    peak_hours: Optional[List[int]] = None  # Hours of day (0-23)
    preferred_features: Optional[List[str]] = None

    # Privacy and consent
    consent_level: ConsentLevel = ConsentLevel.BASIC
    data_retention_days: int = 365
    allow_analytics: bool = True
    allow_personalization: bool = True

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MetadataCollector:
    """
    Collects and manages user metadata with privacy controls.

    Features:
    - Structured metadata collection
    - Consent management
    - Privacy-aware storage
    - Opt-in/opt-out mechanisms
    - Data validation
    - GDPR compliance helpers
    """

    def __init__(
        self,
        user_id: str,
        persistent_memory: Optional[Any] = None
    ):
        self.user_id = user_id
        self.persistent_memory = persistent_memory

        # Current metadata
        self._metadata: Optional[UserMetadata] = None
        self._metadata_loaded = False

        logger.info(f"MetadataCollector initialized for user {user_id}")

    async def initialize(self) -> None:
        """Initialize and load existing metadata."""
        if self.persistent_memory:
            user_data = await self.persistent_memory.get_user_data()
            if user_data:
                # Convert UserData to UserMetadata
                self._metadata = UserMetadata(
                    user_id=self.user_id,
                    name=user_data.name,
                    age=user_data.age,
                    date_of_birth=user_data.date_of_birth,
                    **user_data.preferences,
                    created_at=user_data.created_at,
                    updated_at=user_data.updated_at
                )
                self._metadata_loaded = True
                logger.info(f"Loaded existing metadata for user {self.user_id}")
        else:
            # Create default metadata
            self._metadata = UserMetadata(
                user_id=self.user_id,
                created_at=datetime.utcnow().isoformat()
            )

    async def collect_basic_info(
        self,
        name: Optional[str] = None,
        language: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> UserMetadata:
        """
        Collect basic user information.

        Args:
            name: User's name
            language: User's preferred language
            timezone: User's timezone

        Returns:
            Updated UserMetadata
        """
        if not self._metadata:
            await self.initialize()

        # Update metadata
        if name is not None:
            self._metadata.name = name
        if language is not None:
            self._metadata.language = language
        if timezone is not None:
            self._metadata.timezone = timezone

        self._metadata.updated_at = datetime.utcnow().isoformat()

        # Save to persistent memory
        await self._save_metadata()

        logger.debug(f"Collected basic info for user {self.user_id}")
        return self._metadata

    async def collect_demographics(
        self,
        age: Optional[int] = None,
        date_of_birth: Optional[str] = None,
        location: Optional[str] = None
    ) -> UserMetadata:
        """
        Collect demographic information (requires STANDARD consent).

        Args:
            age: User's age
            date_of_birth: User's date of birth (ISO format)
            location: User's location

        Returns:
            Updated UserMetadata
        """
        if not self._metadata:
            await self.initialize()

        # Check consent level
        if self._metadata.consent_level == ConsentLevel.NONE:
            logger.warning(f"Cannot collect demographics: consent level is NONE")
            raise PermissionError("User has not consented to data collection")

        if self._metadata.consent_level == ConsentLevel.BASIC:
            logger.warning(f"Cannot collect demographics: consent level is BASIC")
            raise PermissionError("User consent level does not allow demographic data collection")

        # Update metadata
        if age is not None:
            self._metadata.age = age
        if date_of_birth is not None:
            self._metadata.date_of_birth = date_of_birth
        if location is not None:
            self._metadata.location = location

        self._metadata.updated_at = datetime.utcnow().isoformat()

        # Save to persistent memory
        await self._save_metadata()

        logger.debug(f"Collected demographics for user {self.user_id}")
        return self._metadata

    async def collect_preferences(
        self,
        communication_style: Optional[str] = None,
        response_length: Optional[str] = None,
        topics_of_interest: Optional[List[str]] = None,
        expertise_areas: Optional[List[str]] = None
    ) -> UserMetadata:
        """
        Collect user preferences.

        Args:
            communication_style: Preferred communication style
            response_length: Preferred response length
            topics_of_interest: List of topics the user is interested in
            expertise_areas: List of user's areas of expertise

        Returns:
            Updated UserMetadata
        """
        if not self._metadata:
            await self.initialize()

        # Update metadata
        if communication_style is not None:
            self._metadata.communication_style = communication_style
        if response_length is not None:
            self._metadata.response_length = response_length
        if topics_of_interest is not None:
            self._metadata.topics_of_interest = topics_of_interest
        if expertise_areas is not None:
            self._metadata.expertise_areas = expertise_areas

        self._metadata.updated_at = datetime.utcnow().isoformat()

        # Save to persistent memory
        await self._save_metadata()

        logger.debug(f"Collected preferences for user {self.user_id}")
        return self._metadata

    async def collect_behavioral_patterns(
        self,
        interaction_frequency: Optional[str] = None,
        peak_hours: Optional[List[int]] = None,
        preferred_features: Optional[List[str]] = None
    ) -> UserMetadata:
        """
        Collect behavioral patterns (requires FULL consent).

        Args:
            interaction_frequency: Frequency of interaction
            peak_hours: Peak hours of interaction
            preferred_features: Features the user prefers

        Returns:
            Updated UserMetadata
        """
        if not self._metadata:
            await self.initialize()

        # Check consent level
        if self._metadata.consent_level != ConsentLevel.FULL:
            logger.warning(f"Cannot collect behavioral patterns: consent level is {self._metadata.consent_level}")
            raise PermissionError("User consent level does not allow behavioral pattern collection")

        # Update metadata
        if interaction_frequency is not None:
            self._metadata.interaction_frequency = interaction_frequency
        if peak_hours is not None:
            self._metadata.peak_hours = peak_hours
        if preferred_features is not None:
            self._metadata.preferred_features = preferred_features

        self._metadata.updated_at = datetime.utcnow().isoformat()

        # Save to persistent memory
        await self._save_metadata()

        logger.debug(f"Collected behavioral patterns for user {self.user_id}")
        return self._metadata

    async def update_consent(
        self,
        consent_level: ConsentLevel,
        allow_analytics: Optional[bool] = None,
        allow_personalization: Optional[bool] = None,
        data_retention_days: Optional[int] = None
    ) -> UserMetadata:
        """
        Update user consent and privacy settings.

        Args:
            consent_level: New consent level
            allow_analytics: Allow analytics
            allow_personalization: Allow personalization
            data_retention_days: Data retention period in days

        Returns:
            Updated UserMetadata
        """
        if not self._metadata:
            await self.initialize()

        # Update consent settings
        self._metadata.consent_level = consent_level

        if allow_analytics is not None:
            self._metadata.allow_analytics = allow_analytics
        if allow_personalization is not None:
            self._metadata.allow_personalization = allow_personalization
        if data_retention_days is not None:
            self._metadata.data_retention_days = data_retention_days

        self._metadata.updated_at = datetime.utcnow().isoformat()

        # Save to persistent memory
        await self._save_metadata()

        logger.info(f"Updated consent for user {self.user_id} to {consent_level}")
        return self._metadata

    async def get_metadata(self) -> Optional[UserMetadata]:
        """
        Get current user metadata.

        Returns:
            UserMetadata or None
        """
        if not self._metadata:
            await self.initialize()

        return self._metadata

    async def export_metadata(self) -> Dict[str, Any]:
        """
        Export all user metadata (for GDPR data portability).

        Returns:
            Dictionary with all metadata
        """
        if not self._metadata:
            await self.initialize()

        if not self._metadata:
            return {}

        return asdict(self._metadata)

    async def delete_metadata(self) -> bool:
        """
        Delete all user metadata (for GDPR right to be forgotten).

        Returns:
            True if successful
        """
        if self.persistent_memory:
            success = await self.persistent_memory.delete_user_data()
            if success:
                self._metadata = None
                self._metadata_loaded = False
                logger.info(f"Deleted metadata for user {self.user_id}")
            return success
        else:
            self._metadata = None
            logger.info(f"Deleted metadata for user {self.user_id} (no persistent storage)")
            return True

    async def _save_metadata(self) -> None:
        """Save metadata to persistent memory."""
        if not self.persistent_memory or not self._metadata:
            return

        # Convert to preferences dict for storage
        preferences = {
            "communication_style": self._metadata.communication_style,
            "response_length": self._metadata.response_length,
            "topics_of_interest": self._metadata.topics_of_interest,
            "expertise_areas": self._metadata.expertise_areas,
            "interaction_frequency": self._metadata.interaction_frequency,
            "peak_hours": self._metadata.peak_hours,
            "preferred_features": self._metadata.preferred_features,
            "location": self._metadata.location,
            "timezone": self._metadata.timezone,
            "language": self._metadata.language
        }

        metadata_dict = {
            "consent_level": self._metadata.consent_level.value,
            "data_retention_days": self._metadata.data_retention_days,
            "allow_analytics": self._metadata.allow_analytics,
            "allow_personalization": self._metadata.allow_personalization
        }

        await self.persistent_memory.store_user_data(
            name=self._metadata.name,
            age=self._metadata.age,
            date_of_birth=self._metadata.date_of_birth,
            preferences=preferences,
            metadata=metadata_dict
        )

    async def get_personalization_hints(self) -> Dict[str, Any]:
        """
        Get hints for personalizing interactions.

        Returns:
            Dictionary with personalization hints
        """
        if not self._metadata or not self._metadata.allow_personalization:
            return {}

        hints = {}

        if self._metadata.communication_style:
            hints["communication_style"] = self._metadata.communication_style

        if self._metadata.response_length:
            hints["response_length"] = self._metadata.response_length

        if self._metadata.topics_of_interest:
            hints["topics_of_interest"] = self._metadata.topics_of_interest

        if self._metadata.expertise_areas:
            hints["expertise_areas"] = self._metadata.expertise_areas

        if self._metadata.language:
            hints["language"] = self._metadata.language

        return hints


__all__ = [
    "MetadataCollector",
    "UserMetadata",
    "ConsentLevel"
]
