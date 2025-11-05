"""
EchoCore Factory - Centralized initialization and management
Provides factory pattern for all EchoCore components.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from ai_karen_engine.echocore.enhanced_echo_vault import EnhancedEchoVault
from ai_karen_engine.echocore.enhanced_dark_tracker import EnhancedDarkTracker, PrivacyLevel
from ai_karen_engine.echocore.production_fine_tuner import ProductionFineTuner, TrainingConfig
from ai_karen_engine.echocore.echo_components import (
    EchoAnalyzer,
    EchoSynthesizer,
    EchoPipeline
)

logger = logging.getLogger(__name__)


class EchoCoreConfig:
    """Configuration for EchoCore system."""

    def __init__(
        self,
        # Base settings
        base_dir: Path = Path("data/users"),
        # Vault settings
        enable_encryption: bool = False,
        enable_compression: bool = True,
        max_backups: int = 10,
        # Tracker settings
        max_log_size_mb: int = 10,
        max_log_age_days: int = 30,
        enable_sampling: bool = False,
        sampling_rate: float = 1.0,
        privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL,
        # Fine-tuner settings
        enable_experiment_tracking: bool = True,
        # Analysis settings
        default_lookback_days: int = 7,
        enable_auto_analysis: bool = True,
        # Pipeline settings
        enable_auto_fine_tuning: bool = False,
        auto_fine_tuning_threshold: int = 1000,  # Events before triggering
    ):
        self.base_dir = Path(base_dir)

        # Vault
        self.enable_encryption = enable_encryption
        self.enable_compression = enable_compression
        self.max_backups = max_backups

        # Tracker
        self.max_log_size_mb = max_log_size_mb
        self.max_log_age_days = max_log_age_days
        self.enable_sampling = enable_sampling
        self.sampling_rate = sampling_rate
        self.privacy_level = privacy_level

        # Fine-tuner
        self.enable_experiment_tracking = enable_experiment_tracking

        # Analysis
        self.default_lookback_days = default_lookback_days
        self.enable_auto_analysis = enable_auto_analysis

        # Pipeline
        self.enable_auto_fine_tuning = enable_auto_fine_tuning
        self.auto_fine_tuning_threshold = auto_fine_tuning_threshold


class EchoCoreFactory:
    """
    Factory for creating and managing EchoCore components.

    This factory ensures all components are properly initialized,
    configured, and wired together for production use.
    """

    def __init__(self, config: Optional[EchoCoreConfig] = None):
        self.config = config or EchoCoreConfig()
        self._components: Dict[str, Dict[str, Any]] = {}
        logger.info("EchoCoreFactory initialized")

    def create_vault(
        self,
        user_id: str,
        encryption_key: Optional[bytes] = None
    ) -> EnhancedEchoVault:
        """
        Create an EchoVault for a user.

        Args:
            user_id: User identifier
            encryption_key: Optional encryption key

        Returns:
            EnhancedEchoVault instance
        """
        if user_id not in self._components:
            self._components[user_id] = {}

        if "vault" not in self._components[user_id]:
            vault = EnhancedEchoVault(
                user_id=user_id,
                base_dir=self.config.base_dir,
                enable_encryption=self.config.enable_encryption,
                enable_compression=self.config.enable_compression,
                max_backups=self.config.max_backups,
                encryption_key=encryption_key
            )
            self._components[user_id]["vault"] = vault
            logger.info(f"Created vault for user {user_id}")

        return self._components[user_id]["vault"]

    def create_tracker(self, user_id: str) -> EnhancedDarkTracker:
        """
        Create a DarkTracker for a user.

        Args:
            user_id: User identifier

        Returns:
            EnhancedDarkTracker instance
        """
        if user_id not in self._components:
            self._components[user_id] = {}

        if "tracker" not in self._components[user_id]:
            tracker = EnhancedDarkTracker(
                user_id=user_id,
                base_dir=self.config.base_dir,
                max_log_size_mb=self.config.max_log_size_mb,
                max_log_age_days=self.config.max_log_age_days,
                enable_sampling=self.config.enable_sampling,
                sampling_rate=self.config.sampling_rate,
                privacy_level=self.config.privacy_level
            )
            self._components[user_id]["tracker"] = tracker
            logger.info(f"Created tracker for user {user_id}")

        return self._components[user_id]["tracker"]

    def create_fine_tuner(self, user_id: str) -> ProductionFineTuner:
        """
        Create a FineTuner for a user.

        Args:
            user_id: User identifier

        Returns:
            ProductionFineTuner instance
        """
        if user_id not in self._components:
            self._components[user_id] = {}

        if "fine_tuner" not in self._components[user_id]:
            tracker = self.create_tracker(user_id)
            logs_path = tracker.current_log

            fine_tuner = ProductionFineTuner(
                logs_path=logs_path,
                output_dir=self.config.base_dir / user_id / "models",
                enable_experiment_tracking=self.config.enable_experiment_tracking
            )
            self._components[user_id]["fine_tuner"] = fine_tuner
            logger.info(f"Created fine-tuner for user {user_id}")

        return self._components[user_id]["fine_tuner"]

    def create_analyzer(self) -> EchoAnalyzer:
        """
        Create an EchoAnalyzer (shared across users).

        Returns:
            EchoAnalyzer instance
        """
        if "analyzer" not in self._components:
            analyzer = EchoAnalyzer()
            self._components["analyzer"] = analyzer
            logger.info("Created analyzer")

        return self._components["analyzer"]

    def create_synthesizer(self) -> EchoSynthesizer:
        """
        Create an EchoSynthesizer (shared across users).

        Returns:
            EchoSynthesizer instance
        """
        if "synthesizer" not in self._components:
            synthesizer = EchoSynthesizer()
            self._components["synthesizer"] = synthesizer
            logger.info("Created synthesizer")

        return self._components["synthesizer"]

    def create_pipeline(self, user_id: str) -> EchoPipeline:
        """
        Create an EchoPipeline for a user.

        Args:
            user_id: User identifier

        Returns:
            EchoPipeline instance
        """
        if user_id not in self._components:
            self._components[user_id] = {}

        if "pipeline" not in self._components[user_id]:
            pipeline = EchoPipeline(
                user_id=user_id,
                base_dir=self.config.base_dir
            )
            self._components[user_id]["pipeline"] = pipeline
            logger.info(f"Created pipeline for user {user_id}")

        return self._components[user_id]["pipeline"]

    def create_all_for_user(self, user_id: str) -> Dict[str, Any]:
        """
        Create all EchoCore components for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of all components
        """
        return {
            "vault": self.create_vault(user_id),
            "tracker": self.create_tracker(user_id),
            "fine_tuner": self.create_fine_tuner(user_id),
            "pipeline": self.create_pipeline(user_id),
            "analyzer": self.create_analyzer(),
            "synthesizer": self.create_synthesizer()
        }

    def get_components(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all components for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of components or None
        """
        return self._components.get(user_id)

    def list_users(self) -> list:
        """
        List all users with EchoCore components.

        Returns:
            List of user IDs
        """
        return [
            user_id for user_id in self._components.keys()
            if user_id not in ["analyzer", "synthesizer"]
        ]

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on EchoCore system.

        Returns:
            Health check results
        """
        health = {
            "status": "healthy",
            "users_count": len(self.list_users()),
            "components": {}
        }

        # Check each user's components
        for user_id in self.list_users():
            user_health = {}

            # Check vault
            if "vault" in self._components[user_id]:
                vault = self._components[user_id]["vault"]
                vault_stats = await vault.get_statistics()
                user_health["vault"] = {
                    "healthy": True,
                    "current_exists": vault_stats["current_exists"],
                    "snapshot_count": vault_stats["snapshot_count"]
                }

            # Check tracker
            if "tracker" in self._components[user_id]:
                tracker = self._components[user_id]["tracker"]
                tracker_stats = await tracker.get_statistics()
                user_health["tracker"] = {
                    "healthy": True,
                    "current_log_exists": tracker_stats["current_log_exists"],
                    "archive_count": tracker_stats["archive_count"]
                }

            health["components"][user_id] = user_health

        return health


# Global factory instance
_global_factory: Optional[EchoCoreFactory] = None


@lru_cache()
def get_echocore_factory(config: Optional[EchoCoreConfig] = None) -> EchoCoreFactory:
    """
    Get or create global EchoCore factory.

    Args:
        config: Optional configuration

    Returns:
        EchoCoreFactory instance
    """
    global _global_factory

    if _global_factory is None:
        _global_factory = EchoCoreFactory(config)
        logger.info("Global EchoCore factory created")

    return _global_factory


def initialize_echocore_for_user(user_id: str) -> Dict[str, Any]:
    """
    Initialize all EchoCore components for a user.

    Args:
        user_id: User identifier

    Returns:
        Dictionary of all components
    """
    factory = get_echocore_factory()
    return factory.create_all_for_user(user_id)


__all__ = [
    "EchoCoreConfig",
    "EchoCoreFactory",
    "get_echocore_factory",
    "initialize_echocore_for_user"
]
