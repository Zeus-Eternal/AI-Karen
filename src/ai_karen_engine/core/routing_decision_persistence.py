"""Routing Decision Persistence for LLM Router"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Routing decision data model"""

    timestamp: float
    request_id: str
    message_length: int
    preferred_provider: Optional[str]
    preferred_model: Optional[str]
    selected_provider: Optional[str]
    selected_model: Optional[str]
    reason: str
    routing_policy: str
    streaming: bool
    success: Optional[bool] = None
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class ProviderInteraction:
    """Provider interaction data model"""

    timestamp: float
    provider: str
    request_type: str
    success: bool
    latency_ms: float
    error_message: Optional[str] = None


class RoutingDecisionPersistence:
    """Handles persistence of routing decisions and provider interactions"""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        max_decisions: int = 10000,
        max_interactions: int = 50000,
        cleanup_interval: int = 3600,  # 1 hour
    ):
        """Initialize routing decision persistence"""
        self.storage_dir = Path(
            storage_dir or os.path.expanduser("~/.ai_karen/router_persistence")
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.max_decisions = max_decisions
        self.max_interactions = max_interactions
        self.cleanup_interval = cleanup_interval

        self.decisions_file = self.storage_dir / "routing_decisions.json"
        self.interactions_file = self.storage_dir / "provider_interactions.json"
        self.metadata_file = self.storage_dir / "metadata.json"

        self._decisions: List[RoutingDecision] = []
        self._interactions: List[ProviderInteraction] = []
        self._loaded = False
        self._cleanup_task: Optional[asyncio.Task] = None

        # Initialize persistence
        self._initialize_persistence()

    def _initialize_persistence(self):
        """Initialize persistence system"""
        # Load existing data
        self._load_persisted_data()

        # Start cleanup task
        self._start_cleanup_task()

        logger.info("Routing decision persistence initialized")

    def _load_persisted_data(self):
        """Load persisted data from storage"""
        try:
            # Load routing decisions
            if self.decisions_file.exists():
                with open(self.decisions_file, "r") as f:
                    decisions_data = json.load(f)
                    self._decisions = [
                        RoutingDecision(**decision) for decision in decisions_data
                    ]
                logger.info(f"Loaded {len(self._decisions)} routing decisions")

            # Load provider interactions
            if self.interactions_file.exists():
                with open(self.interactions_file, "r") as f:
                    interactions_data = json.load(f)
                    self._interactions = [
                        ProviderInteraction(**interaction)
                        for interaction in interactions_data
                    ]
                logger.info(f"Loaded {len(self._interactions)} provider interactions")

            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
                    self.max_decisions = metadata.get(
                        "max_decisions", self.max_decisions
                    )
                    self.max_interactions = metadata.get(
                        "max_interactions", self.max_interactions
                    )

            self._loaded = True

        except Exception as e:
            logger.error(f"Failed to load persisted data: {e}")
            # Start with empty data if loading fails
            self._decisions = []
            self._interactions = []
            self._loaded = False

    def _start_cleanup_task(self):
        """Start background cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Not in event loop, cleanup will happen on next access
            return

        self._cleanup_task = loop.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """Background cleanup loop"""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_data()
        except asyncio.CancelledError:
            logger.debug("Cleanup task cancelled")
            raise

    async def _cleanup_old_data(self):
        """Clean up old data based on retention policies"""
        cutoff_time = time.time() - (30 * 24 * 3600)  # Keep 30 days of data

        # Clean up old decisions
        old_count = len(self._decisions)
        self._decisions = [
            decision for decision in self._decisions if decision.timestamp > cutoff_time
        ]

        # Clean up old interactions
        old_interactions_count = len(self._interactions)
        self._interactions = [
            interaction
            for interaction in self._interactions
            if interaction.timestamp > cutoff_time
        ]

        # Enforce max limits
        if len(self._decisions) > self.max_decisions:
            self._decisions = self._decisions[-self.max_decisions :]

        if len(self._interactions) > self.max_interactions:
            self._interactions = self._interactions[-self.max_interactions :]

        # Save if we cleaned up anything
        if (
            len(self._decisions) != old_count
            or len(self._interactions) != old_interactions_count
        ):
            await self._save_persisted_data()

            logger.info(
                f"Cleaned up data: {old_count - len(self._decisions)} decisions, "
                f"{old_interactions_count - len(self._interactions)} interactions"
            )

    async def record_routing_decision(
        self,
        request_id: str,
        message_length: int,
        preferred_provider: Optional[str],
        preferred_model: Optional[str],
        selected_provider: Optional[str],
        selected_model: Optional[str],
        reason: str,
        routing_policy: str,
        streaming: bool,
        success: Optional[bool] = None,
        latency_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ):
        """Record a routing decision"""
        decision = RoutingDecision(
            timestamp=time.time(),
            request_id=request_id,
            message_length=message_length,
            preferred_provider=preferred_provider,
            preferred_model=preferred_model,
            selected_provider=selected_provider,
            selected_model=selected_model,
            reason=reason,
            routing_policy=routing_policy,
            streaming=streaming,
            success=success,
            latency_ms=latency_ms,
            error_message=error_message,
        )

        self._decisions.append(decision)

        # Enforce max limit
        if len(self._decisions) > self.max_decisions:
            self._decisions = self._decisions[-self.max_decisions :]

        # Persist immediately
        await self._save_persisted_data()

        logger.debug(f"Recorded routing decision: {selected_provider} ({reason})")

    async def record_provider_interaction(
        self,
        provider: str,
        request_type: str,
        success: bool,
        latency_ms: float,
        error_message: Optional[str] = None,
    ):
        """Record a provider interaction"""
        interaction = ProviderInteraction(
            timestamp=time.time(),
            provider=provider,
            request_type=request_type,
            success=success,
            latency_ms=latency_ms,
            error_message=error_message,
        )

        self._interactions.append(interaction)

        # Enforce max limit
        if len(self._interactions) > self.max_interactions:
            self._interactions = self._interactions[-self.max_interactions :]

        # Persist immediately
        await self._save_persisted_data()

        logger.debug(f"Recorded provider interaction: {provider} ({request_type})")

    async def _save_persisted_data(self):
        """Save data to persistent storage"""
        try:
            # Save routing decisions
            with open(self.decisions_file, "w") as f:
                json.dump(
                    [asdict(decision) for decision in self._decisions], f, indent=2
                )

            # Save provider interactions
            with open(self.interactions_file, "w") as f:
                json.dump(
                    [asdict(interaction) for interaction in self._interactions],
                    f,
                    indent=2,
                )

            # Save metadata
            metadata = {
                "max_decisions": self.max_decisions,
                "max_interactions": self.max_interactions,
                "last_updated": time.time(),
            }
            with open(self.metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save persisted data: {e}")

    def get_routing_decisions(
        self,
        limit: int = 100,
        provider_filter: Optional[str] = None,
        success_filter: Optional[bool] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Get routing decisions with filtering"""
        decisions = self._decisions

        # Apply filters
        if provider_filter:
            decisions = [d for d in decisions if d.selected_provider == provider_filter]

        if success_filter is not None:
            decisions = [d for d in decisions if d.success == success_filter]

        if start_time:
            decisions = [d for d in decisions if d.timestamp >= start_time]

        if end_time:
            decisions = [d for d in decisions if d.timestamp <= end_time]

        # Sort by timestamp (newest first)
        decisions.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        decisions = decisions[:limit]

        # Convert to dict for serialization
        return [asdict(decision) for decision in decisions]

    def get_provider_interactions(
        self,
        limit: int = 100,
        provider_filter: Optional[str] = None,
        success_filter: Optional[bool] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Get provider interactions with filtering"""
        interactions = self._interactions

        # Apply filters
        if provider_filter:
            interactions = [i for i in interactions if i.provider == provider_filter]

        if success_filter is not None:
            interactions = [i for i in interactions if i.success == success_filter]

        if start_time:
            interactions = [i for i in interactions if i.timestamp >= start_time]

        if end_time:
            interactions = [i for i in interactions if i.timestamp <= end_time]

        # Sort by timestamp (newest first)
        interactions.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        interactions = interactions[:limit]

        # Convert to dict for serialization
        return [asdict(interaction) for interaction in interactions]

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics"""
        if not self._decisions:
            return {
                "total_decisions": 0,
                "unique_providers": 0,
                "success_rate": 0.0,
                "average_latency_ms": 0.0,
                "provider_distribution": {},
            }

        total_decisions = len(self._decisions)
        successful_decisions = len([d for d in self._decisions if d.success is True])
        success_rate = (
            successful_decisions / total_decisions if total_decisions > 0 else 0.0
        )

        # Calculate average latency
        latency_decisions = [d for d in self._decisions if d.latency_ms is not None]
        average_latency = (
            sum(d.latency_ms for d in latency_decisions) / len(latency_decisions)
            if latency_decisions
            else 0.0
        )

        # Provider distribution
        provider_counts = {}
        for decision in self._decisions:
            if decision.selected_provider:
                provider_counts[decision.selected_provider] = (
                    provider_counts.get(decision.selected_provider, 0) + 1
                )

        # Reason distribution
        reason_counts = {}
        for decision in self._decisions:
            reason_counts[decision.reason] = reason_counts.get(decision.reason, 0) + 1

        return {
            "total_decisions": total_decisions,
            "successful_decisions": successful_decisions,
            "failed_decisions": total_decisions - successful_decisions,
            "success_rate": success_rate,
            "average_latency_ms": average_latency,
            "unique_providers": len(provider_counts),
            "provider_distribution": provider_counts,
            "reason_distribution": reason_counts,
            "time_range": {
                "earliest": min(d.timestamp for d in self._decisions),
                "latest": max(d.timestamp for d in self._decisions),
            },
        }

    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get provider interaction statistics"""
        if not self._interactions:
            return {
                "total_interactions": 0,
                "unique_providers": 0,
                "success_rate": 0.0,
                "average_latency_ms": 0.0,
                "provider_distribution": {},
            }

        total_interactions = len(self._interactions)
        successful_interactions = len(
            [i for i in self._interactions if i.success is True]
        )
        success_rate = (
            successful_interactions / total_interactions
            if total_interactions > 0
            else 0.0
        )

        # Calculate average latency
        average_latency = (
            sum(i.latency_ms for i in self._interactions) / total_interactions
            if total_interactions > 0
            else 0.0
        )

        # Provider distribution
        provider_counts = {}
        for interaction in self._interactions:
            provider_counts[interaction.provider] = (
                provider_counts.get(interaction.provider, 0) + 1
            )

        # Request type distribution
        request_type_counts = {}
        for interaction in self._interactions:
            request_type_counts[interaction.request_type] = (
                request_type_counts.get(interaction.request_type, 0) + 1
            )

        return {
            "total_interactions": total_interactions,
            "successful_interactions": successful_interactions,
            "failed_interactions": total_interactions - successful_interactions,
            "success_rate": success_rate,
            "average_latency_ms": average_latency,
            "unique_providers": len(provider_counts),
            "provider_distribution": provider_counts,
            "request_type_distribution": request_type_counts,
            "time_range": {
                "earliest": min(i.timestamp for i in self._interactions),
                "latest": max(i.timestamp for i in self._interactions),
            },
        }

    async def export_data(self, output_dir: str, format: str = "json") -> str:
        """Export routing data to external file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        if format == "json":
            # Export routing decisions
            decisions_file = output_path / f"routing_decisions_{timestamp}.json"
            with open(decisions_file, "w") as f:
                json.dump([asdict(d) for d in self._decisions], f, indent=2)

            # Export provider interactions
            interactions_file = output_path / f"provider_interactions_{timestamp}.json"
            with open(interactions_file, "w") as f:
                json.dump([asdict(i) for i in self._interactions], f, indent=2)

            # Export statistics
            stats_file = output_path / f"routing_statistics_{timestamp}.json"
            stats = {
                "routing_statistics": self.get_routing_statistics(),
                "provider_statistics": self.get_provider_statistics(),
                "export_timestamp": timestamp,
            }
            with open(stats_file, "w") as f:
                json.dump(stats, f, indent=2)

            logger.info(f"Data exported to {output_path}")
            return str(output_path)

        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def clear_data(self, decisions: bool = True, interactions: bool = True):
        """Clear persisted data"""
        if decisions:
            self._decisions = []
            if self.decisions_file.exists():
                self.decisions_file.unlink()

        if interactions:
            self._interactions = []
            if self.interactions_file.exists():
                self.interactions_file.unlink()

        logger.info("Cleared persisted data")

    async def shutdown(self):
        """Shutdown persistence system"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Save final data
        await self._save_persisted_data()

        logger.info("Routing decision persistence shutdown")


# Global persistence instance
_persistence_instance: Optional[RoutingDecisionPersistence] = None


def get_routing_persistence() -> RoutingDecisionPersistence:
    """Get global routing decision persistence instance"""
    global _persistence_instance
    if _persistence_instance is None:
        _persistence_instance = RoutingDecisionPersistence()
    return _persistence_instance


def initialize_routing_persistence(
    storage_dir: Optional[str] = None,
    max_decisions: int = 10000,
    max_interactions: int = 50000,
) -> RoutingDecisionPersistence:
    """Initialize routing decision persistence with custom configuration"""
    global _persistence_instance
    _persistence_instance = RoutingDecisionPersistence(
        storage_dir=storage_dir,
        max_decisions=max_decisions,
        max_interactions=max_interactions,
    )
    return _persistence_instance
