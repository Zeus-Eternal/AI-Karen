"""
EchoCore - Production-ready user echo system

EchoCore provides a comprehensive system for user data persistence, event tracking,
pattern analysis, insight generation, and model fine-tuning.

Components:
-----------
- EchoVault: User data vault with versioning, encryption, and snapshots
- DarkTracker: Event tracking with log rotation, analytics, and privacy controls
- FineTuner: Production-ready model fine-tuning with experiment tracking
- EchoAnalyzer: Pattern discovery and anomaly detection
- EchoSynthesizer: Insight generation and recommendations
- EchoPipeline: End-to-end orchestration of echo workflow

Features:
---------
- Versioned data storage with snapshots
- Optional encryption and compression
- Automatic log rotation and retention
- Privacy level enforcement
- Pattern discovery and trend analysis
- Actionable insight generation
- Real model fine-tuning with HuggingFace
- Experiment tracking and model versioning
- Complete pipeline orchestration
- Factory pattern for easy initialization

Usage:
------
# Simple usage (backward compatible)
from ai_karen_engine.echocore import EchoVault, DarkTracker

vault = EchoVault(user_id="user123")
vault.backup({"key": "value"})

tracker = DarkTracker(user_id="user123")
tracker.capture({"event": "login"})

# Production usage
from ai_karen_engine.echocore import initialize_echocore_for_user

components = initialize_echocore_for_user("user123")
vault = components["vault"]
tracker = components["tracker"]
pipeline = components["pipeline"]

# Run full pipeline
results = await pipeline.run_full_pipeline(
    lookback_days=7,
    generate_report=True,
    trigger_fine_tuning=False
)
"""

# Legacy compatibility exports
from ai_karen_engine.echocore.echo_vault import EchoVault as LegacyEchoVault
from ai_karen_engine.echocore.dark_tracker import DarkTracker as LegacyDarkTracker
from ai_karen_engine.echocore.fine_tuner import NightlyFineTuner as LegacyFineTuner

# Enhanced component exports
from ai_karen_engine.echocore.enhanced_echo_vault import (
    EnhancedEchoVault,
    EchoVault,  # Sync wrapper
    VaultVersion,
    VaultSnapshot
)

from ai_karen_engine.echocore.enhanced_dark_tracker import (
    EnhancedDarkTracker,
    DarkTracker,  # Sync wrapper
    EventSeverity,
    PrivacyLevel
)

from ai_karen_engine.echocore.production_fine_tuner import (
    ProductionFineTuner,
    NightlyFineTuner,  # Sync wrapper
    TrainingConfig,
    TrainingMetrics,
    TrainingRun
)

from ai_karen_engine.echocore.echo_components import (
    EchoPattern,
    EchoInsight,
    EchoAnalyzer,
    EchoSynthesizer,
    EchoPipeline
)

from ai_karen_engine.echocore.factory import (
    EchoCoreConfig,
    EchoCoreFactory,
    get_echocore_factory,
    initialize_echocore_for_user
)

# Memory tier components
from ai_karen_engine.echocore.memory_tiers import (
    ShortTermMemory,
    MemoryVector,
    SearchResult,
    LongTermMemory,
    AnalyticsQuery,
    TrendAnalysis,
    PersistentMemory,
    UserData,
    InteractionRecord
)

# Memory management
from ai_karen_engine.echocore.memory_manager import (
    MemoryManager,
    MemoryTier,
    QueryType
)

# Metadata collection
from ai_karen_engine.echocore.metadata_collector import (
    MetadataCollector,
    UserMetadata,
    ConsentLevel
)

# Telemetry
from ai_karen_engine.echocore.telemetry_manager import TelemetryManager

__all__ = [
    # Legacy compatibility (simple, synchronous)
    "LegacyEchoVault",
    "LegacyDarkTracker",
    "LegacyFineTuner",
    # Enhanced async components
    "EnhancedEchoVault",
    "EnhancedDarkTracker",
    "ProductionFineTuner",
    # Sync wrappers (backward compatible)
    "EchoVault",
    "DarkTracker",
    "NightlyFineTuner",
    # Vault types
    "VaultVersion",
    "VaultSnapshot",
    # Tracker types
    "EventSeverity",
    "PrivacyLevel",
    # Fine-tuner types
    "TrainingConfig",
    "TrainingMetrics",
    "TrainingRun",
    # Analysis components
    "EchoPattern",
    "EchoInsight",
    "EchoAnalyzer",
    "EchoSynthesizer",
    "EchoPipeline",
    # Factory and initialization
    "EchoCoreConfig",
    "EchoCoreFactory",
    "get_echocore_factory",
    "initialize_echocore_for_user",
    # Memory tiers
    "ShortTermMemory",
    "MemoryVector",
    "SearchResult",
    "LongTermMemory",
    "AnalyticsQuery",
    "TrendAnalysis",
    "PersistentMemory",
    "UserData",
    "InteractionRecord",
    # Memory management
    "MemoryManager",
    "MemoryTier",
    "QueryType",
    # Metadata collection
    "MetadataCollector",
    "UserMetadata",
    "ConsentLevel",
    # Telemetry
    "TelemetryManager",
]
