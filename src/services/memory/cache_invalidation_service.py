"""
Cache Invalidation Service

Provides intelligent cache invalidation strategies for dynamic content
and coordinated cache management across different cache types.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from production_cache_service import get_cache_service
from model_library_cache_service import get_model_cache_service
from database_query_cache_service import get_db_cache_service

logger = logging.getLogger(__name__)


class InvalidationTrigger(Enum):
    """Types of events that can trigger cache invalidation."""
    MODEL_STATUS_CHANGE = "model_status_change"
    USER_DATA_UPDATE = "user_data_update"
    PROVIDER_CONFIG_CHANGE = "provider_config_change"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    DATABASE_WRITE = "database_write"
    MANUAL_INVALIDATION = "manual_invalidation"
    SCHEDULED_CLEANUP = "scheduled_cleanup"


@dataclass
class InvalidationRule:
    """Defines a cache invalidation rule."""
    trigger: InvalidationTrigger
    target_namespaces: List[str]
    target_tags: List[str]
    condition_func: Optional[Callable] = None
    delay_seconds: int = 0
    description: str = ""


@dataclass
class InvalidationEvent:
    """Represents a cache invalidation event."""
    trigger: InvalidationTrigger
    timestamp: datetime
    metadata: Dict[str, Any]
    affected_keys: List[str] = None  # type: ignore
    
    def __post_init__(self):
        if self.affected_keys is None:
            self.affected_keys = []


class CacheInvalidationService:
    """
    Service for managing intelligent cache invalidation strategies.
    
    Features:
    - Event-driven cache invalidation
    - Coordinated invalidation across cache types
    - Delayed invalidation for batch operations
    - Conditional invalidation rules
    - Invalidation event tracking and analytics
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.model_cache_service = get_model_cache_service()
        self.db_cache_service = get_db_cache_service()
        
        # Track invalidation events
        self.invalidation_history: List[InvalidationEvent] = []
        self.max_history_size = 1000
        
        # Pending delayed invalidations
        self.pending_invalidations: Dict[str, InvalidationEvent] = {}
        
        # Define invalidation rules
        self.invalidation_rules = self._setup_invalidation_rules()
        
        logger.info("Cache invalidation service initialized")
    
    def _setup_invalidation_rules(self) -> List[InvalidationRule]:
        """Setup default invalidation rules."""
        return [
            # Model status changes should invalidate model library cache
            InvalidationRule(
                trigger=InvalidationTrigger.MODEL_STATUS_CHANGE,
                target_namespaces=['model_library'],
                target_tags=['model_library'],
                description="Invalidate model library cache when model status changes"
            ),
            
            # User data updates should invalidate user-specific caches
            InvalidationRule(
                trigger=InvalidationTrigger.USER_DATA_UPDATE,
                target_namespaces=['response_formatting'],
                target_tags=['user_sessions'],
                description="Invalidate user-specific caches when user data changes"
            ),
            
            # Provider config changes should invalidate related caches
            InvalidationRule(
                trigger=InvalidationTrigger.PROVIDER_CONFIG_CHANGE,
                target_namespaces=['model_library', 'database_queries'],
                target_tags=['provider_config'],
                description="Invalidate provider-related caches when config changes"
            ),
            
            # System config changes should invalidate system-wide caches
            InvalidationRule(
                trigger=InvalidationTrigger.SYSTEM_CONFIG_CHANGE,
                target_namespaces=['model_library', 'database_queries', 'response_formatting'],
                target_tags=['system_config'],
                description="Invalidate system caches when system config changes"
            ),
            
            # Database writes should invalidate related query caches
            InvalidationRule(
                trigger=InvalidationTrigger.DATABASE_WRITE,
                target_namespaces=['database_queries'],
                target_tags=[],  # Will be determined dynamically based on affected tables
                delay_seconds=5,  # Small delay to batch multiple writes
                description="Invalidate query caches when database is modified"
            ),
        ]
    
    async def trigger_invalidation(
        self,
        trigger: InvalidationTrigger,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Trigger cache invalidation based on an event.
        
        Args:
            trigger: The type of event that triggered invalidation
            metadata: Additional metadata about the event
            
        Returns:
            Number of cache entries invalidated
        """
        metadata = metadata or {}
        event = InvalidationEvent(
            trigger=trigger,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        total_invalidated = 0
        
        # Find matching rules
        matching_rules = [rule for rule in self.invalidation_rules if rule.trigger == trigger]
        
        for rule in matching_rules:
            try:
                # Check condition if specified
                if rule.condition_func and not rule.condition_func(metadata):
                    continue
                
                if rule.delay_seconds > 0:
                    # Schedule delayed invalidation
                    await self._schedule_delayed_invalidation(rule, event)
                else:
                    # Immediate invalidation
                    invalidated = await self._execute_invalidation_rule(rule, event)
                    total_invalidated += invalidated
                    
            except Exception as e:
                logger.error(f"Error executing invalidation rule {rule.description}: {e}")
        
        # Record the event
        self._record_invalidation_event(event)
        
        logger.info(f"Triggered invalidation for {trigger.value}: {total_invalidated} entries invalidated")
        return total_invalidated
    
    async def _execute_invalidation_rule(
        self,
        rule: InvalidationRule,
        event: InvalidationEvent
    ) -> int:
        """Execute a specific invalidation rule."""
        total_invalidated = 0
        
        # Invalidate by namespaces
        for namespace in rule.target_namespaces:
            try:
                if namespace == 'model_library':
                    invalidated = await self.model_cache_service.invalidate_all_model_cache()
                elif namespace == 'database_queries':
                    invalidated = await self.db_cache_service.invalidate_all_query_cache()
                else:
                    invalidated = await self.cache_service.clear_namespace(namespace)
                
                total_invalidated += invalidated
                event.affected_keys.extend([f"namespace:{namespace}"])
                
            except Exception as e:
                logger.error(f"Error invalidating namespace {namespace}: {e}")
        
        # Invalidate by tags
        if rule.target_tags:
            try:
                # Handle dynamic tags based on event metadata
                tags_to_invalidate = self._resolve_dynamic_tags(rule.target_tags, event.metadata)
                
                if tags_to_invalidate:
                    invalidated = await self.cache_service.invalidate_by_tags(tags_to_invalidate)
                    total_invalidated += invalidated
                    event.affected_keys.extend([f"tag:{tag}" for tag in tags_to_invalidate])
                
            except Exception as e:
                logger.error(f"Error invalidating tags {rule.target_tags}: {e}")
        
        return total_invalidated
    
    def _resolve_dynamic_tags(self, tag_templates: List[str], metadata: Dict[str, Any]) -> List[str]:
        """Resolve dynamic tags based on event metadata."""
        resolved_tags = []
        
        for tag_template in tag_templates:
            if ':' in tag_template and '{' in tag_template:
                # Dynamic tag template (e.g., "user:{user_id}")
                try:
                    resolved_tag = tag_template.format(**metadata)
                    resolved_tags.append(resolved_tag)
                except KeyError:
                    # Missing metadata for template, skip
                    continue
            else:
                # Static tag
                resolved_tags.append(tag_template)
        
        # Add special handling for database write events
        if 'affected_tables' in metadata:
            for table in metadata['affected_tables']:
                resolved_tags.append(f"table:{table}")
        
        return resolved_tags
    
    async def _schedule_delayed_invalidation(
        self,
        rule: InvalidationRule,
        event: InvalidationEvent
    ) -> None:
        """Schedule a delayed invalidation."""
        delay_key = f"{rule.trigger.value}_{rule.delay_seconds}"
        
        # Store or update pending invalidation
        self.pending_invalidations[delay_key] = event
        
        # Schedule execution
        asyncio.create_task(self._execute_delayed_invalidation(rule, event, delay_key))
    
    async def _execute_delayed_invalidation(
        self,
        rule: InvalidationRule,
        event: InvalidationEvent,
        delay_key: str
    ) -> None:
        """Execute a delayed invalidation after the specified delay."""
        await asyncio.sleep(rule.delay_seconds)
        
        # Check if this invalidation is still pending
        if delay_key in self.pending_invalidations:
            try:
                invalidated = await self._execute_invalidation_rule(rule, event)
                logger.info(f"Executed delayed invalidation: {invalidated} entries invalidated")
            except Exception as e:
                logger.error(f"Error in delayed invalidation: {e}")
            finally:
                # Remove from pending
                self.pending_invalidations.pop(delay_key, None)
    
    def _record_invalidation_event(self, event: InvalidationEvent) -> None:
        """Record an invalidation event for analytics."""
        self.invalidation_history.append(event)
        
        # Trim history if it gets too large
        if len(self.invalidation_history) > self.max_history_size:
            self.invalidation_history = self.invalidation_history[-self.max_history_size:]
    
    async def invalidate_model_status_change(
        self,
        model_id: str,
        old_status: str,
        new_status: str,
        provider: Optional[str] = None
    ) -> int:
        """Invalidate caches when a model's status changes."""
        metadata = {
            'model_id': model_id,
            'old_status': old_status,
            'new_status': new_status,
            'provider': provider
        }
        
        # Trigger general model status change invalidation
        total_invalidated = await self.trigger_invalidation(
            InvalidationTrigger.MODEL_STATUS_CHANGE,
            metadata
        )
        
        # Also invalidate specific model and status caches
        try:
            model_invalidated = await self.model_cache_service.invalidate_model(model_id)
            status_invalidated = await self.model_cache_service.invalidate_status(new_status)
            total_invalidated += model_invalidated + status_invalidated
            
            if provider:
                provider_invalidated = await self.model_cache_service.invalidate_provider(provider)
                total_invalidated += provider_invalidated
                
        except Exception as e:
            logger.error(f"Error in model-specific cache invalidation: {e}")
        
        return total_invalidated
    
    async def invalidate_user_data_change(
        self,
        user_id: str,
        data_type: str = "general"
    ) -> int:
        """Invalidate caches when user data changes."""
        metadata = {
            'user_id': user_id,
            'data_type': data_type
        }
        
        # Trigger user data update invalidation
        total_invalidated = await self.trigger_invalidation(
            InvalidationTrigger.USER_DATA_UPDATE,
            metadata
        )
        
        # Also invalidate user-specific response formatting cache
        try:
            from extensions.response_formatting.cache_integration import get_cached_formatter_registry
            cached_registry = get_cached_formatter_registry()
            user_invalidated = await cached_registry.invalidate_user_cache(user_id)
            total_invalidated += user_invalidated
        except Exception as e:
            logger.error(f"Error invalidating user response formatting cache: {e}")
        
        return total_invalidated
    
    async def invalidate_database_write(
        self,
        affected_tables: List[str],
        operation: str = "unknown"
    ) -> int:
        """Invalidate caches when database is modified."""
        metadata = {
            'affected_tables': affected_tables,
            'operation': operation
        }
        
        # Trigger database write invalidation
        total_invalidated = await self.trigger_invalidation(
            InvalidationTrigger.DATABASE_WRITE,
            metadata
        )
        
        # Also invalidate table-specific query caches
        try:
            for table in affected_tables:
                table_invalidated = await self.db_cache_service.invalidate_table_cache(table)
                total_invalidated += table_invalidated
        except Exception as e:
            logger.error(f"Error invalidating table-specific caches: {e}")
        
        return total_invalidated
    
    async def invalidate_provider_config_change(
        self,
        provider: str,
        config_type: str = "general"
    ) -> int:
        """Invalidate caches when provider configuration changes."""
        metadata = {
            'provider': provider,
            'config_type': config_type
        }
        
        # Trigger provider config change invalidation
        total_invalidated = await self.trigger_invalidation(
            InvalidationTrigger.PROVIDER_CONFIG_CHANGE,
            metadata
        )
        
        # Also invalidate provider-specific model cache
        try:
            provider_invalidated = await self.model_cache_service.invalidate_provider(provider)
            total_invalidated += provider_invalidated
        except Exception as e:
            logger.error(f"Error invalidating provider-specific cache: {e}")
        
        return total_invalidated
    
    async def manual_cache_clear(
        self,
        namespaces: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Manually clear cache entries."""
        metadata = {
            'namespaces': namespaces or [],
            'tags': tags or []
        }
        
        total_invalidated = 0
        
        # Clear specified namespaces
        if namespaces:
            for namespace in namespaces:
                try:
                    if namespace == 'model_library':
                        invalidated = await self.model_cache_service.invalidate_all_model_cache()
                    elif namespace == 'database_queries':
                        invalidated = await self.db_cache_service.invalidate_all_query_cache()
                    else:
                        invalidated = await self.cache_service.clear_namespace(namespace)
                    
                    total_invalidated += invalidated
                except Exception as e:
                    logger.error(f"Error clearing namespace {namespace}: {e}")
        
        # Clear specified tags
        if tags:
            try:
                invalidated = await self.cache_service.invalidate_by_tags(tags)
                total_invalidated += invalidated
            except Exception as e:
                logger.error(f"Error clearing tags {tags}: {e}")
        
        # Record manual invalidation event
        await self.trigger_invalidation(
            InvalidationTrigger.MANUAL_INVALIDATION,
            metadata
        )
        
        return total_invalidated
    
    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get cache invalidation statistics."""
        # Count events by trigger type
        trigger_counts = {}
        for event in self.invalidation_history:
            trigger = event.trigger.value
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        # Recent events (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_events = [
            event for event in self.invalidation_history
            if event.timestamp > recent_cutoff
        ]
        
        return {
            'total_events': len(self.invalidation_history),
            'recent_events_24h': len(recent_events),
            'trigger_counts': trigger_counts,
            'pending_delayed_invalidations': len(self.pending_invalidations),
            'invalidation_rules': len(self.invalidation_rules),
            'last_event': self.invalidation_history[-1].timestamp.isoformat() if self.invalidation_history else None
        }
    
    def add_invalidation_rule(self, rule: InvalidationRule) -> None:
        """Add a custom invalidation rule."""
        self.invalidation_rules.append(rule)
        logger.info(f"Added invalidation rule: {rule.description}")
    
    def remove_invalidation_rule(self, description: str) -> bool:
        """Remove an invalidation rule by description."""
        original_count = len(self.invalidation_rules)
        self.invalidation_rules = [
            rule for rule in self.invalidation_rules
            if rule.description != description
        ]
        
        removed = original_count - len(self.invalidation_rules)
        if removed > 0:
            logger.info(f"Removed {removed} invalidation rule(s): {description}")
        
        return removed > 0


# Global cache invalidation service instance
_invalidation_service: Optional[CacheInvalidationService] = None


def get_invalidation_service() -> CacheInvalidationService:
    """Get the global cache invalidation service instance."""
    global _invalidation_service
    
    if _invalidation_service is None:
        _invalidation_service = CacheInvalidationService()
    
    return _invalidation_service


def reset_invalidation_service() -> None:
    """Reset the global cache invalidation service (for testing)."""
    global _invalidation_service
    _invalidation_service = None