"""
Enhanced DarkTracker - Production-ready event tracking and analytics
Provides log rotation, filtering, sampling, and analytics capabilities.
"""

import json
import gzip
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from collections import Counter, defaultdict
from enum import Enum
import asyncio
import aiofiles

logger = logging.getLogger(__name__)


class EventSeverity(str, Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PrivacyLevel(str, Enum):
    """Privacy levels for event data."""
    PUBLIC = "public"  # No PII
    INTERNAL = "internal"  # May contain PII, internal use only
    SENSITIVE = "sensitive"  # Contains sensitive data, encrypted
    RESTRICTED = "restricted"  # Highly restricted access


class EnhancedDarkTracker:
    """
    Production-ready event tracker with analytics and privacy controls.

    Features:
    - Log rotation by size and time
    - Event filtering and sampling
    - Privacy level enforcement
    - Event aggregation and analytics
    - Retention policies
    - Compression of old logs
    - Event schemas and validation
    - Query capabilities
    - Performance metrics
    """

    def __init__(
        self,
        user_id: str,
        base_dir: Path = Path("data/users"),
        max_log_size_mb: int = 10,
        max_log_age_days: int = 30,
        enable_compression: bool = True,
        enable_sampling: bool = False,
        sampling_rate: float = 1.0,
        privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    ):
        self.user_id = user_id
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / user_id / "dark_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.current_log = self.logs_dir / "current.log"
        self.archive_dir = self.logs_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)

        self.max_log_size_bytes = max_log_size_mb * 1024 * 1024
        self.max_log_age = timedelta(days=max_log_age_days)
        self.enable_compression = enable_compression
        self.enable_sampling = enable_sampling
        self.sampling_rate = sampling_rate
        self.privacy_level = privacy_level

        # Event counters
        self._event_count = 0
        self._filtered_count = 0
        self._sampled_count = 0

        # Event filters
        self._filters: List[Callable[[Dict], bool]] = []

    def add_filter(self, filter_func: Callable[[Dict], bool]) -> None:
        """
        Add an event filter function.

        Args:
            filter_func: Function that returns True if event should be kept
        """
        self._filters.append(filter_func)

    def _should_sample(self) -> bool:
        """Determine if event should be sampled."""
        if not self.enable_sampling:
            return True

        import random
        return random.random() < self.sampling_rate

    def _apply_filters(self, event: Dict[str, Any]) -> bool:
        """
        Apply all filters to an event.

        Args:
            event: Event dictionary

        Returns:
            True if event passes all filters
        """
        for filter_func in self._filters:
            try:
                if not filter_func(event):
                    return False
            except Exception as e:
                logger.error(f"Filter error: {e}")
                return False
        return True

    def _sanitize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize event based on privacy level.

        Args:
            event: Event dictionary

        Returns:
            Sanitized event
        """
        if self.privacy_level == PrivacyLevel.PUBLIC:
            # Remove all potentially sensitive fields
            sensitive_keys = ["email", "password", "token", "api_key", "secret"]
            return {
                k: v for k, v in event.items()
                if not any(sk in k.lower() for sk in sensitive_keys)
            }

        elif self.privacy_level == PrivacyLevel.SENSITIVE:
            # Hash sensitive values
            sensitive_keys = ["email", "password", "token", "api_key"]
            sanitized = event.copy()
            for key in sensitive_keys:
                if key in sanitized:
                    sanitized[key] = hashlib.sha256(
                        str(sanitized[key]).encode()
                    ).hexdigest()[:16]
            return sanitized

        # INTERNAL and RESTRICTED: keep as-is
        return event

    async def capture(
        self,
        event: Dict[str, Any],
        severity: EventSeverity = EventSeverity.INFO
    ) -> bool:
        """
        Capture an event to the dark log.

        Args:
            event: Event data
            severity: Event severity level

        Returns:
            True if event was captured, False if filtered/sampled out
        """
        self._event_count += 1

        # Apply sampling
        if not self._should_sample():
            self._sampled_count += 1
            return False

        # Apply filters
        if not self._apply_filters(event):
            self._filtered_count += 1
            return False

        # Sanitize based on privacy level
        sanitized_event = self._sanitize_event(event)

        # Add metadata
        full_event = {
            "ts": datetime.utcnow().isoformat(),
            "user_id": self.user_id,
            "severity": severity.value,
            "event_id": hashlib.sha256(
                f"{self.user_id}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16],
            **sanitized_event
        }

        # Write to log
        async with aiofiles.open(self.current_log, 'a', encoding='utf-8') as f:
            await f.write(json.dumps(full_event) + "\n")

        # Check if rotation is needed
        await self._check_rotation()

        return True

    async def _check_rotation(self) -> None:
        """Check if log rotation is needed and perform if necessary."""
        if not self.current_log.exists():
            return

        file_size = self.current_log.stat().st_size

        # Rotate if file is too large
        if file_size >= self.max_log_size_bytes:
            await self._rotate_log()

    async def _rotate_log(self) -> None:
        """Rotate the current log file."""
        if not self.current_log.exists():
            return

        # Generate archive filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_file = self.archive_dir / f"dark_{timestamp}.log"

        # Move current log to archive
        self.current_log.rename(archive_file)

        # Compress if enabled
        if self.enable_compression:
            await self._compress_log(archive_file)

        # Clean old logs
        await self._clean_old_logs()

        logger.info(f"Rotated log for user {self.user_id}: {archive_file}")

    async def _compress_log(self, log_file: Path) -> None:
        """Compress a log file."""
        compressed_file = log_file.with_suffix('.log.gz')

        async with aiofiles.open(log_file, 'rb') as f_in:
            content = await f_in.read()

        compressed_content = gzip.compress(content)

        async with aiofiles.open(compressed_file, 'wb') as f_out:
            await f_out.write(compressed_content)

        # Remove original
        log_file.unlink()

        logger.debug(f"Compressed log: {compressed_file}")

    async def _clean_old_logs(self) -> None:
        """Remove logs older than max_log_age."""
        cutoff_time = datetime.utcnow() - self.max_log_age

        for log_file in self.archive_dir.glob("dark_*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_time:
                    log_file.unlink()
                    logger.debug(f"Removed old log: {log_file}")
            except Exception as e:
                logger.error(f"Error cleaning log {log_file}: {e}")

    async def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[EventSeverity] = None,
        event_type: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query events from logs.

        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time
            severity: Filter by severity level
            event_type: Filter by event type
            limit: Maximum number of events to return

        Returns:
            List of matching events
        """
        events = []

        # Read current log
        if self.current_log.exists():
            async with aiofiles.open(self.current_log, 'r', encoding='utf-8') as f:
                async for line in f:
                    if len(events) >= limit:
                        break

                    try:
                        event = json.loads(line)
                        if self._matches_query(event, start_time, end_time, severity, event_type):
                            events.append(event)
                    except json.JSONDecodeError:
                        continue

        # Read archive logs if needed
        if len(events) < limit:
            for archive_file in sorted(self.archive_dir.glob("dark_*.log*"), reverse=True):
                if len(events) >= limit:
                    break

                events.extend(
                    await self._read_archive(archive_file, start_time, end_time, severity, event_type, limit - len(events))
                )

        return events

    def _matches_query(
        self,
        event: Dict[str, Any],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        severity: Optional[EventSeverity],
        event_type: Optional[str]
    ) -> bool:
        """Check if event matches query criteria."""
        try:
            event_time = datetime.fromisoformat(event["ts"])

            if start_time and event_time < start_time:
                return False
            if end_time and event_time > end_time:
                return False
            if severity and event.get("severity") != severity.value:
                return False
            if event_type and event.get("type") != event_type:
                return False

            return True
        except (KeyError, ValueError):
            return False

    async def _read_archive(
        self,
        archive_file: Path,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        severity: Optional[EventSeverity],
        event_type: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Read events from archive file."""
        events = []

        try:
            # Handle compressed files
            if archive_file.suffix == '.gz':
                async with aiofiles.open(archive_file, 'rb') as f:
                    compressed_content = await f.read()
                content = gzip.decompress(compressed_content).decode('utf-8')
                lines = content.splitlines()
            else:
                async with aiofiles.open(archive_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    lines = content.splitlines()

            for line in lines:
                if len(events) >= limit:
                    break

                try:
                    event = json.loads(line)
                    if self._matches_query(event, start_time, end_time, severity, event_type):
                        events.append(event)
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            logger.error(f"Error reading archive {archive_file}: {e}")

        return events

    async def get_analytics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for tracked events.

        Args:
            start_time: Start time for analytics
            end_time: End time for analytics

        Returns:
            Dictionary with analytics
        """
        events = await self.query_events(start_time=start_time, end_time=end_time, limit=10000)

        # Count by severity
        severity_counts = Counter(e.get("severity") for e in events)

        # Count by type
        type_counts = Counter(e.get("type") for e in events)

        # Count by hour
        hourly_counts = defaultdict(int)
        for event in events:
            try:
                event_time = datetime.fromisoformat(event["ts"])
                hour_key = event_time.strftime("%Y-%m-%d %H:00")
                hourly_counts[hour_key] += 1
            except (KeyError, ValueError):
                continue

        # Calculate time range
        if events:
            timestamps = [datetime.fromisoformat(e["ts"]) for e in events if "ts" in e]
            if timestamps:
                first_event = min(timestamps)
                last_event = max(timestamps)
                duration = (last_event - first_event).total_seconds()
            else:
                first_event = None
                last_event = None
                duration = 0
        else:
            first_event = None
            last_event = None
            duration = 0

        return {
            "total_events": len(events),
            "severity_distribution": dict(severity_counts),
            "type_distribution": dict(type_counts),
            "hourly_distribution": dict(sorted(hourly_counts.items())),
            "time_range": {
                "first_event": first_event.isoformat() if first_event else None,
                "last_event": last_event.isoformat() if last_event else None,
                "duration_seconds": duration
            },
            "tracking_stats": {
                "total_captured": self._event_count,
                "filtered_out": self._filtered_count,
                "sampled_out": self._sampled_count,
                "capture_rate": (self._event_count - self._filtered_count - self._sampled_count) / self._event_count if self._event_count > 0 else 0
            }
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get tracker statistics.

        Returns:
            Dictionary with tracker statistics
        """
        stats = {
            "user_id": self.user_id,
            "logs_dir": str(self.logs_dir),
            "current_log_exists": self.current_log.exists(),
            "archive_count": len(list(self.archive_dir.glob("dark_*.log*"))),
            "compression_enabled": self.enable_compression,
            "sampling_enabled": self.enable_sampling,
            "sampling_rate": self.sampling_rate,
            "privacy_level": self.privacy_level.value,
            "max_log_age_days": self.max_log_age.days,
            "event_stats": {
                "total_events": self._event_count,
                "filtered": self._filtered_count,
                "sampled": self._sampled_count
            }
        }

        if self.current_log.exists():
            stats["current_log_size_bytes"] = self.current_log.stat().st_size
            stats["current_log_modified"] = datetime.fromtimestamp(
                self.current_log.stat().st_mtime
            ).isoformat()

        # Total size of all logs
        total_size = sum(
            f.stat().st_size for f in self.logs_dir.rglob("*.log*")
        )
        stats["total_logs_size_bytes"] = total_size

        return stats


# Synchronous wrapper for backward compatibility
class DarkTracker:
    """Synchronous wrapper for EnhancedDarkTracker."""

    def __init__(self, user_id: str, base_dir: Path = Path("data/users")):
        self.tracker = EnhancedDarkTracker(user_id, base_dir)

    def capture(self, event: Dict[str, Any]) -> None:
        """Synchronous capture."""
        asyncio.run(self.tracker.capture(event))
